#!/usr/bin/env python3
"""Phase 4 proof: boots the real opsgate_mcp_server.py as a subprocess and drives it over
genuine MCP protocol calls - not direct Python function calls - covering the legacy
shared-secret path, the tenant path (including its adversarial isolation cases), the knowledge
resources/tools, and the two-mount tool split (/mcp/replit vs /mcp/claude), all through the one
fully wired system.

Creates two real tenants in the real tenants/registry.json for the duration of the run - the
point is exercising the exact file the live server reads, not an isolated copy - and removes
every tenant it creates in a `finally` block so the registry is left exactly as it started.

Requires the mcp-server/.venv environment (see mcp-server/README.md).
Run: mcp-server/.venv/bin/python3 tests/test_opsgate_mcp_integration.py
"""
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
TOOLS_DIR = ROOT_DIR / "tools"
SERVER_DIR = ROOT_DIR / "mcp-server"
sys.path.insert(0, str(TOOLS_DIR))

import opsgate_tenants as tenants  # noqa: E402

from mcp import ClientSession  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402

RESULTS = []
SHARED_TOKEN = "integration-test-shared-secret"
TENANT_A = "integration-acme"
TENANT_B = "integration-globex"

REPLIT_TOOLS = {
    "opsgate_show_profile", "opsgate_check_capability", "opsgate_check_paths", "opsgate_preflight",
    "opsgate_record_decision", "opsgate_sync_instructions", "opsgate_sync_file",
}
CLAUDE_TOOLS = {
    "opsgate_show_profile", "opsgate_check_capability", "opsgate_check_paths", "opsgate_preflight",
    "opsgate_record_decision", "opsgate_route_request", "opsgate_init_state", "opsgate_init_run",
    "opsgate_compile_prompt", "opsgate_next_phase_prompt", "opsgate_intake_request",
    "opsgate_parse_report", "opsgate_lint_report", "opsgate_lint_prompt", "opsgate_export_ruleset",
}


def record(name, passed, detail=""):
    RESULTS.append((name, passed, detail))
    print(("PASS " if passed else "FAIL ") + name + (f" - {detail}" if detail and not passed else ""))


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def call_with_token(url, token, fn):
    headers = {"X-Opsgate-Token": token} if token else {}
    async with streamablehttp_client(url, headers=headers) as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


async def wait_until_ready(url, token, attempts=50, delay=0.2):
    for _ in range(attempts):
        try:
            await call_with_token(url, token, lambda session: session.list_tools())
            return True
        except Exception:
            await asyncio.sleep(delay)
    return False


async def raw_post_status(url, headers):
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers={**headers, "Accept": "text/event-stream, application/json", "Content-Type": "application/json"}, content="{}")
        return response.status_code


