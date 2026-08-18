#!/usr/bin/env python3
"""Phase 4 proof: boots the real opsgate_mcp_server.py as a subprocess and drives it over
genuine MCP protocol calls - not direct Python function calls - covering the legacy
shared-secret path, the Phase 1/2 tenant path (including its adversarial isolation cases), and
the Phase 3 knowledge resources/tool, all through the one fully wired system.

Creates two real tenants in the real tenants/registry.json for the duration of the run - the
point is exercising the exact file the live server reads, not an isolated copy - and removes
every tenant it creates in a `finally` block so the registry is left exactly as it started.

Requires the mcp-server/.venv environment (see mcp-server/README.md).
Run: mcp-server/.venv/bin/python3 tests/test_opsgate_mcp_integration.py
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
TOOLS_DIR = ROOT_DIR / "tools"
SERVER_DIR = ROOT_DIR / "mcp-server"
sys.path.insert(0, str(TOOLS_DIR))

import opsgate_knowledge as knowledge  # noqa: E402
import opsgate_tenants as tenants  # noqa: E402

from mcp import ClientSession  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402

RESULTS = []
SHARED_TOKEN = "integration-test-shared-secret"
TENANT_A = "integration-acme"
TENANT_B = "integration-globex"


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
    url = f"http://127.0.0.1:{port}/mcp"
    env = dict(os.environ, OPSGATE_MCP_TOKEN=SHARED_TOKEN)
    proc = subprocess.Popen(
        [sys.executable, str(SERVER_DIR / "opsgate_mcp_server.py"), "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        if not await wait_until_ready(url, SHARED_TOKEN):
            output = proc.stdout.read() if proc.stdout else ""
            record("server became ready", False, f"server never accepted a call - log:\n{output}")
            return

        # --- Legacy shared-secret path still works, unaffected by the tenant store existing ---
        legacy_profile = await call_with_token(url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
        record("legacy shared-secret token still resolves a profile", legacy_profile.structuredContent is not None or bool(legacy_profile.content))

        status = await raw_post_status(url, {})
        record("unauthenticated request still gets 401 with the tenant store wired in", status == 401)

        bad_token_status = await raw_post_status(url, {"X-Opsgate-Token": "not-a-real-token-of-any-kind"})
        record("unknown/malformed token still gets 401 (no silent fallback)", bad_token_status == 401)

        # --- Set up two real tenants in the REAL registry the running server reads ---
        tenants.create_profile(TENANT_A, frontend_root="acme-client/src", backend_root="acme-server/src", extra_never_access=["acme-secrets/**"])
        tenants.create_profile(TENANT_B, frontend_root="globex-web/src", backend_root="globex-api/src", extra_never_access=["globex-secrets/**"])
        token_a = tenants.issue_token(TENANT_A)
        token_b = tenants.issue_token(TENANT_B)
        admin_token_a = tenants.issue_token(TENANT_A, admin=True)

        async def show_profile(token):
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

        async def check_paths(token, write_paths):
            result = await call_with_token(url, token, lambda s: s.call_tool("opsgate_check_paths", {"request": {"scope": {"write_paths": write_paths}}}))
            return json.loads(result.content[0].text)

        blocked_a = await check_paths(token_a, ["acme-secrets/config.json"])
        allowed_b_on_a_path = await check_paths(token_b, ["acme-secrets/config.json"])
        record("tenant A is blocked from A's own protected path", blocked_a.get("can_proceed") is False)
        record("tenant B is NOT blocked by A's protected path (it isn't B's)", allowed_b_on_a_path.get("can_proceed") is not False)

        # --- Adversarial: revoked token fails closed immediately, through the real server ---
        tenants.revoke_token(token_a)
        revoked_status = await raw_post_status(url, {"X-Opsgate-Token": token_a})
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

        # --- Phase 3 knowledge resources/tool, consolidated one more time under the full system ---
        hitl_resource = await call_with_token(url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/hitl-protocol"))
        record("HITL protocol resource reachable under the full wired system", "Human-in-the-Loop" in hitl_resource.contents[0].text)

        skill_resource = await call_with_token(url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/skill-workflow/auth-permission-workflow"))
        record("skill-workflow resource template reachable under the full wired system", "Auth and Permission Workflow" in skill_resource.contents[0].text)

        object_resource = await call_with_token(url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/instruction-object/backend"))
        record("instruction-object resource template reachable under the full wired system", "Backend/API Instruction Object" in object_resource.contents[0].text)

        export = await call_with_token(url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_export_ruleset", {}))
        export_payload = json.loads(export.content[0].text)
        record(
            "opsgate_export_ruleset returns all three Phase 3 categories under the full wired system",
            {"hitl_protocol", "security_rules", "skill_workflows", "instruction_objects"} <= export_payload.keys(),
        )

        sync = await call_with_token(url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_sync_instructions", {}))
        sync_payload = json.loads(sync.content[0].text)
        record(
            "opsgate_sync_instructions returns replit.md plus every ai object and skill, each with its install path",
            sync_payload.get("replit_md", {}).get("path") == "replit.md"
            and "# Replit Project Instructions" in sync_payload.get("replit_md", {}).get("content", "")
            and set(sync_payload.get("ai_objects", {})) == set(knowledge.INSTRUCTION_OBJECT_NAMES)
            and all(entry["path"] == f"ai/{name}.md" for name, entry in sync_payload.get("ai_objects", {}).items())
            and set(sync_payload.get("skills", {})) == set(knowledge.list_skill_names())
            and all(entry["path"] == f".agents/skills/{skill}/SKILL.md" for skill, entry in sync_payload.get("skills", {}).items()),
        )

    finally:
        for tenant_id in (TENANT_A, TENANT_B):
            try:
                tenants.delete_profile(tenant_id)
            except tenants.TenantError:
                pass
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
