#!/usr/bin/env python3
"""HTTP MCP server exposing this engine's own gate/routing tools remotely.

Every tool below calls opsgate.py's pure core functions (check_capabilities_result,
check_paths_result, preflight_result, etc.) directly, in-process - no temp files, no stdout
capture. The CLI's own cmd_* wrappers still exist unchanged for `python3 tools/opsgate.py
<command>`, but this server calls straight past them into the pure functions they themselves
call. Nothing about routing, gate logic, or prompt compilation is duplicated here; the pure
functions in opsgate.py/opsgate_prompts.py/opsgate_tenants.py are the single source of truth
for both callers.

Tool names match the convention `replit.md` Section 10 already documents
("MCP tool availability") - `opsgate_` prefix, e.g. `opsgate_check_capability`,
`opsgate_check_paths`, `opsgate_preflight`, `opsgate_record_decision`, plus the
routing/lint tools it mentions in passing. A Replit Agent that already reads
that section needs no new instructions to use this server once it is
registered - the tool names it was told to expect are the tool names here.

Where this lives: `<engine-dir>/mcp-server/opsgate_mcp_server.py`, a sibling
of `tools/`. It imports `opsgate.py` directly from the real `tools/`
directory next to it, so `ROOT_DIR` inside that module resolves exactly the
way it does for the CLI - this server does not run against a copy.

Which tenant this server answers for, per call: the `X-Opsgate-Token` header value is checked
first against the multi-tenant store (`opsgate_tenants.resolve_tenant_from_token`) - if it
resolves, that tenant's own profile/protected-paths from the tenant store govern the call. If
the header does not match any tenant token, it falls back to the single shared
`--token`/`OPSGATE_MCP_TOKEN` server-access secret, and the call resolves to
`opsgate_tenants.LOCAL_DEV_TENANT_ID` - a safe, always-available default with no roots assumed.
Both paths are real and fully supported at once.

Run:

    python3 mcp-server/opsgate_mcp_server.py [--host 127.0.0.1] [--port 8765] [--token <shared-secret>]

Requires the `mcp` package (`pip install mcp`). Talks HTTP ("streamable-http"
transport) so a remote client (e.g. Replit's Connect via MCP) can reach it
once it is exposed through a tunnel - this file only starts the local server;
it does not expose it to the internet by itself.

Every request must carry an `X-Opsgate-Token: <token>` header - there is no
unauthenticated path, since this server has real side effects
(`opsgate_init_run` writes to disk) and is meant to end up reachable through a
public tunnel. A custom header, not `Authorization`, because Cloudflare's free
account-less quick tunnels (trycloudflare.com) reject any request carrying an
Authorization header at the edge - confirmed empirically, see the comment
above TokenAuthMiddleware below. Set `--token`/`OPSGATE_MCP_TOKEN` to a fixed value so it
survives restarts; if neither is set, a random token is generated and printed
once to stderr at startup. See `mcp-server/README.md` for details.
"""

import argparse
import contextvars
import hmac
import os
import secrets
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
ENGINE_TOOLS_DIR = SERVER_DIR.parent / "tools"
if not (ENGINE_TOOLS_DIR / "opsgate.py").exists():
    sys.exit(
        f"Expected to find opsgate.py in {ENGINE_TOOLS_DIR}, but it is not there.\n"
        "This server must live in a 'mcp-server/' folder that sits next to this engine's "
        "own 'tools/' folder (i.e. <engine-dir>/mcp-server/opsgate_mcp_server.py) - move it "
        "there and re-run."
    )
sys.path.insert(0, str(ENGINE_TOOLS_DIR))

import opsgate  # noqa: E402  (import must follow the sys.path fix-up above)
import opsgate_knowledge  # noqa: E402
import opsgate_tenants  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.exit("The 'mcp' package is not installed. Run: pip install mcp")

try:
    import uvicorn
    from starlette.responses import JSONResponse
except ImportError:
    sys.exit("The 'uvicorn'/'starlette' packages are not installed - they should come with 'mcp'. Run: pip install mcp")


mcp = FastMCP(
    name="opsgate",
    instructions=(
        "Gate, routing, and lint tools for this project's own Replit-agent orchestration "
        "engine. See this project's replit.md (Section 10, 'MCP tool availability') for "
        "when and how an Agent should call these instead of re-deriving the same checks by "
        "hand."
    ),
)


