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
import base64
import hashlib
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
    "opsgate_list_own_tokens", "opsgate_issue_own_token", "opsgate_revoke_own_token", "opsgate_list_audit_log",
    "opsgate_admin_create_tenant", "opsgate_admin_list_tenants", "opsgate_admin_issue_token", "opsgate_admin_revoke_token",
    "opsgate_quota_usage",
}
CLAUDE_TOOLS = {
    "opsgate_show_profile", "opsgate_check_capability", "opsgate_check_paths", "opsgate_preflight",
    "opsgate_record_decision", "opsgate_route_request", "opsgate_init_run",
    "opsgate_compile_prompt", "opsgate_next_phase_prompt", "opsgate_intake_request",
    "opsgate_parse_report", "opsgate_lint_report", "opsgate_lint_prompt", "opsgate_export_ruleset",
    "opsgate_list_own_tokens", "opsgate_issue_own_token", "opsgate_revoke_own_token", "opsgate_list_audit_log",
    "opsgate_list_runs", "opsgate_get_run",
    "opsgate_admin_create_tenant", "opsgate_admin_list_tenants", "opsgate_admin_issue_token", "opsgate_admin_revoke_token",
    "opsgate_quota_usage",
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


async def call_with_bearer_token(url, token, fn):
    """Same as call_with_token, but via `Authorization: Bearer <token>` - the header transport
    an OAuth access_token actually uses, distinct from this server's own X-Opsgate-Token."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with streamablehttp_client(url, headers=headers) as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


def read_env_file(path):
    """Same tiny KEY=VALUE parser opsgate_mcp_server.py's own _load_dotenv_if_present() uses -
    duplicated rather than imported, since this test only needs to read a few OAuth values out
    of the real mcp-server/.env to drive requests against the server, not the loader itself."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


async def oauth_authorize_and_exchange(base_url, client_id, client_secret, code_verifier=None, redirect_uri="https://claude.example/callback", state="test-state-123"):
    """Drives the full /authorize -> /token round trip exactly as an OAuth client would -
    real PKCE challenge/verifier pair unless one is deliberately overridden (the adversarial
    wrong-verifier case below passes a different one than it authorized with)."""
    import httpx

    verifier, challenge = pkce_pair()
    async with httpx.AsyncClient(follow_redirects=False) as client:
        authorize_resp = await client.get(f"{base_url}/authorize", params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        if authorize_resp.status_code != 302:
            return {"authorize_status": authorize_resp.status_code}
        location = httpx.URL(authorize_resp.headers.get("location", ""))
        code = location.params.get("code")
        token_resp = await client.post(f"{base_url}/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier if code_verifier is not None else verifier,
            "client_id": client_id,
            "client_secret": client_secret,
        })
        return {
            "authorize_status": authorize_resp.status_code,
            "returned_state": location.params.get("state"),
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier if code_verifier is not None else verifier,
            "token_status": token_resp.status_code,
            "token_body": token_resp.json() if token_resp.headers.get("content-type", "").startswith("application/json") else token_resp.text,
        }


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
        record("/mcp/replit lists exactly the 16 Replit-facing tools", replit_names == REPLIT_TOOLS, f"got {sorted(replit_names)}")
        record("/mcp/claude lists exactly the 25 Claude-facing tools", claude_names == CLAUDE_TOOLS, f"got {sorted(claude_names)}")
        record(
            "the 14 shared gate/profile/decision/token/audit/admin/quota tools appear on both mounts",
            (REPLIT_TOOLS & CLAUDE_TOOLS) == {
                "opsgate_show_profile", "opsgate_check_capability", "opsgate_check_paths", "opsgate_preflight",
                "opsgate_record_decision", "opsgate_list_own_tokens", "opsgate_issue_own_token",
                "opsgate_revoke_own_token", "opsgate_list_audit_log",
                "opsgate_admin_create_tenant", "opsgate_admin_list_tenants", "opsgate_admin_issue_token",
                "opsgate_admin_revoke_token", "opsgate_quota_usage",
            },
        )

        # --- Legacy shared-secret path still works, unaffected by the tenant store existing ---
        legacy_profile = await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
        record("legacy shared-secret token still resolves a profile", legacy_profile.structuredContent is not None or bool(legacy_profile.content))

        status = await raw_post_status(replit_url, {})
        record("unauthenticated request still gets 401 on /mcp/replit with the tenant store wired in", status == 401)
        status_claude = await raw_post_status(claude_url, {})
        record("unauthenticated request still gets 401 on /mcp/claude too - auth is shared across both mounts", status_claude == 401)

        bad_token_status = await raw_post_status(replit_url, {"X-Opsgate-Token": "not-a-real-token-of-any-kind"})
        record("unknown/malformed token still gets 401 (no silent fallback)", bad_token_status == 401)

        # --- /health: unauthenticated on purpose (a liveness probe needs to be checkable with
        # no credential), and must not require one even though every other route in this file does.
        import httpx

        async with httpx.AsyncClient() as client:
            health_resp = await client.get(f"http://127.0.0.1:{port}/health")
        record("GET /health requires no credential and reports ok", health_resp.status_code == 200 and health_resp.json().get("status") == "ok")

        # --- OAuth 2.1 + PKCE wrapper (opsgate_oauth.py), for Claude's org-level custom-
        # connector flow, which is OAuth-only. Uses the REAL configured client_id/secret/backing
        # token from mcp-server/.env, same reasoning as testing against the real tenant
        # registry above - the point is proving the exact credentials a real connector setup
        # would use, not a synthetic stand-in for them.
        #
        # `base_url` is the actual local socket the test connects to; `expected_issuer` is what
        # opsgate_oauth.issuer_base_url() should report given the REAL .env's own config
        # (OPSGATE_MCP_ALLOWED_HOSTS is already set there to the real Tailscale hostname, so the
        # metadata correctly advertises that URL, not this test's local 127.0.0.1 socket -
        # replicated here rather than assumed, so this test reflects whatever .env actually says).
        base_url = f"http://127.0.0.1:{port}"
        oauth_env = read_env_file(SERVER_DIR / ".env")
        oauth_client_id = oauth_env.get("OPSGATE_OAUTH_CLIENT_ID")
        oauth_client_secret = oauth_env.get("OPSGATE_OAUTH_CLIENT_SECRET")
        oauth_backing_token = oauth_env.get("OPSGATE_OAUTH_BACKING_TOKEN")
        allowed_hosts = [h.strip() for h in oauth_env.get("OPSGATE_MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
        expected_issuer = (oauth_env.get("OPSGATE_OAUTH_ISSUER_BASE_URL") or (f"https://{allowed_hosts[0]}" if allowed_hosts else base_url)).rstrip("/")
        # If .env pins a real redirect_uri (it does - see opsgate_oauth.py's module docstring),
        # every happy-path round trip below must use that exact value or /authorize would reject
        # it; fall back to a synthetic one only when nothing is pinned yet.
        pinned_redirect_uri = oauth_env.get("OPSGATE_OAUTH_ALLOWED_REDIRECT_URI")
        test_redirect_uri = pinned_redirect_uri or "https://claude.example/callback"
        if not (oauth_client_id and oauth_client_secret and oauth_backing_token):
            record("OAuth env vars configured in mcp-server/.env", False, "OPSGATE_OAUTH_CLIENT_ID/SECRET/BACKING_TOKEN missing - skipped every OAuth check below")
        else:
            import httpx

            async with httpx.AsyncClient() as client:
                as_metadata = (await client.get(f"{base_url}/.well-known/oauth-authorization-server")).json()
                pr_metadata = (await client.get(f"{base_url}/.well-known/oauth-protected-resource")).json()
            record(
                "OAuth authorization-server metadata advertises the configured issuer's /authorize and /token",
                as_metadata.get("authorization_endpoint") == f"{expected_issuer}/authorize" and as_metadata.get("token_endpoint") == f"{expected_issuer}/token",
                f"expected issuer {expected_issuer}, got {as_metadata}",
            )
            record(
                "OAuth protected-resource metadata names the configured issuer as its own authorization server",
                pr_metadata.get("authorization_servers") == [expected_issuer],
                f"expected issuer {expected_issuer}, got {pr_metadata}",
            )

            round_trip = await oauth_authorize_and_exchange(base_url, oauth_client_id, oauth_client_secret, redirect_uri=test_redirect_uri)
            record("OAuth /authorize redirects (302) with a code", round_trip.get("authorize_status") == 302)
            record("OAuth /authorize echoes back the caller's own state param unmodified", round_trip.get("returned_state") == "test-state-123")
            record("OAuth /token exchange succeeds (200) with a valid PKCE verifier", round_trip.get("token_status") == 200)
            issued_access_token = round_trip.get("token_body", {}).get("access_token") if isinstance(round_trip.get("token_body"), dict) else None
            record(
                "OAuth access_token IS the configured backing token - tenant resolution is unaffected by this wrapper",
                issued_access_token == oauth_backing_token,
            )

            if issued_access_token:
                bearer_profile = await call_with_bearer_token(claude_url, issued_access_token, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
                bearer_profile_payload = json.loads(bearer_profile.content[0].text)
                record(
                    "the OAuth-issued access_token authenticates a real tool call via Authorization: Bearer",
                    bool(bearer_profile_payload.get("resolved_profile")),
                )

            # --- Adversarial: a code_verifier that doesn't match the original code_challenge
            # must be rejected, not silently accepted (this is the entire security property
            # PKCE exists to provide - an intercepted `code` alone must be useless).
            wrong_verifier_result = await oauth_authorize_and_exchange(base_url, oauth_client_id, oauth_client_secret, code_verifier="this-does-not-match-the-challenge", redirect_uri=test_redirect_uri)
            record("OAuth /token rejects a code_verifier that doesn't match its code_challenge", wrong_verifier_result.get("token_status") == 400)

            # --- Adversarial: wrong client credentials must be rejected outright ---
            async with httpx.AsyncClient() as client:
                bad_client_resp = await client.post(f"{base_url}/token", data={"grant_type": "authorization_code", "code": "irrelevant", "redirect_uri": test_redirect_uri, "code_verifier": "irrelevant", "client_id": "not-the-real-client-id", "client_secret": "not-the-real-client-secret"})
                bad_authorize_resp = await client.get(f"{base_url}/authorize", params={"response_type": "code", "client_id": "not-the-real-client-id", "redirect_uri": test_redirect_uri, "code_challenge": "x", "code_challenge_method": "S256"})
            record("OAuth /token rejects a request with the wrong client_id/secret", bad_client_resp.status_code == 401)
            record("OAuth /authorize rejects a request with the wrong client_id", bad_authorize_resp.status_code == 401)

            # --- Pinned redirect_uri (OPSGATE_OAUTH_ALLOWED_REDIRECT_URI): once set, /authorize
            # must reject anything else, closing the open-redirect gap left open when unset.
            if pinned_redirect_uri:
                async with httpx.AsyncClient() as client:
                    mismatched_redirect_resp = await client.get(f"{base_url}/authorize", params={"response_type": "code", "client_id": oauth_client_id, "redirect_uri": "https://not-the-pinned-uri.example/callback", "code_challenge": "x", "code_challenge_method": "S256"})
                record("OAuth /authorize rejects a redirect_uri other than the pinned OPSGATE_OAUTH_ALLOWED_REDIRECT_URI", mismatched_redirect_resp.status_code == 400)

            # --- Adversarial: replaying an already-redeemed code must fail (single-use) ---
            replayed = await oauth_authorize_and_exchange(base_url, oauth_client_id, oauth_client_secret, redirect_uri=test_redirect_uri)
            record("first redemption of a fresh code succeeds, setting up the replay check", replayed.get("token_status") == 200)
            async with httpx.AsyncClient() as client:
                replay_resp = await client.post(f"{base_url}/token", data={
                    "grant_type": "authorization_code",
                    "code": replayed.get("code"),
                    "redirect_uri": replayed.get("redirect_uri"),
                    "code_verifier": replayed.get("code_verifier"),
                    "client_id": oauth_client_id,
                    "client_secret": oauth_client_secret,
                })
            record("OAuth /token rejects replaying an already-redeemed code", replay_resp.status_code == 400)

            # --- Discovery header: an unauthenticated 401 must point a real OAuth client at
            # where to actually go, per RFC 9728's resource-metadata discovery convention.
            async with httpx.AsyncClient() as client:
                no_auth_full = await client.post(claude_url, headers={"Content-Type": "application/json", "Accept": "text/event-stream, application/json"}, content="{}")
            record(
                "a 401 response's WWW-Authenticate header points at the configured issuer's protected-resource metadata",
                f'resource_metadata="{expected_issuer}/.well-known/oauth-protected-resource"' in no_auth_full.headers.get("www-authenticate", ""),
            )

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

        # --- Session-identity regression: with stateless_http, every request must resolve
        # identity purely from its own token, never from a reused/fabricated Mcp-Session-Id.
        # Before stateless_http was set, a stateful session's tool calls executed inside a
        # task spawned once at session-creation time - Python contextvars don't propagate
        # across tasks, so a later request's own TokenAuthMiddleware-set identity had no
        # effect on that task, and the SDK's own "session reusable only by its creating
        # credential" guard never activated here (it requires a real auth provider populating
        # scope["user"], which this server does not use). A request presenting someone else's
        # (or a fabricated) Mcp-Session-Id must resolve strictly to ITS OWN token's tenant.
        import httpx as _httpx

        async def call_raw_with_session_header(url, token, session_id):
            async with _httpx.AsyncClient() as client:
                payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "opsgate_show_profile", "arguments": {"request": {}}}}
                response = await client.post(
                    url,
                    headers={
                        "X-Opsgate-Token": token,
                        "Mcp-Session-Id": session_id,
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    content=json.dumps(payload),
                )
                return response

        foreign_session_resp = await call_raw_with_session_header(claude_url, token_b, "0" * 32)
        # The body is SSE-framed ("event: message\ndata: <json-rpc envelope>") and the tool's
        # own JSON result is itself a string inside that envelope - parse both layers rather
        # than substring-matching raw text, which would need to account for double-escaped
        # quotes and is fragile against unrelated formatting changes.
        foreign_session_resolved_profile = None
        try:
            data_line = next(line for line in foreign_session_resp.text.splitlines() if line.startswith("data: "))
            envelope = json.loads(data_line[len("data: "):])
            foreign_session_resolved_profile = json.loads(envelope["result"]["content"][0]["text"]).get("resolved_profile")
        except (StopIteration, KeyError, IndexError, json.JSONDecodeError):
            pass
        record(
            "a fabricated/foreign Mcp-Session-Id does not change which tenant a request resolves to",
            foreign_session_resp.status_code == 200 and foreign_session_resolved_profile == TENANT_B,
            f"status={foreign_session_resp.status_code} resolved_profile={foreign_session_resolved_profile!r} body={foreign_session_resp.text[:300]}",
        )

        # --- Tenant-id threading regression: opsgate_route_request must resolve the CALLER's own
        # tenant profile_roots (a real bug once silently fell back to local-dev's None/None roots
        # regardless of which tenant's token authenticated the call).
        route_a = await call_with_token(claude_url, token_a, lambda s: s.call_tool("opsgate_route_request", {"request": {"id": "route-check-a", "outcome": "test", "module": "x"}}))
        route_a_payload = json.loads(route_a.content[0].text)
        record(
            "opsgate_route_request resolves the caller's own tenant profile_roots, not local-dev's",
            route_a_payload.get("profile_roots", {}).get("frontend_root") == "acme-client/src",
        )

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

        # opsgate_init_run's own directory scoping was already correct; the bug was that the
        # route.py it persists inside that directory was computed with no tenant_id at all, so
        # it silently carried local-dev's (None, None) roots instead of the run's own tenant's.
        route_py_ns = {}
        exec((ROOT_DIR / run_a_payload["run_dir"] / "route.py").read_text(encoding="utf-8"), route_py_ns)
        record(
            "opsgate_init_run's persisted route.py reflects the run's own tenant profile_roots, not local-dev's",
            route_py_ns["ROUTE"].get("profile_roots", {}).get("frontend_root") == "globex-web/src",
        )

        decision_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_record_decision", {"hitl_id": "HITL-shared-id-Q1", "answer": "tenant B's answer"}))
        decision_b_payload = json.loads(decision_b.content[0].text)
        record("opsgate_record_decision attributes the entry to the caller's own tenant_id", decision_b_payload.get("tenant_id") == TENANT_B)
        decisions_log = ROOT_DIR / "runs" / TENANT_B / "decisions.pylog"
        record("opsgate_record_decision writes to a tenant-scoped decisions.pylog, not a shared global one", decisions_log.exists())

        oversized_answer = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_record_decision", {"hitl_id": "HITL-oversized-Q1", "answer": "x" * 6000}))
        record("opsgate_record_decision rejects an oversized answer instead of writing it", bool(oversized_answer.isError))

        # --- Structured audit log (runs/audit.jsonl): every tool call, successful or not,
        # should leave a matching entry attributing tenant_id + tool name + outcome - this is
        # what actually distinguishes "which tool did this tenant call" from uvicorn's own
        # access log, which only ever shows "POST /mcp/claude/ 200 OK" regardless of which
        # opsgate_* tool ran inside that one HTTP request.
        AUDIT_LOG_PATH = ROOT_DIR / "runs" / "audit.jsonl"
        audit_probe = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_show_profile", {"request": {}}))
        success_entry = json.loads(AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-1])
        record(
            "a successful tool call leaves a matching audit-log entry (tenant, tool, success)",
            success_entry.get("tenant_id") == TENANT_B and success_entry.get("tool") == "opsgate_show_profile" and success_entry.get("success") is True,
        )

        # A hitl_id used to have no shape requirement at all - any string got appended to
        # decisions.pylog as if it were a valid, attributable decision.
        malformed_id_decision = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_record_decision", {"hitl_id": "not-a-hitl-id-at-all", "answer": "some answer"}))
        record("opsgate_record_decision rejects a hitl_id that doesn't match the required HITL id shape", bool(malformed_id_decision.isError))
        failure_entry = json.loads(AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-1])
        record(
            "a failing tool call leaves a matching audit-log entry with success=False and an error message",
            failure_entry.get("tenant_id") == TENANT_B and failure_entry.get("tool") == "opsgate_record_decision" and failure_entry.get("success") is False and bool(failure_entry.get("error")),
        )

        # Unlike decisions.pylog (an intentionally unbounded append-only log), opsgate_init_run
        # creates a brand-new directory with several files per call and had no size cap at all -
        # a real disk-fill vector for any caller holding a valid tenant token.
        oversized_run = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_init_run", {"request": {"id": "oversized-run", "outcome": "x" * 60000, "module": "x", "scope": {"write_paths": ["x"]}}}))
        record("opsgate_init_run rejects an oversized request instead of writing it to disk", bool(oversized_run.isError))
        record("opsgate_init_run's size rejection left no directory behind", not (ROOT_DIR / "runs" / TENANT_B / "oversized-run").exists())

        # --- Self-service token lifecycle, tenant-scoped run introspection, and tenant-scoped
        # audit-log reading - the three new tool groups added to close the "MCP-exposed tenant
        # provisioning"/"observability"/"run recovery" gaps flagged in the tool audit. token_a
        # was deliberately revoked above for the earlier adversarial case, so a fresh token is
        # issued here for tenant A rather than reusing it.
        token_a2 = tenants.issue_token(TENANT_A)

        own_tokens_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_list_own_tokens", {}))
        own_tokens_b_payload = json.loads(own_tokens_b.content[0].text)
        record("opsgate_list_own_tokens returns the caller's own tenant_id", own_tokens_b_payload.get("tenant_id") == TENANT_B)

        issued = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_issue_own_token", {"label": "integration-test-rotated"}))
        issued_payload = json.loads(issued.content[0].text)
        new_token_b = issued_payload.get("token")
        record("opsgate_issue_own_token mints a usable new token for the caller's own tenant", bool(new_token_b))

        own_tokens_b_after = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_list_own_tokens", {}))
        own_tokens_b_after_payload = json.loads(own_tokens_b_after.content[0].text)
        record(
            "the newly issued token appears in opsgate_list_own_tokens, labeled and non-admin",
            any(t.get("label") == "integration-test-rotated" and t.get("admin") is False for t in own_tokens_b_after_payload.get("tokens", [])),
        )

        cross_tenant_revoke = await call_with_token(claude_url, token_a2, lambda s: s.call_tool("opsgate_revoke_own_token", {"token": new_token_b}))
        record("opsgate_revoke_own_token rejects a token belonging to a different tenant", bool(cross_tenant_revoke.isError))
        still_valid_status = await raw_post_status(replit_url, {"X-Opsgate-Token": new_token_b})
        record("a token a different tenant failed to revoke is still valid", still_valid_status != 401)

        own_revoke = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_revoke_own_token", {"token": new_token_b}))
        record("opsgate_revoke_own_token succeeds for the caller's own token", not bool(own_revoke.isError))
        revoked_status = await raw_post_status(replit_url, {"X-Opsgate-Token": new_token_b})
        record("the token is actually revoked after opsgate_revoke_own_token", revoked_status == 401)

        run_list_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_list_runs", {}))
        run_list_b_payload = json.loads(run_list_b.content[0].text)
        record(
            "opsgate_list_runs lists the caller's own tenant's run (same-run-id, created earlier)",
            any(r.get("run_id") == "same-run-id" for r in run_list_b_payload.get("runs", [])),
        )
        run_list_a = await call_with_token(claude_url, token_a2, lambda s: s.call_tool("opsgate_list_runs", {}))
        run_list_a_payload = json.loads(run_list_a.content[0].text)
        # Checked both directions, not just "B's specific run_id is absent" - a bug that leaked
        # a THIRD tenant's run into A's response (not B's) would pass the narrower check but
        # fail this one, since the response is only ever supposed to be attributed to A.
        record(
            "opsgate_list_runs does not leak tenant B's run to tenant A, and is attributed to A",
            run_list_a_payload.get("tenant_id") == TENANT_A
            and not any(r.get("run_id") == "same-run-id" for r in run_list_a_payload.get("runs", [])),
        )

        got_run_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_get_run", {"run_id": "same-run-id"}))
        got_run_b_payload = json.loads(got_run_b.content[0].text)
        record("opsgate_get_run returns the caller's own tenant's run detail", got_run_b_payload.get("request", {}).get("id") == "same-run-id")
        got_run_a_cross = await call_with_token(claude_url, token_a2, lambda s: s.call_tool("opsgate_get_run", {"run_id": "same-run-id"}))
        record("opsgate_get_run rejects a run_id belonging to a different tenant", bool(got_run_a_cross.isError))

        audit_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_list_audit_log", {}))
        audit_b_payload = json.loads(audit_b.content[0].text)
        audit_b_entries = audit_b_payload.get("entries", [])
        record(
            "opsgate_list_audit_log returns only the caller's own tenant's entries, and at least one",
            len(audit_b_entries) > 0 and all(e.get("tenant_id") == TENANT_B for e in audit_b_entries),
        )
        audit_a = await call_with_token(claude_url, token_a2, lambda s: s.call_tool("opsgate_list_audit_log", {}))
        audit_a_payload = json.loads(audit_a.content[0].text)
        audit_a_entries = audit_a_payload.get("entries", [])
        # Checked both directions, matching the rigor of the B-side check above - every entry
        # returned must actually be A's own, not merely "missing one specific B entry" (which
        # a leak of some OTHER tenant's entry would still pass).
        record(
            "opsgate_list_audit_log does not leak tenant B's activity to tenant A, and every entry is A's own",
            all(e.get("tenant_id") == TENANT_A for e in audit_a_entries)
            and not any(e.get("tool") == "opsgate_issue_own_token" for e in audit_a_entries),
        )

        # --- Quota visibility (no enforcement) ---
        quota_b = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_quota_usage", {}))
        quota_b_payload = json.loads(quota_b.content[0].text)
        record(
            "opsgate_quota_usage reports the caller's own tenant_id and a non-empty tool breakdown",
            quota_b_payload.get("tenant_id") == TENANT_B and quota_b_payload.get("total_calls_recorded", 0) > 0,
        )
        quota_a = await call_with_token(claude_url, token_a2, lambda s: s.call_tool("opsgate_quota_usage", {}))
        quota_a_payload = json.loads(quota_a.content[0].text)
        record(
            "opsgate_quota_usage does not leak tenant B's call counts into tenant A's report, and is attributed to A",
            quota_a_payload.get("tenant_id") == TENANT_A
            and "opsgate_issue_own_token" not in quota_a_payload.get("calls_by_tool", {}),
        )

        # --- Admin-gated tenant provisioning: opsgate_admin_create_tenant/list_tenants/
        # issue_token/revoke_token. admin_token_a (issued above with admin=True) is the only
        # token in this test flagged admin - every non-admin token must be rejected outright.
        TENANT_C = "integration-admin-provisioned"
        non_admin_create = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_admin_create_tenant", {"tenant_id": TENANT_C}))
        record("opsgate_admin_create_tenant rejects a non-admin token", bool(non_admin_create.isError))

        non_admin_list = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_admin_list_tenants", {}))
        record("opsgate_admin_list_tenants rejects a non-admin token", bool(non_admin_list.isError))

        # opsgate_admin_issue_token is the single most privilege-sensitive admin tool (mints a
        # token for any tenant, optionally admin-flagged itself) - its non-admin rejection had
        # no test coverage, unlike its three siblings above/below.
        non_admin_issue = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_admin_issue_token", {"tenant_id": TENANT_A, "label": "should-never-be-minted"}))
        record("opsgate_admin_issue_token rejects a non-admin token", bool(non_admin_issue.isError))

        try:
            admin_created = await call_with_token(claude_url, admin_token_a, lambda s: s.call_tool("opsgate_admin_create_tenant", {"tenant_id": TENANT_C, "frontend_root": "admin-provisioned/src"}))
            record("opsgate_admin_create_tenant succeeds for an admin token", not bool(admin_created.isError))

            admin_list = await call_with_token(claude_url, admin_token_a, lambda s: s.call_tool("opsgate_admin_list_tenants", {}))
            admin_list_payload = json.loads(admin_list.content[0].text)
            record(
                "opsgate_admin_list_tenants sees every tenant, not just the admin's own",
                {TENANT_A, TENANT_B, TENANT_C} <= set(admin_list_payload.get("tenants", {}).keys()),
            )

            # An admin token issuing a token for a DIFFERENT tenant than its own - the whole
            # point of opsgate_admin_issue_token over the self-service opsgate_issue_own_token.
            admin_issued = await call_with_token(claude_url, admin_token_a, lambda s: s.call_tool("opsgate_admin_issue_token", {"tenant_id": TENANT_C, "label": "admin-provisioned-token"}))
            admin_issued_payload = json.loads(admin_issued.content[0].text)
            new_c_token = admin_issued_payload.get("token")
            record("opsgate_admin_issue_token mints a token for a different tenant than the caller's own", bool(new_c_token))

            profile_c = await show_profile(new_c_token)
            record("the admin-issued token actually resolves to the target tenant", profile_c.get("resolved_profile") == TENANT_C)

            non_admin_revoke = await call_with_token(claude_url, token_b, lambda s: s.call_tool("opsgate_admin_revoke_token", {"token": new_c_token}))
            record("opsgate_admin_revoke_token rejects a non-admin token", bool(non_admin_revoke.isError))

            admin_revoked = await call_with_token(claude_url, admin_token_a, lambda s: s.call_tool("opsgate_admin_revoke_token", {"token": new_c_token}))
            record("opsgate_admin_revoke_token succeeds for an admin token, on a token belonging to a different tenant", not bool(admin_revoked.isError))
            revoked_c_status = await raw_post_status(replit_url, {"X-Opsgate-Token": new_c_token})
            record("the admin-revoked token is actually rejected afterward", revoked_c_status == 401)
        finally:
            try:
                tenants.delete_profile(TENANT_C)
            except tenants.TenantError:
                pass
            shutil.rmtree(ROOT_DIR / "runs" / TENANT_C, ignore_errors=True)

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

        # --- Claude MCP workflow resource: Claude-only, unlike the shared ones above - this is
        # the whole point of exposing it this way instead of a per-person plugin/skill upload.
        claude_workflow_resource = await call_with_token(claude_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/claude-mcp-workflow"))
        record("Claude MCP workflow resource reachable via /mcp/claude with no plugin installed", "opsgate_intake_request" in claude_workflow_resource.contents[0].text)
        claude_workflow_missing_on_replit = False
        try:
            await call_with_token(replit_url, SHARED_TOKEN, lambda s: s.read_resource("opsgate://knowledge/claude-mcp-workflow"))
        except Exception:
            claude_workflow_missing_on_replit = True
        record("Claude MCP workflow resource is correctly absent from /mcp/replit (Replit doesn't need it)", claude_workflow_missing_on_replit)

        # --- Claude-only tools, via /mcp/claude ---
        export = await call_with_token(claude_url, SHARED_TOKEN, lambda s: s.call_tool("opsgate_export_ruleset", {}))
        export_payload = json.loads(export.content[0].text)
        record(
            "opsgate_export_ruleset returns all four categories under the full wired system",
            {"hitl_protocol", "security_rules", "claude_mcp_workflow", "skill_workflows", "instruction_objects"} <= export_payload.keys(),
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
