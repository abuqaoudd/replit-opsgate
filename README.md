# OpsGate

A governance engine for AI coding agents working on Replit projects: prompt/skill content with object-oriented instruction contracts, served through a hosted, multi-tenant MCP server (`mcp-server/`) that exposes gates and routing as live tool calls instead of prose an agent reasons through by hand.

## Architecture

- `content/` is the live source of truth for instructions, templates, references, and specifications - read directly by `tools/opsgate_knowledge.py` and the MCP server at call time. There is no build step and no generated copy to keep in sync; editing a file here changes what the next call returns.
- `tools/opsgate_contracts.py` contains every machine-readable contract: routing, capability gates, protected paths, schemas.
- `tools/opsgate_tenants.py` (backed by `tenants/registry.json`, gitignored) is the multi-tenant profile store - each tenant's own frontend/backend roots, protected paths, and auth tokens.
- `tools/opsgate.py` is the CLI entrypoint (`python3 tools/opsgate.py <command> [args...]`); its pure core functions are what `mcp-server/opsgate_mcp_server.py` calls directly, in-process, to serve the same logic as real MCP tool calls.
- `fixtures/` (real files) and `tools/opsgate_fixtures.py` (embedded gold-standard/routing/HITL data, no file on disk) hold the sample requests, routing cases, and HITL/report examples this engine's own test suite exercises - test-only, never served to a tenant or agent.

## Using this engine

Register `mcp-server/opsgate_mcp_server.py` with an MCP-capable client (Replit's Connect via MCP, Claude, etc.) - see `mcp-server/README.md` for running it, exposing it through a tunnel, and its full tool/resource table. Every gate (`opsgate_preflight`, `opsgate_check_paths`, `opsgate_check_capability`, ...) runs as a real tool call against the caller's own resolved tenant, not manual reasoning.

Copy `content/references/replit.md`, `content/references/ai/**`, and `content/references/replit-skills/**` into a target Replit project's root once, as `replit.md`, `ai/**`, and `.agents/skills/**` respectively - this is the one per-project step; the MCP server provides the gates and supplementary knowledge resources (HITL protocol, security rules, skill workflows, instruction objects - see `mcp-server/README.md`'s "Resources exposed"), but `replit.md` remains the primary root instruction file a Replit Agent reads first.

Onboard a new tenant (a new project or team) with `tools/opsgate_tenants.py`:

```python
import opsgate_tenants as tenants

tenants.create_profile("acme", frontend_root="client/src", backend_root="server/src")
token = tenants.issue_token("acme")  # returned once, in plaintext - deliver it to the tenant
```

That token, set as the `X-Opsgate-Token` header, is all a tenant needs to connect - no local file, no rebuild, no copy step beyond the one-time `replit.md`/`ai/**` install above.

## Commands

Run from this folder, via the one CLI entrypoint:

```bash
python3 tools/opsgate.py validate-engine
python3 tools/opsgate.py test-all  # runs every command below against every fixture in one pass
python3 tools/opsgate.py route-request routing:frontend-task
python3 tools/opsgate.py compile-prompt routing:frontend-task
python3 tools/opsgate.py init-state routing:migration-task-missing-auth
python3 tools/opsgate.py parse-report fixtures/reports/sample-replit-final-report.md
python3 tools/opsgate.py intake-request "Audit the Roles module without changing code"
python3 tools/opsgate.py next-phase-prompt state:ready-phased-state reports:parsed-sample-report
python3 tools/opsgate.py preflight routing:frontend-task
python3 tools/opsgate.py check-paths routing:frontend-task
python3 tools/opsgate.py show-profile --tenant acme  # resolved tenant, roots, and protected paths - defaults to local-dev with no --tenant
python3 tools/opsgate.py check-capabilities routing:migration-task-missing-auth
python3 tools/opsgate.py lint-prompt fixtures/prompts/frontend-compiled-with-gate.md
python3 tools/opsgate.py lint-report fixtures/reports/sample-replit-final-report.md
python3 tools/opsgate.py init-run routing:frontend-task
python3 tools/opsgate.py record-decision HITL-example-P1-Q1 "Use the approved feature owner only"
python3 tools/opsgate.py validate-json manifests/request.schema.json fixtures/routing/frontend-task.json
```

## Engine direction

Markdown remains the agent-facing instruction layer; Python contracts are the engine-facing contract. Object-oriented instruction files make each domain rule set own a clear responsibility without granting authority - routing, gates, protected paths, and schemas live in Python contracts and root instructions, not duplicated in Markdown.

The prompt compiler, state initializer, and report parser are intentionally simple first versions. They establish the engine contract and should become stricter as more real requests are captured.

## Hard gate enforcement

`tools/opsgate_contracts.py` plus these enforcement commands (all run via `python3 tools/opsgate.py <command>`, and all reachable as live MCP tools with matching `opsgate_` names via `mcp-server/opsgate_mcp_server.py`):

- `preflight`
- `check-paths`
- `check-capabilities`
- `lint-prompt`
- `lint-report`

`replit.md`, scenario skills, and compiled prompts require the Mandatory HITL Gate before edits, phases, and final reports - see `content/specifications/HITL_SPEC.md` for the full three-case protocol.
