# METCO Kit v6 Engine Foundation

This package converts the v6 METCO prompt kit into a single canonical kit with generated Claude and Replit distributions.

## What changed

- `canonical/` is the source of truth for instructions, templates, references, specifications, examples, and Claude skill sources.
- `tools/metco_contracts.py` contains machine-readable routing, capability, protected-path, HITL, request, profile, schema, and distribution rules.
- `tools/metco_fixtures.py` contains validation fixtures and gold-standard examples.
- The kit no longer stores METCO-owned contracts, schemas, fixtures, package metadata, or release hashes as standalone `.json` files.
- `tools/` contains the first engine commands for building, validating, and routing requests.
- `fixtures/` contains sample routing and HITL cases used by validation.
- `canonical/examples/gold-standard/` contains sample requests, HITL resume, and parseable final-report examples.
- `dist/claude/` and `dist/replit/` are generated outputs.
- `canonical/references/ai/**` is organized as object-oriented instruction objects with responsibility, activation, inputs, boundaries, workflows, and output evidence.

## Commands

Run from this folder:

```bash
python3 tools/build-distributions.py
python3 tools/validate-kit.py
python3 tools/test-all.py  # runs every command below against every fixture in one pass
python3 tools/route-request.py routing:frontend-task
python3 tools/compile-prompt.py routing:frontend-task
python3 tools/init-state.py routing:migration-task-missing-auth
python3 tools/parse-report.py fixtures/reports/sample-replit-final-report.md
python3 tools/intake-request.py "Audit the Roles module without changing code"
python3 tools/next-phase-prompt.py state:ready-phased-state reports:parsed-sample-report
python3 tools/build-replit-install.py
python3 tools/diff-upgrade.py ../audit_unpack/metco-gpt-project-kit canonical
python3 tools/release-notes.py ../audit_unpack/metco-gpt-project-kit
python3 tools/preflight.py routing:frontend-task
python3 tools/check-paths.py routing:frontend-task
python3 tools/check-capabilities.py routing:migration-task-missing-auth
python3 tools/lint-prompt.py fixtures/prompts/frontend-compiled-with-gate.md
python3 tools/lint-report.py fixtures/reports/sample-replit-final-report.md
python3 tools/audit-engine.py dist/replit-install
python3 tools/init-run.py routing:frontend-task
python3 tools/record-decision.py HITL-example-P1-Q1 "Use the approved feature owner only"
```

## Distribution model

The kit should not be split into separate Claude and Replit source kits.

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

Markdown remains the agent-facing instruction layer. Python contracts are the engine-facing contract. Validators protect the kit from drift. Build tools package the correct files for Claude and Replit.

Object-oriented instruction files make each domain rule set own a clear responsibility without granting authority. Routing, gates, protected paths, schemas, and distribution rules live in Python contracts and root instructions.

The prompt compiler, state initializer, report parser, and upgrade diff command are intentionally simple first versions. They establish the engine contract and should become stricter as more real METCO requests are captured.

## Hard gate enforcement

The engine includes `tools/metco_contracts.py` plus enforcement tools:

- `preflight.py`
- `check-paths.py`
- `check-capabilities.py`
- `lint-prompt.py`
- `lint-report.py`
- `audit-engine.py`

Root `replit.md`, scenario skills, and compiled prompts require the Mandatory HITL Gate before edits, phases, and final reports.

## Replit install output

Run:

```bash
python3 tools/build-replit-install.py
```

Then use `dist/replit-install/` as the clean install folder for Replit. It contains only `replit.md`, `ai/**`, `.agents/skills/**`, and install notes.