# ---------------------------------------------------------------------------
# Tenant resolution. TokenAuthMiddleware (below) sets this contextvar to the
# resolved tenant ID for the duration of each HTTP request, before the MCP
# request-handling code runs in the same async task - reading it here from
# inside a tool function gets the exact token that authenticated this call,
# with no dependency on any MCP-SDK-internal request-context mechanism.
# `None` means the shared-secret path (no tenant token) authenticated this
# call; _active_tenant_id() resolves that to opsgate_tenants.LOCAL_DEV_TENANT_ID,
# the same safe, always-available identity the bare CLI defaults to.
# ---------------------------------------------------------------------------

_current_tenant_id = contextvars.ContextVar("_current_tenant_id", default=None)


def _active_tenant_id():
    return _current_tenant_id.get() or opsgate_tenants.LOCAL_DEV_TENANT_ID


# ---------------------------------------------------------------------------
# Tools - one per runtime cmd_* function in opsgate.py. Maintenance-only
# commands (validate-json, validate-engine, test-all) are deliberately not
# exposed here - those are engine-authoring operations run by hand inside
# this repo, not gate/routing calls a live Replit task needs.
# ---------------------------------------------------------------------------


@mcp.tool(
    name="opsgate_route_request",
    description=(
        "Resolve which deliverable, mode, skill, references, and execution shape a request "
        "routes to, given its deliverable/outcome/module/acceptance/authorizations/scope "
        "fields. Read-only; does not check gates by itself (use opsgate_preflight for that)."
    ),
)
def opsgate_route_request(request: dict) -> dict:
    return opsgate.route_request(request or {})


@mcp.tool(
    name="opsgate_check_capability",
    description=(
        "Deterministic capability_gate check: does this request's own authorizations cover "
        "every capability its route requires? `can_proceed: false` means an authorization is "
        "missing - report it as a blocked gate, never as a HITL decision."
    ),
)
def opsgate_check_capability(request: dict) -> dict:
    return opsgate.check_capabilities_result(request or {})


@mcp.tool(
    name="opsgate_check_paths",
    description=(
        "Deterministic protected_path_gate check: do this request's write/read scope paths "
        "touch any path the active profile protects? `can_proceed: false` names the exact "
        "violation(s) - report as blocked, never as a HITL decision."
    ),
)
def opsgate_check_paths(request: dict) -> dict:
    return opsgate.check_paths_result(request or {}, tenant_id=_active_tenant_id())


@mcp.tool(
    name="opsgate_preflight",
    description=(
        "Run every deterministic gate (scope_gate, capability_gate, protected_path_gate) in "
        "one call before the first edit, before each phase, and before the final report. "
        "`can_proceed: false` lists every failed gate by name - none of them are HITL "
        "decisions; they mean an authorization, scope, or evidence grant is missing."
    ),
)
def opsgate_preflight(request: dict) -> dict:
    return opsgate.preflight_result(request or {}, tenant_id=_active_tenant_id())


@mcp.tool(
    name="opsgate_show_profile",
    description=(
        "Show which profile is currently active (tenant token, env var, request field, or "
        "default), its resolved frontend/backend roots, and its protected paths - with no "
        "request required. Pass an empty object, or a request with a \"profile\" field to "
        "check a specific legacy (non-tenant) profile."
    ),
)
def opsgate_show_profile(request: dict | None = None) -> dict:
    return opsgate.show_profile_result(request or {}, tenant_id=_active_tenant_id())


@mcp.tool(
    name="opsgate_init_state",
    description=(
        "Build the initial run-state object (status, phases if execution is phased, empty "
        "decisions/checks lists) for a request, based on its resolved route. Read-only - does "
        "not write anything to disk (use opsgate_init_run for that)."
    ),
)
def opsgate_init_state(request: dict) -> dict:
    return opsgate.init_state_result(request or {})


@mcp.tool(
    name="opsgate_init_run",
    description=(
        "Create a runs/<request-id>/ directory on this server's own machine with the "
        "request, its resolved route, initial gate result, and initial handoff state "
        "persisted as files. Has a real side effect on disk under this project's runs/ "
        "folder - only call this to actually start tracking a run, not to preview one."
    ),
)
def opsgate_init_run(request: dict) -> dict:
    return opsgate.init_run_result(request or {})


