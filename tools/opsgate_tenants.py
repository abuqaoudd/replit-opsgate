"""Multi-tenant profile store and tenant resolution.

This is the single profile-resolution mechanism in the engine: every caller - the CLI, the MCP
server - resolves against this store, identified by tenant ID. There is no per-project
hardcoded profile and no external config file to walk for; a caller with no specific tenant
identity (local CLI use with no --tenant, or the MCP server's shared-secret auth path with no
tenant token) resolves to LOCAL_DEV_TENANT_ID, a small built-in default (see get_profile()) -
not a fallback profile system of its own, just one named, always-available tenant.

Storage is a simple, swappable file-backed JSON registry - the interface (get_profile/
create_profile/update_profile/list_profiles/token issuance/resolution) is what matters; the
backend can become a real database later with no caller-visible change.

Reuses opsgate_tenant_entry.build_entry() directly (pure - no file I/O, no target-root coupling).
create_profile() below validates its own tenant-key pattern inline and raises TenantError on a
bad key, rather than the sys.exit(1)-on-failure style that suits a CLI script but not library
code a caller needs to catch and recover from.

Tenant resolution is token-first: a caller's auth token maps, server-side, to exactly one tenant
ID. Tokens are never stored in plaintext - only their SHA-256 hash - so a leaked registry file
does not itself leak usable credentials. An explicit tenant override exists only for admin
tokens, and is itself checked against the tenant registry (never trusted blindly), so a non-admin
token can never address another tenant's profile by passing a different ID.
"""
import contextlib
import copy
import fcntl
import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path

from opsgate_tenant_entry import build_entry
import opsgate_contracts

ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "tenants" / "registry.json"

PROFILE_KEY_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

LOCAL_DEV_TENANT_ID = "local-dev"
# Deliberately code, not a registry.json entry: tenants/registry.json is gitignored (real
# tenant data doesn't belong in git), so anything only stored there would not exist on a fresh
# checkout - and the CLI/shared-secret path need a safe default with zero setup. frontend_root/
# backend_root are left unset rather than guessed, since assuming a wrong project root silently
# is worse than admitting it isn't configured. A deployment that wants this identity to have
# real roots can still call create_profile(LOCAL_DEV_TENANT_ID, ...) - a real registry entry
# always takes precedence over this built-in one, see get_profile() below.
_BUILTIN_TENANTS = {
    LOCAL_DEV_TENANT_ID: {
        "description": "Default identity when no specific tenant is named - local CLI use with no --tenant, or the MCP server's shared-secret auth path with no tenant token.",
        "business_file": None,
        "frontend_root": None,
        "backend_root": None,
    }
}


class TenantError(Exception):
    """Raised for a caller-facing tenant-store error (unknown tenant, duplicate key, etc.)."""


def _load_registry():
    if not REGISTRY_PATH.exists():
        return {"tenants": {}}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # Every tenant-resolving MCP tool surfaces an unhandled TenantError straight back to the
        # caller as its error response - name the registry file, not this server's absolute
        # filesystem path to it, which no caller has any legitimate use for.
        raise TenantError(f"tenant registry ({REGISTRY_PATH.name}) is not valid JSON ({exc})") from exc
    data.setdefault("tenants", {})
    return data


def _save_registry(data):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Holds every tenant's absolute frontend/backend roots and every issued token's hash - keep
    # both the file and its directory private to this user account. Set on every save (not just
    # once by hand) so a fresh checkout or a deleted-and-recreated registry can't silently regress
    # to the process umask's default (typically world/group-readable).
    REGISTRY_PATH.parent.chmod(0o700)
    REGISTRY_PATH.chmod(0o600)


