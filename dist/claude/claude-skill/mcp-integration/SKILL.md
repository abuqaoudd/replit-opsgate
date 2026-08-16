---
name: mcp-integration
description: Set up, troubleshoot, or extend this engine's MCP server (mcp-server/opsgate_mcp_server.py) so Replit's Agent, Claude, or any MCP-capable client can call this engine's gates directly (opsgate_check_capability, opsgate_check_paths, opsgate_preflight, opsgate_record_decision, opsgate_route_request, and more - 14 tools total, tool_prefix configurable) instead of following gates in prose. Use when a user wants to connect an MCP client to this engine, needs help exposing the server through a tunnel, hits a connection/auth error, or wants a different integration shape than the reference server provides.
---

# MCP Integration

Return working code plus a verification result, not just an implementation guide, unless the user asked only for a plan.

## Use the existing reference server first

`mcp-server/opsgate_mcp_server.py` is a working, verified HTTP MCP server for this engine - it wires up 14 tools (`opsgate_route_request`, `opsgate_check_capability`, `opsgate_check_paths`, `opsgate_preflight`, `opsgate_show_profile`, `opsgate_init_state`, `opsgate_init_run`, `opsgate_compile_prompt`, `opsgate_next_phase_prompt`, `opsgate_intake_request`, `opsgate_parse_report`, `opsgate_lint_report`, `opsgate_lint_prompt`, `opsgate_record_decision`) directly against `tools/opsgate.py`'s own functions - no subprocess shelling, no reimplemented gate logic. It already has token-based auth and DNS-rebinding-safe Host header handling. Do not rebuild this from scratch. See `mcp-server/README.md` for the full reference; help the user with:

- **Running it locally**: `pip install -r mcp-server/requirements.txt` (needs Python 3.10+), then `python3 mcp-server/opsgate_mcp_server.py`. It reads a token from `mcp-server/.env`/`OPSGATE_MCP_TOKEN`, or generates and prints one at startup if neither is set.
- **Exposing it publicly**: it only binds locally by default - reaching it from Replit, Claude, or any remote MCP client needs a tunnel (Cloudflare Tunnel, ngrok, Tailscale Funnel) pointed at its port. Add the tunnel's hostname to `OPSGATE_MCP_ALLOWED_HOSTS` - the underlying `mcp` SDK's DNS-rebinding protection otherwise rejects any Host header but `localhost`/`127.0.0.1` with a `421`, regardless of tunnel provider.
- **Registering it with a client**: send the public URL plus a custom header, `X-Opsgate-Token: <token>` - not the standard `Authorization` header. Some free, account-less tunnel providers (Cloudflare's quick tunnels) reject requests carrying `Authorization` at their edge, so a custom header name avoids that entirely.
- **Debugging a broken connection**: verify with the official `mcp` Python SDK's `streamablehttp_client` or MCP Inspector before assuming the client integration is wrong - most failures are a token/header mismatch or a missing `OPSGATE_MCP_ALLOWED_HOSTS` entry, not a protocol bug.

## When a different architecture is actually needed

Some projects can't run a second standalone process (e.g. a deployment that only exposes one port). Only in that case, mount this engine's tools onto the project's own existing HTTP server instead of running `opsgate_mcp_server.py` as shipped:

- Confirm this engine is available to the target project (a vendored copy or git submodule) and find its root. Read an `OPSGATE_ROOT` environment variable first (legacy name `METCO_KIT_ROOT` also honored, from before the 6.0.13 generalization rename); fall back to relative-path guesses (`replit-opsgate`, `opsgate-engine`, and the same prefixed with `../` and `../../`) resolved from the process's working directory. Never hardcode an absolute path.
- Import `tools/opsgate.py`'s functions directly and call them in-process - the same pattern `opsgate_mcp_server.py` itself uses - rather than shelling out to a subprocess per call.
- Still enforce a shared-secret header check in front of these tools if the host server is reachable publicly. Do not skip auth just because the tools are mounted differently.
- Degrade gracefully: if the engine or a function can't be found, the host server must still start with whatever tools are available - never let optional engine-tool wiring take the whole server down.

## Verify before reporting done

1. `initialize` returns the expected `serverInfo.name`.
2. `tools/list` returns every tool that was supposed to be wired - if fewer show up than expected, the engine path isn't resolving; fix that before reporting success.
3. `tools/call` against at least one gate tool (`opsgate_check_paths` is a good smoke test) returns real JSON from the underlying script, not a wrapper error.
4. If a token/header is required, confirm a request with no or wrong credential is actually rejected (401) - auth that hasn't been verified isn't auth.

## Close the loop

Wiring the server without telling the project's own root instructions about it leaves the tools unused - an agent that never learns the tools exist will keep reasoning through the gate in prose. Update the target project's `replit.md` (or equivalent) Section 10 to name the tools that are now actually registered, not just the ones the engine ships by default.

## Scope

Adding a dependency, a new route, and possibly new environment secrets is a package/config/environment change - follow the target project's own root capability gate for that before touching its `package.json`, app entrypoint, or environment/secrets, the same as any other change in that category.