@mcp.tool(
    name="opsgate_compile_prompt",
    description=(
        "Compile a full Replit prompt or artifact-authoring prompt (scope, HITL gate, "
        "execution shape, final-report structure, etc.) from a request. Returns prose text, "
        "not JSON - this is the actual prompt to hand to the implementing agent/session."
    ),
)
def opsgate_compile_prompt(request: dict) -> str:
    return opsgate.compile_prompt_text(request or {}, tenant_id=_active_tenant_id())


@mcp.tool(
    name="opsgate_next_phase_prompt",
    description=(
        "Given a run's current state and the parsed report from its most recently completed "
        "phase, produce the prompt for the next planned/ready phase - or a 'Phase Blocked' / "
        "'No Next Phase' message if the previous phase failed or nothing is left to run. "
        "Returns prose text, not JSON."
    ),
)
def opsgate_next_phase_prompt(run_state: dict, parsed_report: dict) -> str:
    return opsgate.next_phase_prompt_text(run_state or {}, parsed_report or {})


@mcp.tool(
    name="opsgate_intake_request",
    description=(
        "Turn a single plain-language sentence describing what someone wants (no JSON, no "
        "field names) into a draft request object - deliverable, outcome, module, and any "
        "authorizations it looks like the request will need. A starting point to refine, not "
        "a final answer if the deliverable comes back ambiguous (see intake_notes)."
    ),
)
def opsgate_intake_request(text: str) -> dict:
    return opsgate.intake_request_result(text or "")


@mcp.tool(
    name="opsgate_parse_report",
    description=(
        "Parse a final-report markdown document into structured fields: outcome, acceptance "
        "status, files changed, PASSED/FAILED/NOT RUN checks, HITL decision references, "
        "blockers, and residual risk. Feed its output into opsgate_next_phase_prompt."
    ),
)
def opsgate_parse_report(report_markdown: str) -> dict:
    return opsgate.parse_report_result(report_markdown or "")


@mcp.tool(
    name="opsgate_lint_report",
    description=(
        "Check whether a final-report markdown document has every required section (HITL "
        "Gate Result table with all required rows, Files Changed, Checks, Protected Path "
        "Compliance, Residual Risk) filled in with real evidence, not placeholders. "
        "`pass: false` lists exactly what's missing or weak."
    ),
)
def opsgate_lint_report(report_markdown: str) -> dict:
    return opsgate.lint_report_result(report_markdown or "")


@mcp.tool(
    name="opsgate_lint_prompt",
    description=(
        "Check whether a compiled Replit prompt states every required concept (scope/phase "
        "boundary, never-access boundary, HITL pause policy, acceptance criteria, "
        "PASSED/FAILED/NOT RUN labeling, final report section) and, if it emits a HITL "
        "decision block, that the block is well-formed. `pass: false` lists what's missing."
    ),
)
def opsgate_lint_prompt(prompt_markdown: str) -> dict:
    return opsgate.lint_prompt_result(prompt_markdown or "")


@mcp.tool(
    name="opsgate_record_decision",
    description=(
        "Persist a human's answer to a HITL decision (by its HITL-ID) to this server's own "
        "runs/decisions.pylog, so the decision survives outside the current conversation. "
        "Call this immediately after a human answers a HITL question, before resuming work."
    ),
)
def opsgate_record_decision(hitl_id: str, answer: str) -> dict:
    return opsgate.record_decision_result(hitl_id, answer)


# ---------------------------------------------------------------------------
# Always-on knowledge resources - not tenant-scoped or route-conditional, unlike the tools
# above; every caller gets the same durable rules regardless of profile or request shape.
# opsgate_knowledge.py reads these live from their canonical source files, so nothing here
# can drift out of sync with that source.
# ---------------------------------------------------------------------------


@mcp.resource(
    "opsgate://knowledge/hitl-protocol",
    name="HITL protocol",
    description="The full Human-in-the-Loop specification: exclusive triggers, pre-trigger test, check frequency, pause contract, decision request format, resume protocol, and final evidence.",
    mime_type="text/markdown",
)
def opsgate_hitl_protocol_resource() -> str:
    return opsgate_knowledge.hitl_protocol_text()


