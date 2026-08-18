#!/usr/bin/env python3
"""Isolation and adversarial-case tests for the multi-tenant profile store
(opsgate_tenants.py): two tenants never leak into each other, a revoked token loses access
immediately, a non-admin cross-tenant override attempt is rejected, and a malformed/unknown
tenant ID fails closed rather than falling back to a default.

Standalone, not yet wired into test-all.py. Uses an isolated temp registry file so it never
touches or depends on a real tenants/registry.json.

Run: python3 tests/test_opsgate_tenants.py
"""
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "tools"))

import opsgate_tenants as tenants  # noqa: E402

RESULTS = []


def record(name, passed, detail=""):
    RESULTS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}" + (f" - {detail}" if detail and not passed else ""))


def expect_raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return False
    except tenants.TenantError:
        return True


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tenants.REGISTRY_PATH = Path(tmp) / "registry.json"

        # --- Setup: two real tenants with distinct config ---
        tenants.create_profile("acme", frontend_root="client/src", backend_root="server/src", extra_never_access=["billing/**"])
        tenants.create_profile("globex", frontend_root="web/app", backend_root="api/app", extra_never_access=["secrets-vault/**"])
        acme_token = tenants.issue_token("acme")
        globex_token = tenants.issue_token("globex")
        acme_admin_token = tenants.issue_token("acme", admin=True)

        # --- Two-tenant isolation ---
        record("acme token resolves to acme", tenants.resolve_tenant(acme_token) == "acme")
        record("globex token resolves to globex", tenants.resolve_tenant(globex_token) == "globex")
        record("acme token does not resolve to globex", tenants.resolve_tenant(acme_token) != "globex")

        acme_paths = tenants.protected_paths_for_tenant("acme")
        globex_paths = tenants.protected_paths_for_tenant("globex")
        record("acme protected paths contain only acme's extra path", "billing/**" in acme_paths["never_access"] and "secrets-vault/**" not in acme_paths["never_access"])
        record("globex protected paths contain only globex's extra path", "secrets-vault/**" in globex_paths["never_access"] and "billing/**" not in globex_paths["never_access"])
        record("both tenants still get the universal baseline", ".env" in acme_paths["never_access"] and ".env" in globex_paths["never_access"])

        # --- Adversarial: revoked token loses access immediately ---
        throwaway_token = tenants.issue_token("acme")
        record("throwaway token resolves before revocation", tenants.resolve_tenant(throwaway_token) == "acme")
        tenants.revoke_token(throwaway_token)
        record("revoked token fails closed immediately", tenants.resolve_tenant(throwaway_token) is None)
        record("acme's other token is unaffected by revoking a different one", tenants.resolve_tenant(acme_token) == "acme")

        # --- Adversarial: cross-tenant override attempt (non-admin) is rejected ---
        record("non-admin override attempt is rejected, not silently granted", tenants.resolve_tenant(acme_token, override_tenant_id="globex") is None)

        # --- Positive control: admin override actually works when properly scoped ---
        record("admin token can validly override to another real tenant", tenants.resolve_tenant(acme_admin_token, override_tenant_id="globex") == "globex")

        # --- Adversarial: malformed/unknown tenant ID fails closed ---
        record("unknown tenant get_profile returns None, not a default", tenants.get_profile("does-not-exist") is None)
        record("admin override to a nonexistent tenant is rejected, not silently granted", tenants.resolve_tenant(acme_admin_token, override_tenant_id="does-not-exist") is None)
        record("empty/missing token fails closed", tenants.resolve_tenant("") is None)
        record("invalid profile key format is rejected", expect_raises(tenants.create_profile, "Not A Valid Key!"))

        # --- Hygiene: duplicate tenant, token_hashes protection, no credential leakage ---
        record("duplicate tenant creation is rejected", expect_raises(tenants.create_profile, "acme", frontend_root="x"))
        record("update_profile cannot touch token_hashes directly", expect_raises(tenants.update_profile, "acme", token_hashes=["forged"]))
        record("list_profiles never exposes token_hashes", "token_hashes" not in tenants.list_profiles()["acme"])
        record("get_profile never exposes token_hashes", "token_hashes" not in tenants.get_profile("acme"))

    failed = [name for name, passed, _ in RESULTS if not passed]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed.")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        sys.exit(1)
    print("PASS test-opsgate-tenants: isolation and adversarial cases hold.")


if __name__ == "__main__":
    main()