@contextlib.contextmanager
def _locked_registry():
    """Exclusive-locks tenants/registry.json.lock for one read-modify-write cycle, then loads
    and yields the registry - every mutating function below (create/update/delete_profile,
    issue/revoke_token) used to load, mutate, and save with no lock at all, so two
    near-simultaneous writers (e.g. two issue_token() calls for different tenants landing close
    together) could race and one write silently vanish (a lost update) on this plain JSON file.
    Read-only callers (get_profile/list_profiles/resolve_tenant_from_token) still call
    _load_registry() directly and never wait on this - only writers serialize against each
    other. This only adds mutual exclusion around the existing load/mutate/save pattern; each
    caller below still calls _save_registry(registry) itself, exactly where it did before, so
    whether/when a save actually happens is unchanged (e.g. revoke_token() still only saves if
    it actually found the token).

    The lock path is derived from the current value of REGISTRY_PATH on every call, not
    captured once at import time - tests reassign the module-level REGISTRY_PATH to redirect
    the whole store into a temp directory, and the lock must follow that redirect too, or a
    test run would take out a real lock against this repo's own tenants/ directory instead of
    its isolated temp copy."""
    registry_lock_path = REGISTRY_PATH.parent / f"{REGISTRY_PATH.name}.lock"
    registry_lock_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_lock_path.open("w") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        try:
            yield _load_registry()
        finally:
            fcntl.flock(lock_handle, fcntl.LOCK_UN)


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_profile(tenant_id, frontend_root=None, backend_root=None, description=None, extra_never_access=None, business_file=None):
    """Register a new tenant. Refuses to overwrite an existing tenant_id - update_profile() is
    the explicit path for changing an existing tenant's config."""
    if not PROFILE_KEY_RE.match(tenant_id):
        raise TenantError(f"tenant id {tenant_id!r} must be lowercase letters/digits, hyphen-separated (e.g. acme, my-project)")
    with _locked_registry() as registry:
        if tenant_id in registry["tenants"]:
            raise TenantError(f"tenant {tenant_id!r} already exists - use update_profile() to change it")
        entry = build_entry(
            tenant_id,
            frontend_root=frontend_root,
            backend_root=backend_root,
            description=description,
            extra_never_access=extra_never_access,
            business_file=business_file,
        )
        entry["token_hashes"] = []
        registry["tenants"][tenant_id] = entry
        _save_registry(registry)
    return _public_profile(entry)


def update_profile(tenant_id, **fields):
    """Merge `fields` into an existing tenant's profile. Never touches token_hashes - use
    issue_token()/revoke_token() for that, so credential state and profile state can't be
    silently overwritten by the same call."""
    with _locked_registry() as registry:
        entry = registry["tenants"].get(tenant_id)
        if entry is None:
            raise TenantError(f"unknown tenant {tenant_id!r}")
        for key, value in fields.items():
            if key == "token_hashes":
                raise TenantError("update_profile() cannot modify token_hashes - use issue_token()/revoke_token()")
            entry[key] = value
        _save_registry(registry)
    return _public_profile(entry)


def get_profile(tenant_id):
    """Returns the tenant's public profile, or None if the tenant does not exist - callers
    must treat None as fail-closed (no fallback to a default profile), not an error to retry.

    The one deliberate exception: LOCAL_DEV_TENANT_ID always resolves, even with an empty
    registry - a real registry entry for it (if a deployment has created one) takes precedence
    over the built-in default in _BUILTIN_TENANTS. This is not a general unknown-tenant
    fallback - every other tenant_id still returns None exactly as before."""
    entry = _load_registry()["tenants"].get(tenant_id) or _BUILTIN_TENANTS.get(tenant_id)
    return _public_profile(entry) if entry is not None else None


def list_profiles():
    return {tenant_id: _public_profile(entry) for tenant_id, entry in _load_registry()["tenants"].items()}


def delete_profile(tenant_id):
    with _locked_registry() as registry:
        if tenant_id not in registry["tenants"]:
            raise TenantError(f"unknown tenant {tenant_id!r}")
        del registry["tenants"][tenant_id]
        _save_registry(registry)


def _public_profile(entry):
    """Never return token_hashes to a caller - even hashed, there's no reason a profile read
    needs to expose credential material."""
    return {key: value for key, value in entry.items() if key != "token_hashes"}


def issue_token(tenant_id, admin=False, label=None):
    """Generates a new secret token, stores only its hash, and returns the plaintext token
    exactly once - the caller is responsible for delivering it to the tenant; this module never
    logs or persists it in recoverable form.

    `label` is a free-text, non-secret note on what this specific token is *for* (e.g.
    "oauth-backing", "claude-code-direct", "replit-connector") - never used for authorization,
    purely operator-facing via list_tokens() below. Exists because a token silently doing double
    duty for two different consumers is a real, easy-to-make mistake with a real consequence:
    revoking one consumer's access revokes the other's too, with no warning. A label doesn't
    prevent that by itself, but it makes "what is this token actually used for" answerable at a
    glance instead of a guess - mint a separate, distinctly-labeled token per consumer rather
    than handing the same one to two different callers."""
    with _locked_registry() as registry:
        entry = registry["tenants"].get(tenant_id)
        if entry is None:
            raise TenantError(f"unknown tenant {tenant_id!r}")
        token = secrets.token_urlsafe(32)
        entry.setdefault("token_hashes", []).append({"hash": _hash_token(token), "admin": bool(admin), "label": label})
        _save_registry(registry)
    return token