@mcp.resource(
    "opsgate://knowledge/security-rules",
    name="Security rules",
    description="Durable security rules (identity, authorization, sensitive data, uploads, logging, mutations, integrations, leakage prevention) - routing/activation prose is omitted since this resource is always on.",
    mime_type="text/markdown",
)
def opsgate_security_rules_resource() -> str:
    return opsgate_knowledge.security_rules_text()


@mcp.resource(
    "opsgate://knowledge/skill-workflow/{skill}",
    name="Skill workflow",
    description=(
        "The durable numbered workflow procedure for one replit-skills entry (e.g. "
        "'auth-permission-workflow', 'database-schema-migration') - unlike the HITL/security "
        "resources above, this is per-skill, not always-on: fetch it for the specific skill "
        "opsgate_route_request/opsgate_compile_prompt resolved for the current request. Routing "
        "scaffolding (frontmatter, mode-select sentence, reference-reading step) is already "
        "covered by ROUTING_MANIFEST and opsgate_compile_prompt's own output, so it's omitted here."
    ),
    mime_type="text/markdown",
)
def opsgate_skill_workflow_resource(skill: str) -> str:
    return opsgate_knowledge.skill_workflow_text(skill)


@mcp.resource(
    "opsgate://knowledge/instruction-object/{name}",
    name="Instruction object",
    description=(
        "The durable rules of one ai/*.md domain instruction object (e.g. 'backend', "
        "'frontend', 'database', 'ui-ux', 'testing', 'refactoring', 'agents', 'maintenance' - "
        "'security' is also reachable here, though it's covered unconditionally by the "
        "always-on security-rules resource above). Per-route, not always-on: fetch the ones "
        "named in the current route's ROUTING_MANIFEST references, surfaced via "
        "opsgate_route_request/opsgate_compile_prompt. Routing scaffolding (the object's "
        "Activation section and, for most objects, its pre-Activation summary line) is "
        "already covered by that same routing data, so it's omitted here."
    ),
    mime_type="text/markdown",
)
def opsgate_instruction_object_resource(name: str) -> str:
    return opsgate_knowledge.instruction_object_text(name)


@mcp.tool(
    name="opsgate_export_ruleset",
    description=(
        "Read-only snapshot of every rule this server currently exposes as knowledge "
        "resources - the always-on HITL protocol and security rules, every per-skill workflow "
        "procedure keyed by skill name, and every domain instruction object keyed by name - "
        "along with the canonical source path each came from. For offline/CI use where "
        "reading the live MCP resources isn't practical."
    ),
)
def opsgate_export_ruleset() -> dict:
    return opsgate_knowledge.export_ruleset()


@mcp.tool(
    name="opsgate_sync_instructions",
    description=(
        "Read-only: returns everything needed to install or refresh a project's own copy of "
        "this engine's instruction system - replit.md, every ai/*.md instruction object, and "
        "every skill workflow file - each with its own target install `path` (skill files "
        "install under `.agents/skills/<skill>/SKILL.md`, a different directory name than "
        "this engine's own `replit-skills/` source layout). This server cannot write into the "
        "calling project's own filesystem - the caller must write each returned `content` to "
        "its `path` verbatim, creating anything missing and overwriting anything that "
        "differs, then re-read each to confirm the write succeeded. Works the same way for a "
        "brand-new project (nothing installed yet - write every entry) and a stale existing "
        "one (write only what differs). Does not create tenants or issue tokens - that stays "
        "a separate, deliberate step (see ADOPTION_GUIDE.md), never self-service via this "
        "tool. See ai/maintenance.md for the full instruction-maintenance workflow."
    ),
)
def opsgate_sync_instructions() -> dict:
    return opsgate_knowledge.project_files_bundle()


# ---------------------------------------------------------------------------
# Auth. This server has real side effects (opsgate_init_run writes to disk,
# opsgate_record_decision appends to a log) and is meant to be reached through
# a public tunnel once registered with Replit's "Connect via MCP" - so it must
# never serve requests with no credential check, regardless of --host. A
# shared token is required on every request; if one isn't supplied via
# --token/OPSGATE_MCP_TOKEN, a random one is generated and printed once at
# startup so a first run still works without extra setup, it just cannot be
# guessed or skipped.
#
# Deliberately a custom header (X-Opsgate-Token), not "Authorization: Bearer
# <token>": Cloudflare's free, account-less "quick tunnels" (trycloudflare.com,
# used by `cloudflared tunnel --url ...` with no login) reject any request
# carrying an Authorization header at the edge - confirmed empirically (a
# request with only that header back gets HTTP 421 "Invalid Host header"
# straight from Cloudflare, never reaching this process; the identical request
# with a custom header name passes through untouched). Presumably an anti-abuse
# measure against using shared throwaway domains to relay stolen credentials.
# A custom header carries the same secret with the same protection and isn't
# subject to that block.
# ---------------------------------------------------------------------------

