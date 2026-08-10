---
name: metco-mcp-integration
description: Wire metco-kit's gate and routing tools into a target project's own MCP server as real callable tools (metco_check_capability, metco_check_paths, metco_preflight, metco_record_decision, and optionally metco_route_request, metco_lint_prompt, metco_lint_report) instead of leaving gate-following to prose instructions alone. Use when a user wants Replit's Agent or any MCP-capable agent to call metco-kit's gates directly, or asks to add, debug, or verify an MCP server for a project that vendors or submodules metco-kit.
---

# METCO MCP Integration

Return working code plus a verification result, not just an implementation guide, unless the user asked only for a plan.

## Locate the kit

Confirm metco-kit is available to the target project - a vendored copy or a git submodule pointing at the canonical kit repo - and find its root path. Read that path from a `METCO_KIT_ROOT` environment variable first; fall back to relative-path guesses (`metco-kit`, `../metco-kit`, `../../metco-kit`) resolved from the process's working directory. Never hardcode an absolute path.

## Build the tools

Add one MCP tool per script the project needs, each shelling out to `python3 <METCO_KIT_ROOT>/tools/<script>.py` and returning that script's own JSON output unparsed beyond what the MCP transport requires - do not reimplement any gate logic in the target project's language:

- `metco_check_capability`, `metco_check_paths`, `metco_preflight`, `metco_record_decision` are the minimum set `replit.md`'s MCP-tool-availability section depends on for gate-following.
- `metco_route_request`, `metco_lint_prompt`, `metco_lint_report` are useful additions for a project that also wants routing or prompt/report linting exposed, but are not required just to satisfy the gate.

Degrade gracefully: if the kit or a script can't be found, the MCP server must still start with whatever tools are available - never let optional kit-tool wiring take the whole server down. A dynamic import wrapped in try/catch, checked once at server construction, is enough.

## Mount on the existing server

Mount the tools on the project's existing HTTP server - do not stand up a second server or a second port. Use the MCP SDK's stateless HTTP transport (a fresh server and transport instance per request, no session state held between requests) unless the project has a specific reason to need session continuity.

## Verify before reporting done

1. `initialize` returns the expected `serverInfo.name`.
2. `tools/list` returns every tool that was supposed to be wired - if fewer show up than expected, the kit path isn't resolving; fix that before reporting success.
3. `tools/call` against at least one gate tool (`metco_check_paths` is a good smoke test) returns real JSON from the underlying script, not a wrapper error.

## Close the loop

Wiring the server without telling the project's own root instructions about it leaves the tools unused - an agent that never learns the tools exist will keep reasoning through the gate in prose. Update the target project's `replit.md` (or equivalent) MCP-tool-availability section to name the tools that are now actually registered, not just the ones the kit ships by default.

## Scope

Adding a dependency, a new route, and possibly new environment secrets is a package/config/environment change - follow the target project's own root capability gate for that before touching its `package.json`, app entrypoint, or environment/secrets, the same as any other change in that category.
