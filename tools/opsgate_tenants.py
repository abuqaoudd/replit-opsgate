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

Reuses opsgate_setup_lib.build_entry() directly (pure - no file I/O, no target-root coupling).
create_profile() below validates its own tenant-key pattern inline and raises TenantError on a
bad key, rather than the sys.exit(1)-on-failure style that suits a CLI script but not library
code a caller needs to catch and recover from.

Tenant resolution is token-first: a caller's auth token maps, server-side, to exactly one tenant
ID. Tokens are never stored in plaintext - only their SHA-256 hash - so a leaked registry file
does not itself leak usable credentials. An explicit tenant override exists only for admin
tokens, and is itself checked against the tenant registry (never trusted blindly), so a non-admin
token can never address another tenant's profile by passing a different ID.
"""
import copy
import hashlib
import json
import re
import secrets
from pathlib import Path

from opsgate_setup_lib import build_entry
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
        raise TenantError(f"tenant registry at {REGISTRY_PATH} is not valid JSON ({exc})") from exc
    data.setdefault("tenants", {})
    return data


def _save_registry(data):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_profile(tenant_id, frontend_root=None, backend_root=None, description=None, extra_never_access=None, business_file=None):
    """Register a new tenant. Refuses to overwrite an existing tenant_id - update_profile() is
    the explicit path for changing an existing tenant's config."""
    if not PROFILE_KEY_RE.match(tenant_id):
        raise TenantError(f"tenant id {tenant_id!r} must be lowercase letters/digits, hyphen-separated (e.g. acme, my-project)")
    registry = _load_registry()
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
    registry = _load_registry()
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
    registry = _load_registry()
    if tenant_id not in registry["tenants"]:
        raise TenantError(f"unknown tenant {tenant_id!r}")
    del registry["tenants"][tenant_id]
    _save_registry(registry)


def _public_profile(entry):
    """Never return token_hashes to a caller - even hashed, there's no reason a profile read
    needs to expose credential material."""
    return {key: value for key, value in entry.items() if key != "token_hashes"}


def issue_token(tenant_id, admin=False):
    """Generates a new secret token, stores only its hash, and returns the plaintext token
    exactly once - the caller is responsible for delivering it to the tenant; this module never
    logs or persists it in recoverable form."""
    registry = _load_registry()
    entry = registry["tenants"].get(tenant_id)
    if entry is None:
        raise TenantError(f"unknown tenant {tenant_id!r}")
    token = secrets.token_urlsafe(32)
    entry.setdefault("token_hashes", []).append({"hash": _hash_token(token), "admin": bool(admin)})
    _save_registry(registry)
    return token


def revoke_token(token):
    """Removes a token's hash from whichever tenant holds it. Idempotent - revoking an
    already-revoked or unknown token is a no-op, not an error, since the caller's goal (that
    token no longer works) is already satisfied either way."""
    registry = _load_registry()
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
            if record["hash"] == target_hash:
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
