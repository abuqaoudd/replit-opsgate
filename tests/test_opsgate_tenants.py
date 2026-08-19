#!/usr/bin/env python3
"""Isolation and adversarial-case tests for the multi-tenant profile store
(opsgate_tenants.py): two tenants never leak into each other, a revoked token loses access
immediately, a non-admin cross-tenant override attempt is rejected, a malformed/unknown
tenant ID fails closed rather than falling back to a default, and a tenant's mcp_enabled flag
correctly switches opsgate.compile_prompt_text()'s HITL gate language without requiring every
caller to pass request["mcp"]["enabled"] itself.

Standalone, not yet wired into test-all.py. Uses an isolated temp registry file so it never
touches or depends on a real tenants/registry.json.

Run: python3 tests/test_opsgate_tenants.py
"""
import sys
import tempfile
import threading
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "tools"))

import opsgate  # noqa: E402  (same module instance opsgate_tenants.py's redirected REGISTRY_PATH below reaches, since sys.path/module caching are shared)
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

        # --- Token labels: operator-facing metadata for "what is this specific token for",
        # so two different consumers never end up silently sharing one token by accident.
        labeled_token = tenants.issue_token("acme", label="ci-pipeline")
        unlabeled_token = tenants.issue_token("acme")
        acme_tokens = tenants.list_tokens("acme")
        record("list_tokens reflects a token's label", any(entry.get("label") == "ci-pipeline" for entry in acme_tokens))
        record("list_tokens reports label=None for a token issued with no label", any(entry.get("label") is None for entry in acme_tokens))
        record("list_tokens never exposes a token hash", all("hash" not in entry for entry in acme_tokens))
        record("list_tokens on an unknown tenant raises, not returns an empty list", expect_raises(tenants.list_tokens, "does-not-exist"))
        record("a labeled token still resolves and authenticates normally", tenants.resolve_tenant(labeled_token) == "acme")
        tenants.revoke_token(labeled_token)
        tenants.revoke_token(unlabeled_token)

        # --- Concurrency: the registry's read-modify-write cycle must not lose a write to a
        # race. Without _locked_registry(), two near-simultaneous issue_token() calls for
        # different tenants could each load the registry before the other saves, and whichever
        # saves last would silently overwrite the other's new token with a stale in-memory copy
        # (a lost update) - real risk on a file the tenant registry is the entire trust boundary
        # for. Deliberately widens the load-to-save window (via a patched, slower _load_registry)
        # well past what real disk I/O would ever take, so this test would reliably fail if the
        # lock were ever removed or a new mutator forgot to use it.
        original_load_registry = tenants._load_registry

        def slow_load_registry():
            data = original_load_registry()
            time.sleep(0.05)
            return data

        race_tenants = [f"race-tenant-{i}" for i in range(8)]
        for race_tenant in race_tenants:
            tenants.create_profile(race_tenant, frontend_root="x")
        issued = {}
        tenants._load_registry = slow_load_registry
        try:
            barrier = threading.Barrier(len(race_tenants))

            def issue_for(race_tenant):
                barrier.wait()
                issued[race_tenant] = tenants.issue_token(race_tenant)

            race_threads = [threading.Thread(target=issue_for, args=(race_tenant,)) for race_tenant in race_tenants]
            for thread in race_threads:
                thread.start()
            for thread in race_threads:
                thread.join()
        finally:
            tenants._load_registry = original_load_registry
        record(
            "concurrent issue_token calls for different tenants under a widened race window all persist (no lost update)",
            all(tenants.resolve_tenant(issued.get(race_tenant)) == race_tenant for race_tenant in race_tenants),
        )

        # --- mcp_enabled tenant flag: compile_prompt_text should switch to the "call these
        # tools directly" gate language automatically for a tenant whose Replit project has
        # real MCP tools registered, without every caller needing to remember to pass
        # request["mcp"]["enabled"] itself on every single compile call.
        mcp_request = {"id": "REQ-MCP-FLAG", "deliverable": "replit_prompt", "outcome": "test", "module": "x", "scope": {"write_paths": ["client/src/x"]}}
        record(
            "a tenant with no mcp_enabled flag gets the manual prose HITL gate by default",
            "MCP mode" not in opsgate.compile_prompt_text(mcp_request, tenant_id="acme"),
        )
        tenants.update_profile("acme", mcp_enabled=True)
        record(
            "setting mcp_enabled=True on a tenant's profile switches compile_prompt_text to MCP-mode gate language with no per-request flag needed",
            "MCP mode" in opsgate.compile_prompt_text(mcp_request, tenant_id="acme"),
        )
        override_request = {**mcp_request, "mcp": {"enabled": False}}
        record(
            "an explicit request-level mcp.enabled always overrides the tenant's own default, in either direction",
            "MCP mode" not in opsgate.compile_prompt_text(override_request, tenant_id="acme"),
        )

    failed = [name for name, passed, _ in RESULTS if not passed]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed.")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        sys.exit(1)
    print("PASS test-opsgate-tenants: isolation and adversarial cases hold.")


if __name__ == "__main__":
    main()