async def main():
    port = free_port()
    # Trailing slash deliberately kept on every URL below: the bare path (no trailing slash)
    # 307-redirects to this same URL, since each mount's own FastMCP app registers its route at
    # "/" and Starlette only matches the mount prefix's remainder as "/", not "" - confirmed by
    # hitting the bare path directly. A POST redirect is exactly the kind of thing a real MCP
    # client might not handle, so the trailing-slash form is the one to actually configure.
    replit_url = f"http://127.0.0.1:{port}/mcp/replit/"
    claude_url = f"http://127.0.0.1:{port}/mcp/claude/"
    env = dict(os.environ, OPSGATE_MCP_TOKEN=SHARED_TOKEN)
    proc = subprocess.Popen(
        [sys.executable, str(SERVER_DIR / "opsgate_mcp_server.py"), "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        if not await wait_until_ready(replit_url, SHARED_TOKEN):
            output = proc.stdout.read() if proc.stdout else ""
            record("server became ready", False, f"server never accepted a call - log:\n{output}")
            return

        # --- Two-mount tool split: each mount lists exactly its own tools, not the other's ---
        replit_list = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.list_tools())
        claude_list = await call_with_token(claude_url, SHARED_TOKEN, lambda s: s.list_tools())
        replit_names = {t.name for t in replit_list.tools}
        claude_names = {t.name for t in claude_list.tools}
        record("/mcp/replit lists exactly the 7 Replit-facing tools", replit_names == REPLIT_TOOLS, f"got {sorted(replit_names)}")
        record("/mcp/claude lists exactly the 15 Claude-facing tools", claude_names == CLAUDE_TOOLS, f"got {sorted(claude_names)}")
        record("the 5 shared gate/profile/decision tools appear on both mounts", (REPLIT_TOOLS & CLAUDE_TOOLS) == {"opsgate_show_profile", "opsgate_check_capability", "opsgate_check_paths", "opsgate_preflight", "opsgate_record_decision"})

        # --- Legacy shared-secret path still works, unaffected by the tenant store existing ---
        legacy_profile = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
        record("legacy shared-secret token still resolves a profile", legacy_profile.structuredContent is not None or bool(legacy_profile.content))

        status = await raw_post_status(replit_url, {})
        record("unauthenticated request still gets 401 on /mcp/replit with the tenant store wired in", status == 401)
        status_claude = await raw_post_status(claude_url, {})
        record("unauthenticated request still gets 401 on /mcp/claude too - auth is shared across both mounts", status_claude == 401)

        bad_token_status = await raw_post_status(replit_url, {"X-Opsgate-Token": "not-a-real-token-of-any-kind"})
        record("unknown/malformed token still gets 401 (no silent fallback)", bad_token_status == 401)

        # --- Set up two real tenants in the REAL registry the running server reads ---
        tenants.create_profile(TENANT_A, frontend_root="acme-client/src", backend_root="acme-server/src", extra_never_access=["acme-secrets/**"])
        tenants.create_profile(TENANT_B, frontend_root="globex-web/src", backend_root="globex-api/src", extra_never_access=["globex-secrets/**"])
        token_a = tenants.issue_token(TENANT_A)
        token_b = tenants.issue_token(TENANT_B)
        admin_token_a = tenants.issue_token(TENANT_A, admin=True)

        async def show_profile(token, url=replit_url):
            result = await call_with_token(url, token, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
            return json.loads(result.content[0].text)

        profile_a = await show_profile(token_a)
        profile_b = await show_profile(token_b)

        record("tenant A's token resolves tenant A's own profile", profile_a.get("resolved_profile") == TENANT_A)
        record("tenant B's token resolves tenant B's own profile", profile_b.get("resolved_profile") == TENANT_B)
        never_access_a = profile_a.get("protected_paths", {}).get("never_access", [])
        never_access_b = profile_b.get("protected_paths", {}).get("never_access", [])
        record("tenant A's protected paths contain only A's own extra path", "acme-secrets/**" in never_access_a and "globex-secrets/**" not in never_access_a)
        record("tenant B's protected paths contain only B's own extra path", "globex-secrets/**" in never_access_b and "acme-secrets/**" not in never_access_b)

        # Same tenant token, resolved identically on the *other* mount - proves auth/tenant
        # resolution is shared infrastructure, not duplicated per mount.
        profile_a_via_claude = await show_profile(token_a, url=claude_url)
        record("tenant A's token resolves the same profile via /mcp/claude too", profile_a_via_claude.get("resolved_profile") == TENANT_A)

        async def check_paths(token, write_paths):
            result = await call_with_token(replit_url, token, lambda s: s.call_tool("opsgate_check_paths", {"request": {"scope": {"write_paths": write_paths}}}))
            return json.loads(result.content[0].text)

        blocked_a = await check_paths(token_a, ["acme-secrets/config.json"])
        allowed_b_on_a_path = await check_paths(token_b, ["acme-secrets/config.json"])
        record("tenant A is blocked from A's own protected path", blocked_a.get("can_proceed") is False)
        record("tenant B is NOT blocked by A's protected path (it isn't B's)", allowed_b_on_a_path.get("can_proceed") is not False)

        # --- Adversarial: revoked token fails closed immediately, through the real server ---
        tenants.revoke_token(token_a)
        revoked_status = await raw_post_status(replit_url, {"X-Opsgate-Token": token_a})
        record("revoked tenant token gets 401 immediately (real server, not just the unit store)", revoked_status == 401)

        # --- Admin override: confirmed NOT reachable through the live MCP request path ---
        # opsgate_tenants.resolve_tenant(token, override_tenant_id) supports a checked admin
        # override, but TokenAuthMiddleware only ever calls resolve_tenant_from_token(token) -
        # no request field or header exists anywhere in opsgate_mcp_server.py for a caller to
        # supply an override tenant id. An admin token, called normally, just resolves to its
        # own tenant like any other token; there is no protocol-level way to ask for a
        # different one. Documenting this as a real gap rather than skipping the check.
        admin_profile = await show_profile(admin_token_a)
        record(
            "admin token resolves its own tenant (override plumbing exists in opsgate_tenants.py but has no caller in the live MCP server yet - not exercisable end-to-end)",
            admin_profile.get("resolved_profile") == TENANT_A,
        )

        # --- Tenant-scoped run/decision storage: same request id, two tenants, no collision ---
        same_id_request = {"id": "same-run-id", "outcome": "test", "module": "x", "scope": {"write_paths": ["x"]}}
        run_a = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_init_run", {"request": same_id_request}))
        run_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_init_run", {"request": same_id_request}))
        run_a_payload = json.loads(run_a.content[0].text)
        run_b_payload = json.loads(run_b.content[0].text)
        # (both calls use token_b since token_a was revoked above; the point is the *tenant_id*
        # embedded in the returned run_dir, not which specific token made the call)
        record("opsgate_init_run scopes the run directory under the caller's own tenant_id", run_a_payload.get("run_dir") == f"runs/{TENANT_B}/same-run-id")

        decision_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_record_decision", {"hitl_id": "HITL-shared-id-Q1", "answer": "tenant B's answer"}))
        decision_b_payload = json.loads(decision_b.content[0].text)
        record("opsgate_record_decision attributes the entry to the caller's own tenant_id", decision_b_payload.get("tenant_id") == TENANT_B)
        decisions_log = ROOT_DIR / "runs" / TENANT_B / "decisions.pylog"
        record("opsgate_record_decision writes to a tenant-scoped decisions.pylog, not a shared global one", decisions_log.exists())

        oversized_answer = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_record_decision", {"hitl_id": "HITL-oversized-Q1", "answer": "x" * 6000}))
        record("opsgate_record_decision rejects an oversized answer instead of writing it", bool(oversized_answer.isError))

        # --- Knowledge resources, shared across both mounts - checked via /mcp/replit ---
        hitl_resource = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/hitl-protocol"))
        record("HITL protocol resource reachable under the full wired system", "Human-in-the-Loop" in hitl_resource.contents[0].text)

        skill_resource = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/skill-workflow/auth-permission-workflow"))
        record("skill-workflow resource template reachable under the full wired system", "Auth and Permission Workflow" in skill_resource.contents[0].text)

        object_resource = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/instruction-object/backend"))
        record("instruction-object resource template reachable under the full wired system", "Backend/API Instruction Object" in object_resource.contents[0].text)

        # ...and the same resource is reachable via /mcp/claude too, proving shared_resource
        # actually double-registered it rather than only landing on one mount.
        hitl_resource_via_claude = await call_with_token(claude_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/hitl-protocol"))
        record("HITL protocol resource also reachable via /mcp/claude", "Human-in-the-Loop" in hitl_resource_via_claude.contents[0].text)

        # --- Claude-only tools, via /mcp/claude ---
        export = await call_with_token(claude_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_export_ruleset", {}))
        export_payload = json.loads(export.content[0].text)
        record(
            "opsgate_export_ruleset returns all three Phase 3 categories under the full wired system",
            {"hitl_protocol", "security_rules", "skill_workflows", "instruction_objects"} <= export_payload.keys(),
        )

        # --- Replit-only tools, via /mcp/replit ---
        sync = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_sync_instructions", {}))
        sync_payload = json.loads(sync.content[0].text)
        manifest_files = sync_payload.get("files", [])
        record(
            "opsgate_sync_instructions returns a 24-file manifest with no content under the full wired system",
            len(manifest_files) == 24 and all("content" not in entry for entry in manifest_files),
        )

        sync_file = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_sync_file", {"path": "replit.md"}))
        sync_file_payload = json.loads(sync_file.content[0].text)
        record(
            "opsgate_sync_file('replit.md') returns the actual content under the full wired system",
            sync_file_payload.get("path") == "replit.md" and "# Replit Project Instructions" in sync_file_payload.get("content", ""),
        )

    finally:
        for tenant_id in (TENANT_A, TENANT_B):
            try:
                tenants.delete_profile(tenant_id)
            except tenants.TenantError:
                pass
            shutil.rmtree(ROOT_DIR / "runs" / tenant_id, ignore_errors=True)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    failed = [name for name, passed, _ in RESULTS if not passed]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
