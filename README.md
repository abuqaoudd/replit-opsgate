# Replit OpsGate v6 Engine Foundation

This package is a governance engine for AI coding agents working on Replit projects: a canonical prompt/skill engine with generated Claude and Replit distributions, plus a real MCP server (`mcp-server/`) that exposes the same gates as live tool calls instead of prose an agent reasons through by hand.

## Two ways to use this engine

Both modes enforce the exact same rules from `tools/opsgate_contracts.py` - which one you pick changes how a gate result is obtained, never what it requires.

- **Static mode (zero infrastructure).** Drop `dist/replit-install/`'s `replit.md`, `ai/**`, and `.agents/skills/**` into a target project. The agent reads these files and reasons through the Mandatory HITL Gate in prose - no server, no network, no token to manage. The only option for a project that can't or doesn't want to run anything.
- **MCP mode (live tool calls).** Run `mcp-server/opsgate_mcp_server.py` and register it with an MCP-capable client (Replit's Connect via MCP, Claude, etc.) - see `mcp-server/README.md`. The same gates run as real tool calls (`opsgate_preflight`, `opsgate_check_paths`, ...) instead of manual reasoning. More reliable, but needs a running server, a public tunnel, and an auth token to manage.

## What changed

- `canonical/` is the source of truth for instructions, templates, references, specifications, examples, and Claude skill sources.
- `tools/opsgate_contracts.py` contains machine-readable routing, capability, protected-path, HITL, request, profile, schema, and distribution rules.
- `tools/opsgate_fixtures.py` contains validation fixtures and gold-standard examples.
- The engine no longer stores its own contracts, schemas, fixtures, package metadata, or release hashes as standalone `.json` files.
- `tools/` contains the first engine commands for building, validating, and routing requests.
- `fixtures/` contains sample routing and HITL cases used by validation.
- `canonical/examples/gold-standard/` contains sample requests, HITL resume, and parseable final-report examples.
- `dist/claude/` and `dist/replit/` are generated outputs.
- `canonical/references/ai/**` is organized as object-oriented instruction objects with responsibility, activation, inputs, boundaries, workflows, and output evidence.

## Commands

Run from this folder:

Every command below except `init-profile.py` and `apply-setup.py` (real standalone scripts) runs through the one CLI entrypoint, `tools/opsgate_tools.py <command> [args...]` - there is no separate file per command.

```bash
python3 tools/opsgate_tools.py build-distributions
python3 tools/opsgate_tools.py validate-engine
python3 tools/opsgate_tools.py test-all  # runs every command below against every fixture in one pass
python3 tools/opsgate_tools.py route-request routing:frontend-task
python3 tools/opsgate_tools.py compile-prompt routing:frontend-task
python3 tools/opsgate_tools.py init-state routing:migration-task-missing-auth
python3 tools/opsgate_tools.py parse-report fixtures/reports/sample-replit-final-report.md
python3 tools/opsgate_tools.py intake-request "Audit the Roles module without changing code"
python3 tools/opsgate_tools.py next-phase-prompt state:ready-phased-state reports:parsed-sample-report
python3 tools/opsgate_tools.py build-replit-install
python3 tools/opsgate_tools.py diff-upgrade ../audit_unpack/old-engine-root canonical
python3 tools/opsgate_tools.py release-notes ../audit_unpack/old-engine-root
python3 tools/opsgate_tools.py preflight routing:frontend-task
python3 tools/opsgate_tools.py check-paths routing:frontend-task
python3 tools/opsgate_tools.py show-profile  # resolved active profile, roots, and protected paths - no request file required
python3 tools/init-profile.py --profile acme --target-root ../my-project --frontend-root client/src --backend-root server/src  # scaffold a new project profile + starter business file, written OUTSIDE this engine
python3 tools/apply-setup.py --template PROJECT_SETUP.md --target-root .  # the primary onboarding path: materializes replit.md/ai/**/opsgate.profile.json from a filled-in plain-language template
python3 tools/opsgate_tools.py check-capabilities routing:migration-task-missing-auth
python3 tools/opsgate_tools.py lint-prompt fixtures/prompts/frontend-compiled-with-gate.md
python3 tools/opsgate_tools.py lint-report fixtures/reports/sample-replit-final-report.md
python3 tools/opsgate_tools.py audit-engine dist/replit-install
python3 tools/opsgate_tools.py init-run routing:frontend-task
python3 tools/opsgate_tools.py record-decision HITL-example-P1-Q1 "Use the approved feature owner only"
python3 tools/opsgate_tools.py validate-json manifests/request.schema.json fixtures/routing/frontend-task.json
```

## Distribution model

The engine should not be split into separate Claude and Replit sources.

Maintain one canonical source:

```text
canonical/
  CLAUDE_PROJECT_INSTRUCTIONS.md
  templates/
  references/
  specifications/
  examples/
  claude-skills/
```

Generate two outputs:

```text
dist/claude/
dist/replit/
```

## Engine direction

Markdown remains the agent-facing instruction layer. Python contracts are the engine-facing contract. Validators protect the engine from drift. Build tools package the correct files for Claude and Replit.

Object-oriented instruction files make each domain rule set own a clear responsibility without granting authority. Routing, gates, protected paths, schemas, and distribution rules live in Python contracts and root instructions.

The prompt compiler, state initializer, report parser, and upgrade diff command are intentionally simple first versions. They establish the engine contract and should become stricter as more real requests are captured.

## Hard gate enforcement

The engine includes `tools/opsgate_contracts.py` plus enforcement commands (all run via `python3 tools/opsgate_tools.py <command>`):

- `preflight`
- `check-paths`
- `check-capabilities`
- `lint-prompt`
- `lint-report`
- `audit-engine`

Root `replit.md`, scenario skills, and compiled prompts require the Mandatory HITL Gate before edits, phases, and final reports.

The same enforcement tools above are also reachable as live MCP tools via `mcp-server/opsgate_mcp_server.py` (`opsgate_preflight`, `opsgate_check_paths`, `opsgate_check_capability`, `opsgate_lint_prompt`, `opsgate_lint_report`, ...) - see "Two ways to use this engine" above and `mcp-server/README.md`. Either invocation path runs identical rules.

## Replit install output

Run:

```bash
python3 tools/opsgate_tools.py build-replit-install
```

Then use `dist/replit-install/` as the clean install folder for Replit. It contains only `replit.md`, `ai/**`, `.agents/skills/**`, and install notes.
