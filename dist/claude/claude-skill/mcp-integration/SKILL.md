---
name: mcp-integration
description: Wire this engine's gate and routing tools into a target project's own MCP server as real callable tools (opsgate_check_capability, opsgate_check_paths, opsgate_preflight, opsgate_record_decision, and optionally opsgate_route_request, opsgate_lint_prompt, opsgate_lint_report - tool_prefix is configurable, see PROFILES/REQUEST_SCHEMA) instead of leaving gate-following to prose instructions alone. Use when a user wants Replit's Agent or any MCP-capable agent to call this engine's gates directly, or asks to add, debug, or verify an MCP server for a project that vendors or submodules this engine.
---

# MCP Integration

Return working code plus a verification result, not just an implementation guide, unless the user asked only for a plan.

## Locate the kit

Confirm this engine is available to the target project - a vendored copy or a git submodule pointing at the canonical kit repo - and find its root path. Read that path from an `OPSGATE_ROOT` environment variable first (legacy name `METCO_KIT_ROOT` also honored, for MCP servers wired before the 6.0.13 generalization rename); fall back to relative-path guesses (`replit-opsgate`, `opsgate-kit`, `metco-kit`, and the same three prefixed with `../` and `../../`) resolved from the process's working directory. Never hardcode an absolute path.

## Build the tools

Add one MCP tool per script the project needs, each shelling out to `python3 <resolved-engine-root>/tools/<script>.py` and returning that script's own JSON output unparsed beyond what the MCP transport requires - do not reimplement any gate logic in the target project's language:

- `opsgate_check_capability`, `opsgate_check_paths`, `opsgate_preflight`, `opsgate_record_decision` (or whatever `tool_prefix` the target project's MCP server actually registered them under) are the minimum set `replit.md`'s MCP-tool-availability section depends on for gate-following.
- `opsgate_route_request`, `opsgate_lint_prompt`, `opsgate_lint_report` are useful additions for a project that also wants routing or prompt/report linting exposed, but are not required just to satisfy the gate.

Degrade gracefully: if the kit or a script can't be found, the MCP server must still start with whatever tools are available - never let optional kit-tool wiring take the whole server down. A dynamic import wrapped in try/catch, checked once at server construction, is enough.

## Mount on the existing server

Mount the tools on the project's existing HTTP server - do not stand up a second server or a second port. Use the MCP SDK's stateless HTTP transport (a fresh server and transport instance per request, no session state held between requests) unless the project has a specific reason to need session continuity.

## Verify before reporting done

1. `initialize` returns the expected `serverInfo.name`.
2. `tools/list` returns every tool that was supposed to be wired - if fewer show up than expected, the kit path isn't resolving; fix that before reporting success.
3. `tools/call` against at least one gate tool (`opsgate_check_paths` is a good smoke test) returns real JSON from the underlying script, not a wrapper error.

## Close the loop

Wiring the server without telling the project's own root instructions about it leaves the tools unused - an agent that never learns the tools exist will keep reasoning through the gate in prose. Update the target project's `replit.md` (or equivalent) MCP-tool-availability section to name the tools that are now actually registered, not just the ones the kit ships by default.

## Scope

Adding a dependency, a new route, and possibly new environment secrets is a package/config/environment change - follow the target project's own root capability gate for that before touching its `package.json`, app entrypoint, or environment/secrets, the same as any other change in that category.
