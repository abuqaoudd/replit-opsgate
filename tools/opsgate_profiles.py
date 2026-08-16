"""Profile resolution and protected-path matching.

Split out of opsgate.py (the "structural refactor" pass, keeping every function body
unchanged - this is a relocation, not a rewrite) because it's a genuinely separate concern from
routing, prompt compilation, or command dispatch: everything here answers "which profile
governs this run, and does this path violate it."

read_json() lives here rather than in a separate generic-I/O module because its two special
cases (manifests/profiles.json, manifests/protected-paths.json) exist ONLY to merge in an
external opsgate.profile.json - splitting that special-casing away from the profile-merge logic
it exists to serve would just move the coupling somewhere less obvious. Every other caller in
this engine that needs a plain contract or a real file uses this same read_json.
"""
import copy
import json
import os
import re
import sys
from pathlib import Path

import opsgate_contracts

ROOT_DIR = Path(__file__).resolve().parent.parent

EXTERNAL_PROFILE_CONFIG_FILENAME = "opsgate.profile.json"
_EXTERNAL_PROFILE_CACHE = None
_EXTERNAL_PROFILE_CACHE_KEY = None


def external_profile_config_path():
    """Resolve the consuming project's own profile-override file, so a project that drops
    this engine in as a submodule never has to commit its own profile/business-file data into
    the engine's shared repo (see canonical/ENGINE_ADOPTION_GUIDE.md "Adopting this engine" for why this
    matters - a profile baked into opsgate_contracts.py ships inside this engine's own git
    history to every project that reuses it, which is fine for nothing project-specific but
    wrong for one project's actual business facts).

    Resolution order: OPSGATE_PROFILE_CONFIG env var (explicit, works no matter how deeply
    nested the submodule is) - else walk up from the current working directory looking for a
    file named exactly "opsgate.profile.json", stopping at the first directory that also
    contains .git (that is almost always the outer project's real root) or after 12 levels,
    whichever comes first, so a missing/unusual layout fails to find anything rather than
    walking to the filesystem root. Returns None if neither resolves - callers treat that as
    "no external profiles", not an error."""
    env_path = os.environ.get("OPSGATE_PROFILE_CONFIG")
    if env_path:
        return Path(env_path)
    # The walk starts at this engine's own directory when it is used as a submodule, and
    # that directory almost always has its own .git (a real submodule gitlink file, or a
    # vendored nested repo) - so the .git-based stop below is deliberately skipped for the
    # starting directory itself (`current != start`), otherwise the walk would stop before
    # ever climbing out of the submodule into the outer project that actually has the file.
    start = Path.cwd()
    current = start
    for _ in range(12):
        candidate = current / EXTERNAL_PROFILE_CONFIG_FILENAME
        if candidate.exists():
            return candidate
        if current != start and (current / ".git").exists():
            break
        if current.parent == current:
            break
        current = current.parent
    return None