def list_tokens(tenant_id):
    """Non-secret metadata (label, admin) for every token currently issued to a tenant - never
    the hash itself, which stays exactly as unreachable as it already was via get_profile()/
    list_profiles(). For auditing "what tokens exist and what is each one actually for," the
    exact question that would have caught a token doing accidental double duty before it caused
    a real problem."""
    entry = _load_registry()["tenants"].get(tenant_id)
    if entry is None:
        raise TenantError(f"unknown tenant {tenant_id!r}")
    return [{"label": record.get("label"), "admin": bool(record.get("admin"))} for record in entry.get("token_hashes", [])]


def revoke_token(token):
    """Removes a token's hash from whichever tenant holds it. Idempotent - revoking an
    already-revoked or unknown token is a no-op, not an error, since the caller's goal (that
    token no longer works) is already satisfied either way."""
    with _locked_registry() as registry:
        target_hash = _hash_token(token)
        for entry in registry["tenants"].values():
            before = len(entry.get("token_hashes", []))
            entry["token_hashes"] = [record for record in entry.get("token_hashes", []) if record["hash"] != target_hash]
            if len(entry["token_hashes"]) != before:
                _save_registry(registry)
                return


def resolve_tenant_from_token(token):
    """Returns (tenant_id, is_admin) for a valid, non-revoked token, or (None, False) if the
    token is missing, unknown, or has been revoked - always fails closed, never falls back to
    a default tenant."""
    if not token:
        return None, False
    target_hash = _hash_token(token)
    for tenant_id, entry in _load_registry()["tenants"].items():
        for record in entry.get("token_hashes", []):
            # Comparing hashes, not the raw secret, so a timing leak here wouldn't expose
            # anything usable toward guessing a token (SHA-256's avalanche property means
            # "closer" hash bytes give no signal about the preimage) - hmac.compare_digest
            # anyway, for the same reason the shared-secret check uses it: consistency, not a
            # real exploit this closes.
            if hmac.compare_digest(record["hash"], target_hash):
                return tenant_id, bool(record.get("admin"))
    return None, False


def resolve_tenant(token, override_tenant_id=None):
    """The real resolution entrypoint a caller (the MCP server, eventually) uses. A valid
    token always resolves to its own tenant. `override_tenant_id` - the explicit admin/testing
    escape hatch - is honored ONLY when the token resolves and is flagged admin AND the override
    ID names a tenant that actually exists; any other combination fails closed (returns None),
    it never silently falls back to the caller's own tenant or a default. This is what makes a
    non-admin token unable to address another tenant's profile by passing a different ID."""
    tenant_id, is_admin = resolve_tenant_from_token(token)
    if tenant_id is None:
        return None
    if override_tenant_id is None:
        return tenant_id
    if not is_admin:
        return None
    if get_profile(override_tenant_id) is None:
        return None
    return override_tenant_id


def protected_paths_for_tenant(tenant_id):
    """Per-tenant protected-paths, shaped identically to opsgate_profiles.protected_paths_for()'s
    return value (normal_write_paths/never_access/locked_by_default) so callers can treat it as
    a drop-in match - universal baseline merged with this tenant's own frontend/backend roots
    and extra_never_access, same merge logic as the external-profile-config path in
    opsgate_profiles.py, just sourced from the tenant store instead of a walked file."""
    profile = get_profile(tenant_id)
    if profile is None:
        return None
    write_paths = [p for p in (profile.get("frontend_root"), profile.get("backend_root")) if p]
    return {
        "normal_write_paths": [f"{p.rstrip('/')}/**" for p in write_paths],
        "never_access": [*opsgate_contracts._UNIVERSAL_NEVER_ACCESS, *(profile.get("extra_never_access") or [])],
        "locked_by_default": list(opsgate_contracts._UNIVERSAL_LOCKED_BY_DEFAULT),
    }
