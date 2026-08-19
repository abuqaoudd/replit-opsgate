# OpsGate

A governance engine for AI coding agents building Replit-hosted projects - Replit doing the implementation, Claude (or any other MCP-capable client) compiling the governed prompts it works from - served through a hosted, multi-tenant MCP server (`mcp-server/`) that exposes gates, routing, and prompt compilation as live tool calls instead of prose an agent reasons through by hand.

## Architecture

- `content/` is the live source of truth for instructions, templates, references, and specifications - read directly by `tools/opsgate_knowledge.py` and the MCP server at call time. There is no build step and no generated copy to keep in sync; editing a file here changes what the next call returns.
- `tools/opsgate_contracts.py` contains every machine-readable contract: routing, capability gates, protected paths, schemas.
- `tools/opsgate_tenants.py` (backed by `tenants/registry.json`, gitignored) is the multi-tenant profile store - each tenant's own frontend/backend roots, protected paths, and auth tokens.
- `tools/opsgate.py` is the CLI entrypoint (`python3 tools/opsgate.py <command> [args...]`); its pure core functions are what `mcp-server/opsgate_mcp_server.py` calls directly, in-process, to serve the same logic as real MCP tool calls.
- `fixtures/` (real files) and `tools/opsgate_fixtures.py` (embedded gold-standard/routing/HITL data, no file on disk) hold the sample requests, routing cases, and HITL/report examples this engine's own test suite exercises - test-only, never served to a tenant or agent.

## Using this engine

Register this server twice, once per role, at two different mount paths on the same running process: Replit's "Connect via MCP" points at `/mcp/replit/` (gate/profile/decision tools for its own implementation work, plus the instruction-sync tools below); Claude (or any client compiling prompts for Replit) points at `/mcp/claude/` (the prompt-compiler chain - intake/route/compile/next-phase/parse/lint/init/export). Five gate/profile/decision tools are shared across both. See `mcp-server/README.md` for running it, exposing it through a tunnel, and the full per-mount tool/resource table. Every gate (`opsgate_preflight`, `opsgate_check_paths`, `opsgate_check_capability`, ...) runs as a real tool call against the caller's own resolved tenant, not manual reasoning.

Two ways to authenticate, both resolving to the same tenant model: a static `X-Opsgate-Token` header (what Replit's "Connect via MCP" and any client that supports custom headers use), or OAuth 2.1 + PKCE (`mcp-server/opsgate_oauth.py`) for a client whose connector flow is OAuth-only with no header field at all - Claude's own org-level Connectors feature is exactly this case. A successful OAuth exchange just hands back an existing tenant token as the `access_token`, so which path a caller used never changes how it resolves. See `mcp-server/README.md`'s "OAuth" section for setup.

Install (or refresh) a target Replit project's own `replit.md`/`ai/**`/`.agents/skills/**`: have Replit call `opsgate_sync_instructions` for a manifest of every file, then `opsgate_sync_file(path)` once per entry, writing each to its given path - this works identically for a brand-new project (nothing installed yet) and a stale existing one. A first-ever install still needs one manual step first, since the *currently* installed `replit.md` has to already contain the instruction to call these tools - either paste `content/references/replit.md`/`ai/**`/`replit-skills/**` in by hand once, or just tell Replit directly to call `opsgate_sync_instructions` and write what it returns. The MCP server also provides supplementary knowledge resources (HITL protocol, security rules, skill workflows, instruction objects, and - Claude-only - the Claude MCP workflow describing how to call this server's own tool chain, see `mcp-server/README.md`'s "Resources exposed"), but `replit.md` remains the primary root instruction file a Replit Agent reads first.

Onboard a new tenant (a new project or team) with `tools/opsgate_tenants.py`:

```python
import opsgate_tenants as tenants

tenants.create_profile("acme", frontend_root="client/src", backend_root="server/src")
token = tenants.issue_token("acme")  # returned once, in plaintext - deliver it to the tenant
```

That token, set as the `X-Opsgate-Token` header, is all a tenant needs to connect - no local file, no rebuild, no copy step beyond the one-time `replit.md`/`ai/**` install above. Once the tenant's Replit project genuinely has this server's MCP tools registered (not just a token issued), set `tenants.update_profile("acme", mcp_enabled=True)` - `opsgate_compile_prompt` then defaults every compiled prompt for that tenant to the "call these tools directly" HITL gate instead of the manual prose reasoning table, with no per-request flag needed. See `content/ADOPTION_GUIDE.md` for the full tenant-onboarding walkthrough.

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
