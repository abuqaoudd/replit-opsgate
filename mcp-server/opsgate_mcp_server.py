#!/usr/bin/env python3
"""HTTP MCP server exposing this engine's own gate/routing tools remotely.

What this is: a thin adapter, not a reimplementation. Every tool below shells
out to the exact same `cmd_*` function `tools/opsgate_tools.py`'s own CLI
entrypoints call - it writes the caller's input to a temp file, invokes the
real command, captures whatever it printed, and hands that straight back.
Nothing about routing, gates, protected paths, or profile resolution is
duplicated or reimplemented here; if `opsgate_tools.py` changes, this file
does not need to.

Tool names match the convention `replit.md` Section 10 already documents
("MCP tool availability") - `opsgate_` prefix, e.g. `opsgate_check_capability`,
`opsgate_check_paths`, `opsgate_preflight`, `opsgate_record_decision`, plus the
routing/lint tools it mentions in passing. A Replit Agent that already reads
that section needs no new instructions to use this server once it is
registered - the tool names it was told to expect are the tool names here.

Where this lives: `<engine-dir>/mcp-server/opsgate_mcp_server.py`, a sibling
of `tools/`. It imports `opsgate_tools.py` directly from the real `tools/`
directory next to it, so `ROOT_DIR` inside that module resolves exactly the
way it does for the CLI - this server does not run against a copy.

Which project this server answers for: whichever profile the caller's own
request JSON specifies (`"profile": "..."`), or - for the external
`opsgate.profile.json` override file itself, not the built-in profiles - the
one found by `OPSGATE_PROFILE_CONFIG`/directory walk from this process's
current working directory. Start this server from the target project's own
root (the outer project that vendors this engine as a submodule), or set
`OPSGATE_PROFILE_CONFIG` explicitly, so that resolution finds the right file.
See `canonical/ENGINE_ADOPTION_GUIDE.md` for what that file is and why it exists.

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
import contextlib
import hmac
import io
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
ENGINE_TOOLS_DIR = SERVER_DIR.parent / "tools"
if not (ENGINE_TOOLS_DIR / "opsgate_tools.py").exists():
    sys.exit(
        f"Expected to find opsgate_tools.py in {ENGINE_TOOLS_DIR}, but it is not there.\n"
        "This server must live in a 'mcp-server/' folder that sits next to this engine's "
        "own 'tools/' folder (i.e. <engine-dir>/mcp-server/opsgate_mcp_server.py) - move it "
        "there and re-run."
    )
sys.path.insert(0, str(ENGINE_TOOLS_DIR))

import opsgate_tools  # noqa: E402  (import must follow the sys.path fix-up above)

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
# Adapter plumbing - every function below wraps an existing cmd_* function
# from opsgate_tools.py exactly as the CLI calls it: write input to a temp
# file, invoke the real function with that path in argv, capture whatever it
# printed to stdout, and return that. A cmd_* function that fails a gate
# calls `raise SystemExit(1)` *after* printing its JSON result - that JSON
# (e.g. `"can_proceed": false`) is the actual answer the caller wants, not an
# error, so this always captures stdout regardless of exit code and never
# raises to the MCP layer for a normal gate failure.
# ---------------------------------------------------------------------------


def _capture_stdout(cmd_func, argv):
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            cmd_func(argv)
    except SystemExit:
        pass  # Expected control flow for a failed gate - the JSON was already printed above.
    return buffer.getvalue().strip()


def _write_temp(text, suffix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="opsgate-mcp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
    except Exception:
        os.remove(path)
        raise
    return path


def _run_json_in_json_out(cmd_func, request):
    path = _write_temp(json.dumps(request or {}), ".json")
    try:
        raw = _capture_stdout(cmd_func, [path])
    finally:
        os.remove(path)
    return _parse_json_or_wrap(raw)


def _run_json_in_text_out(cmd_func, request):
    path = _write_temp(json.dumps(request or {}), ".json")
    try:
        return _capture_stdout(cmd_func, [path])
    finally:
        os.remove(path)


def _run_text_in_json_out(cmd_func, text, suffix=".md"):
    path = _write_temp(text or "", suffix)
    try:
        raw = _capture_stdout(cmd_func, [path])
    finally:
        os.remove(path)
    return _parse_json_or_wrap(raw)


def _parse_json_or_wrap(raw):
    if not raw:
        return {"error": "the underlying command produced no output"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "the underlying command did not produce valid JSON", "raw_output": raw}


# ---------------------------------------------------------------------------
# Tools - one per runtime cmd_* function in opsgate_tools.py. Maintenance-only
# commands (build-distributions, build-replit-install, audit-engine,
# diff-upgrade, release-notes, validate-json, validate-engine, test-all) are
# deliberately not exposed here - those are engine-authoring operations run
# by hand inside this repo, not gate/routing calls a live Replit task needs.
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
    return _run_json_in_json_out(opsgate_tools.cmd_route_request, request)


@mcp.tool(
    name="opsgate_check_capability",
    description=(
        "Deterministic capability_gate check: does this request's own authorizations cover "
        "every capability its route requires? `can_proceed: false` means an authorization is "
        "missing - report it as a blocked gate, never as a HITL decision."
    ),
)
def opsgate_check_capability(request: dict) -> dict:
    return _run_json_in_json_out(opsgate_tools.cmd_check_capabilities, request)


@mcp.tool(
    name="opsgate_check_paths",
    description=(
        "Deterministic protected_path_gate check: do this request's write/read scope paths "
        "touch any path the active profile protects? `can_proceed: false` names the exact "
        "violation(s) - report as blocked, never as a HITL decision."
    ),
)
def opsgate_check_paths(request: dict) -> dict:
    return _run_json_in_json_out(opsgate_tools.cmd_check_paths, request)


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
    return _run_json_in_json_out(opsgate_tools.cmd_preflight, request)


@mcp.tool(
    name="opsgate_show_profile",
    description=(
        "Show which profile is currently active (env var, request field, or default), its "
        "resolved frontend/backend roots, and its protected paths - with no request required. "
        "Pass an empty object, or a request with a \"profile\" field to check a specific one."
    ),
)
def opsgate_show_profile(request: dict | None = None) -> dict:
    return _run_json_in_json_out(opsgate_tools.cmd_show_profile, request or {})


@mcp.tool(
    name="opsgate_init_state",
    description=(
        "Build the initial run-state object (status, phases if execution is phased, empty "
        "decisions/checks lists) for a request, based on its resolved route. Read-only - does "
        "not write anything to disk (use opsgate_init_run for that)."
    ),
)
def opsgate_init_state(request: dict) -> dict:
    return _run_json_in_json_out(opsgate_tools.cmd_init_state, request)


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
    return _run_json_in_json_out(opsgate_tools.cmd_init_run, request)


@mcp.tool(
    name="opsgate_compile_prompt",
    description=(
        "Compile a full Replit prompt or artifact-authoring prompt (scope, HITL gate, "
        "execution shape, final-report structure, etc.) from a request. Returns prose text, "
        "not JSON - this is the actual prompt to hand to the implementing agent/session."
    ),
)
def opsgate_compile_prompt(request: dict) -> str:
    return _run_json_in_text_out(opsgate_tools.cmd_compile_prompt, request)


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
    state_path = _write_temp(json.dumps(run_state or {}), ".json")
    report_path = _write_temp(json.dumps(parsed_report or {}), ".json")
    try:
        return _capture_stdout(opsgate_tools.cmd_next_phase_prompt, [state_path, report_path])
    finally:
        os.remove(state_path)
        os.remove(report_path)


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
    raw = _capture_stdout(opsgate_tools.cmd_intake_request, [text or ""])
    return _parse_json_or_wrap(raw)


@mcp.tool(
    name="opsgate_parse_report",
    description=(
        "Parse a final-report markdown document into structured fields: outcome, acceptance "
        "status, files changed, PASSED/FAILED/NOT RUN checks, HITL decision references, "
        "blockers, and residual risk. Feed its output into opsgate_next_phase_prompt."
    ),
)
def opsgate_parse_report(report_markdown: str) -> dict:
    return _run_text_in_json_out(opsgate_tools.cmd_parse_report, report_markdown, ".md")


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
    return _run_text_in_json_out(opsgate_tools.cmd_lint_report, report_markdown, ".md")


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
    return _run_text_in_json_out(opsgate_tools.cmd_lint_prompt, prompt_markdown, ".md")


@mcp.tool(
    name="opsgate_record_decision",
    description=(
        "Persist a human's answer to a HITL decision (by its HITL-ID) to this server's own "
        "runs/decisions.pylog, so the decision survives outside the current conversation. "
        "Call this immediately after a human answers a HITL question, before resuming work."
    ),
)
def opsgate_record_decision(hitl_id: str, answer: str) -> dict:
    raw = _capture_stdout(opsgate_tools.cmd_record_decision, [hitl_id, answer])
    return _parse_json_or_wrap(raw)


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
    def __init__(self, app, token):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        supplied = headers.get(AUTH_HEADER_NAME, b"").decode("latin-1")
        if not hmac.compare_digest(supplied, self.token):
            response = JSONResponse({"error": f"unauthorized - missing or invalid {AUTH_HEADER_NAME.decode()} header"}, status_code=401)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


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