AUTH_HEADER_NAME = b"x-opsgate-token"


class TokenAuthMiddleware:
    """Checks the X-Opsgate-Token header against the tenant store first - if it resolves to a
    real tenant, that tenant governs this call (see _active_tenant_id() above) and the shared-
    secret check below is skipped entirely for this request. If it does not resolve to any
    tenant, this falls back to the single shared --token/OPSGATE_MCP_TOKEN secret, checked with
    the same constant-time comparison either way. A request that matches neither is rejected -
    there is no path that skips authentication."""

    def __init__(self, app, token):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        supplied = headers.get(AUTH_HEADER_NAME, b"").decode("latin-1")
        tenant_id, _is_admin = opsgate_tenants.resolve_tenant_from_token(supplied)
        if tenant_id is None and not hmac.compare_digest(supplied, self.token):
            response = JSONResponse({"error": f"unauthorized - missing or invalid {AUTH_HEADER_NAME.decode()} header"}, status_code=401)
            await response(scope, receive, send)
            return
        reset_token = _current_tenant_id.set(tenant_id)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_tenant_id.reset(reset_token)


def _load_dotenv_if_present():
    """Minimal .env loader (KEY=VALUE per line, '#' comments and blank lines skipped) - avoids
    adding python-dotenv as a dependency for one file. Looks next to this script
    (mcp-server/.env), not the process's cwd, so it's found regardless of where the server is
    launched from. Never overrides a variable already set in the real environment, so
    `OPSGATE_MCP_TOKEN=x python3 ...` on the command line still wins over the file."""
    env_path = SERVER_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    _load_dotenv_if_present()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--host", default=os.environ.get("OPSGATE_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPSGATE_MCP_PORT", "8765")))
    parser.add_argument("--token", default=os.environ.get("OPSGATE_MCP_TOKEN"), help=f"Shared token required on every request via the {AUTH_HEADER_NAME.decode()} header. Defaults to OPSGATE_MCP_TOKEN, or a freshly generated random token if neither is set.")
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=None,
        help=(
            "Extra Host header value(s) to accept, on top of the mcp SDK's built-in "
            "127.0.0.1/localhost/[::1] defaults - required when this server is reached through a "
            "tunnel/reverse-proxy domain (e.g. a Cloudflare/Tailscale hostname), since the SDK's "
            "DNS-rebinding protection otherwise rejects any other Host header with 421. Repeatable, "
            "or set OPSGATE_MCP_ALLOWED_HOSTS as a comma-separated list."
        ),
    )
    args = parser.parse_args()
    token = args.token or secrets.token_urlsafe(32)
    extra_hosts = list(args.allowed_host or []) + [h.strip() for h in os.environ.get("OPSGATE_MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
    if extra_hosts and mcp.settings.transport_security:
        mcp.settings.transport_security.allowed_hosts.extend(extra_hosts)
        print(f"opsgate MCP server: accepting extra Host header(s): {', '.join(extra_hosts)}", file=sys.stderr)
    print(f"opsgate MCP server: engine tools loaded from {ENGINE_TOOLS_DIR}", file=sys.stderr)
    print(f"opsgate MCP server: resolving profile config from cwd {Path.cwd()}", file=sys.stderr)
    print(f"opsgate MCP server: listening on http://{args.host}:{args.port}/mcp", file=sys.stderr)
    if not args.token:
        print(
            "opsgate MCP server: no --token/OPSGATE_MCP_TOKEN set - generated one for this run.\n"
            f"opsgate MCP server: required header on every request: {AUTH_HEADER_NAME.decode()}: {token}\n"
            "opsgate MCP server: set OPSGATE_MCP_TOKEN to a fixed value to keep this stable across restarts "
            "(e.g. for Replit's Connect via MCP custom-header config).",
            file=sys.stderr,
        )
    app = TokenAuthMiddleware(mcp.streamable_http_app(), token)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
