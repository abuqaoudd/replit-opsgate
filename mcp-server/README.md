# opsgate MCP server

Exposes this engine's own gate/routing/lint tools (`tools/opsgate.py`) as an
HTTP-based MCP server, so a remote agent (e.g. Replit's Connect via MCP) can call
them directly instead of an agent inside this repo shelling out to the CLI.

This is an adapter, not a reimplementation - every tool here calls the exact same
`cmd_*` function the CLI calls (`python3 tools/opsgate.py check-paths`,
`... preflight`, etc.), and returns exactly what that function would print. If
`opsgate.py` changes, this file does not need to.

## Where this lives

`<engine-dir>/mcp-server/opsgate_mcp_server.py`, as a sibling of `tools/` and
`canonical/`. It imports `opsgate.py` directly from the real `tools/`
directory next to it, so paths and profile resolution behave exactly as they do
for the CLI.

## Install

Requires **Python 3.10+** (the `mcp` package's own minimum - check with `python3 --version`
first; on a machine whose default `python3` is older, install a newer interpreter and use
that instead, e.g. via a dedicated venv).

```
pip install -r mcp-server/requirements.txt
```

`requirements.txt` pins `mcp>=1.27.0,<2.0.0` - `mcp` 2.0.0 restructured its module layout
(`mcp.server.fastmcp.FastMCP`, which this file imports, no longer exists there), so an
unpinned `pip install mcp` would install a version this file cannot run against.

## Run

From the outer project's root (the project that vendors this engine as a
submodule) - this matters for external profile config resolution, see below:

```
python3 <engine-dir>/mcp-server/opsgate_mcp_server.py --host 127.0.0.1 --port 8765
```

Flags default to `OPSGATE_MCP_HOST` / `OPSGATE_MCP_PORT` env vars, then
`127.0.0.1:8765`. The server listens for MCP's "streamable-http" transport at
`http://<host>:<port>/mcp`.

This only starts the server locally - it is not reachable from Replit's cloud
Agent until it's exposed through a tunnel (ngrok, Cloudflare Tunnel, Tailscale
Funnel, etc.) and that tunnel's public HTTPS URL is registered in Replit's
"Connect via MCP" settings. That's a separate step from just running this file.

## Authentication

Every request must carry an `X-Opsgate-Token: <token>` header, checked by a
small ASGI middleware in front of the MCP app - there is no unauthenticated
path, regardless of `--host`. This matters because the server has real side
effects (`opsgate_init_run` writes to disk, `opsgate_record_decision` appends
to a log) and is designed to end up reachable through a public tunnel.

It's a custom header, not the standard `Authorization` header, because
Cloudflare's free, account-less "quick tunnels" (`cloudflared tunnel --url
...`, no login required) reject any request carrying an `Authorization`
header at the edge with `421 Invalid Host header` - confirmed empirically,
never even reaching this server. A custom header carries the same secret with
the same protection and passes through untouched.

Set a stable token with `--token` or `OPSGATE_MCP_TOKEN` (recommended, so it
survives restarts and you can put the same value into Replit's "Connect via
MCP" custom-header config). If neither is set, the server generates a random
token at startup and prints it once to stderr - fine for a quick local test,
but it changes every restart, so a saved MCP client config would need updating
each time.

A request without a valid token gets `401 {"error": "unauthorized - missing or invalid x-opsgate-token header"}`.

## Which project's profile it answers for

- The **built-in profiles** (`generic-replit`, and any others baked into
  `opsgate_contracts.py`) are selected per-call the same way the CLI selects
  them: the request's own `"profile"` field, or the `OPSGATE_PROFILE`
  environment variable set before the server starts.
- The **external `opsgate.profile.json` override file** (see
  `canonical/ENGINE_ADOPTION_GUIDE.md`) is found by walking up from this *process's own
  current working directory* - so start the server from the target project's
  root, or set `OPSGATE_PROFILE_CONFIG` explicitly to that file's path, before
  launching. `opsgate_show_profile` reports which one - if any - was found.

A single running server answers for one project's external profile config at a
time. Running it against a different project means restarting it from that
project's root (or with a different `OPSGATE_PROFILE_CONFIG`).

## Tools exposed

Names match the convention `replit.md` Section 10 ("MCP tool availability")
already documents - `opsgate_` prefix. All 14 runtime tools:

| Tool | Wraps | Input | Output |
|---|---|---|---|
| `opsgate_route_request` | `cmd_route_request` | `request` (object) | JSON |
| `opsgate_check_capability` | `cmd_check_capabilities` | `request` (object) | JSON |
| `opsgate_check_paths` | `cmd_check_paths` | `request` (object) | JSON |
| `opsgate_preflight` | `cmd_preflight` | `request` (object) | JSON |
| `opsgate_show_profile` | `cmd_show_profile` | `request` (object, optional) | JSON |
| `opsgate_init_state` | `cmd_init_state` | `request` (object) | JSON |
| `opsgate_init_run` | `cmd_init_run` | `request` (object) | JSON - **writes `runs/<id>/` to disk on this server's machine** |
| `opsgate_compile_prompt` | `cmd_compile_prompt` | `request` (object) | prose text |
| `opsgate_next_phase_prompt` | `cmd_next_phase_prompt` | `run_state` + `parsed_report` (objects) | prose text |
| `opsgate_intake_request` | `cmd_intake_request` | `text` (plain sentence) | JSON |
| `opsgate_parse_report` | `cmd_parse_report` | `report_markdown` (text) | JSON |
| `opsgate_lint_report` | `cmd_lint_report` | `report_markdown` (text) | JSON |
| `opsgate_lint_prompt` | `cmd_lint_prompt` | `prompt_markdown` (text) | JSON |
| `opsgate_record_decision` | `cmd_record_decision` | `hitl_id` + `answer` (strings) | JSON - **appends to `runs/decisions.pylog` on this server's machine** |

Deliberately **not** exposed: `build-distributions`, `build-replit-install`,
`audit-engine`, `diff-upgrade`, `release-notes`, `validate-json`, `validate-engine`,
`test-all` - engine-authoring operations run by hand inside this repo, not
gate/routing calls a live Replit task needs. `init-profile`/`apply-setup` (the
onboarding tools) are also not exposed - those are meant to be run once, by the
Agent, via shell during setup, not called mid-task.

A deterministic gate tool failing (`can_proceed: false` / `pass: false`) is a
normal, valid result - not a protocol-level error. The caller (the Agent
following `replit.md`) is expected to read that field and report the gate as
blocked, exactly as it would from the CLI's exit code.

## Verified

Tested end-to-end against a real request/report round-trip (route → preflight →
check_paths violation case → compile_prompt → intake_request → record_decision →
lint_report → parse_report → init_state → init_run) via the official `mcp` Python
SDK's streamable-HTTP client - every tool's output matched what the equivalent
CLI command (`python3 tools/<name>.py ...`) produces, and `init_run` /
`record_decision`'s disk side effects (`runs/<id>/`, `runs/decisions.pylog`) were
confirmed to land in the right place.