def load_external_profile_config():
    """Load the external profile-override file, if one is found, and derive both an
    (external) manifests/profiles.json-shaped dict and an (external) manifests/protected-
    paths.json-shaped dict from it in one pass. A missing or malformed file is never fatal -
    it just means no external profiles are added on top of the built-in ones.

    Cached keyed by (resolved path, mtime), not for the life of the process unconditionally -
    a bare process-lifetime cache was correct for the one-shot CLI but became a real staleness
    bug once the long-running MCP server started calling this in-process: editing a project's
    opsgate.profile.json (e.g. via apply-setup.py) while the server was running was silently
    ignored until restart. Re-checking mtime on every call costs a handful of stat() calls,
    negligible next to a network round trip, and keeps the fix simple rather than adding a
    manual invalidation hook."""
    global _EXTERNAL_PROFILE_CACHE, _EXTERNAL_PROFILE_CACHE_KEY
    path = external_profile_config_path()
    cache_key = (str(path), path.stat().st_mtime) if path and path.exists() else None
    if _EXTERNAL_PROFILE_CACHE is not None and cache_key == _EXTERNAL_PROFILE_CACHE_KEY:
        return _EXTERNAL_PROFILE_CACHE
    if not path:
        _EXTERNAL_PROFILE_CACHE = ({}, {})
        _EXTERNAL_PROFILE_CACHE_KEY = cache_key
        return _EXTERNAL_PROFILE_CACHE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"warning: ignoring external profile config at {path} ({exc})", file=sys.stderr)
        _EXTERNAL_PROFILE_CACHE = ({}, {})
        _EXTERNAL_PROFILE_CACHE_KEY = cache_key
        return _EXTERNAL_PROFILE_CACHE

    external_profiles = {}
    external_protected = {}
    for key, entry in (raw.get("profiles") or {}).items():
        external_profiles[key] = {
            "description": entry.get("description", f"{key} profile (defined in {path})."),
            "business_file": entry.get("business_file", f"ai/{key}.md"),
            "frontend_root": entry.get("frontend_root"),
            "backend_root": entry.get("backend_root"),
        }
        write_paths = [p for p in (entry.get("frontend_root"), entry.get("backend_root")) if p]
        external_protected[key] = {
            "normal_write_paths": [f"{p.rstrip('/')}/**" for p in write_paths],
            "never_access": [*opsgate_contracts._UNIVERSAL_NEVER_ACCESS, *(entry.get("extra_never_access") or [])],
            "locked_by_default": list(opsgate_contracts._UNIVERSAL_LOCKED_BY_DEFAULT),
        }
    _EXTERNAL_PROFILE_CACHE = (external_profiles, external_protected)
    _EXTERNAL_PROFILE_CACHE_KEY = cache_key
    return _EXTERNAL_PROFILE_CACHE


def read_json(relative_path):
    if relative_path == "manifests/profiles.json":
        base = copy.deepcopy(opsgate_contracts.CONTRACTS[relative_path])
        external_profiles, _ = load_external_profile_config()
        base["profiles"] = {**base.get("profiles", {}), **external_profiles}
        return base
    if relative_path == "manifests/protected-paths.json":
        base = copy.deepcopy(opsgate_contracts.CONTRACTS[relative_path])
        _, external_protected = load_external_profile_config()
        base["profiles"] = {**base.get("profiles", {}), **external_protected}
        return base
    if relative_path in opsgate_contracts.CONTRACTS:
        return copy.deepcopy(opsgate_contracts.CONTRACTS[relative_path])
    with (ROOT_DIR / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def active_profile(request=None):
    """Resolve which manifests/profiles.json entry governs this run, so the engine behaves
    correctly both in the project it was built for and in any new Replit project a submodule
    of it gets dropped into. Order: OPSGATE_PROFILE env var (set this when running against a
    different project) > legacy METCO_PROFILE env var (kept only so a deployment configured
    before the 6.0.13-generalization rename keeps working without touching its Repl Secret) >
    an explicit "profile" field on the request itself > the manifest's own default_profile.
    Falls back to "generic-replit" - never raises - if none of those resolve to a profile that
    actually exists, so a new project gets sane generic protections instead of a crash or a
    silent inheritance of another project's paths."""
    profiles = read_json("manifests/profiles.json")
    known = profiles.get("profiles", {})
    for candidate in [
        os.environ.get("OPSGATE_PROFILE"),
        os.environ.get("METCO_PROFILE"),  # legacy env var name, see docstring
        (request or {}).get("profile"),
        profiles.get("default_profile"),
    ]:
        if candidate and candidate in known:
            return candidate
    return "generic-replit" if "generic-replit" in known else profiles.get("default_profile")


def protected_paths_for(request=None):
    profile = active_profile(request)
    profiles_data = read_json("manifests/protected-paths.json")["profiles"]
    return profiles_data.get(profile) or profiles_data.get("generic-replit") or next(iter(profiles_data.values()), {})


def normalize_pattern(pattern):
    return re.sub(r"\*\*/?", "", str(pattern)).replace("*", "")


def matches_protected(candidate, protected_pattern):
    needle = normalize_pattern(protected_pattern).rstrip("/")
    return candidate == needle or candidate.startswith(f"{needle}/") or f"/{needle}/" in candidate or needle in candidate
