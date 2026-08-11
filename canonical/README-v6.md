# Replit OpsGate Claude Project Prompt Kit

This kit turns project requests into detailed business files, implementation specifications, audits, task backlogs, controlled change records, and governed Replit Agent prompts. Version 6 preserves automatic internal process-mode routing and the strict three-case HITL pause/resume flow, and adds first-class module business-file audit updates plus delta spec generation from business MD versus existing spec files.

## Contents

- `CLAUDE_PROJECT_INSTRUCTIONS.md`: Claude project instructions.
- `templates/`: business, specification, audit, backlog, change/improvement, bounded Replit, phased Replit, three-case HITL decision, and intake templates.
- `references/replit.md`: authoritative Replit scope, modes, and safety policy.
- `references/ai/`: progressively loaded domain instruction objects.
- `references/replit-skills/`: Replit Agent workflows for focused scenarios.
- `specifications/`: detailed normative architecture, mode, routing, artifact, execution, HITL, and distribution specifications.
- `examples/`: compact example output.
- `claude-skill/project-prompt-router/`: selects the correct artifact template.
- `claude-skill/replit-task-builder/`: builds bounded or phased Replit prompts.
- `claude-skill/*.zip`: packaged skills.

## Setup

1. Paste `CLAUDE_PROJECT_INSTRUCTIONS.md` into the Claude project instructions.
2. Upload `references/`, `templates/`, `specifications/`, and optionally `examples/`.
3. Keep one current version of each file.
4. Install the packaged router and Replit task-builder skills when reusable Claude Skills are preferred.

Replit workflows cover bounded frontend/API work, architecture refactors, full-stack features, auth/permissions, forms, tables/reporting, UI/UX, schema migrations, seeding, bug diagnosis, performance optimization, verification, and instruction maintenance.

## Replit installation

Copy:

- `references/replit.md` to project-root `replit.md`
- `references/ai/**` to project-root `ai/**`
- `references/replit-skills/**` to project-root `.agents/skills/**`

For an upgrade from version 5.5 to 6, replace `replit.md`, all `ai/**` files, and all `.agents/skills/**` folders because automatic mode selection is distributed across the root, domain references, and scenario skills. Do not copy `templates/`, `specifications/`, `CLAUDE_PROJECT_INSTRUCTIONS.md`, or `claude-skill/` into Replit; those generate and validate prompts on the Claude side.

## Design

- Root files define authority once.
- Domain files load only when relevant and expose responsibility, activation, inputs, `Must Not`, workflow, and output evidence.
- The generator selects one internal mode and one primary scenario skill automatically; users never need to choose them.
- Internal modes cover business definition, specifications, audits, backlogs, change control, prompt generation, frontend, API, full-stack, auth, forms, tables, refactors, schema evolution, seeding, diagnosis, performance, UI/UX, verification, and instruction maintenance.
- Modes and skills select procedure but never grant authority; root capability gates and explicit scope remain controlling.
- Loaded instruction objects guide behavior inside approved scope; they never expand access or replace Python contracts.
- The router selects templates by immediate deliverable, not keywords alone.
- Work that cannot be safely delivered as one batch produces separate gated phase prompts sequentially.
- Only the next authorized phase receives a full prompt; later prompts use verified handoffs.
- Bounded work starts from named paths and stops discovery once ownership, consumers, and checks are proven.
- HITL pauses only for an unknown answer/next step, two materially correct answers, or a self-invented decision that would change scope.
- A HITL request stops the entire Replit task. Replit waits for the matching human answer, validates it and scoped drift, then resumes the exact blocked step without restarting completed work.
- HITL has no modes or risk levels and never replaces authorization, stop conditions, or protected-path rules.
- Generated prompts include only applicable requirements and checks.
- Detailed specification files define requirement records, interface contracts, traceability, state coverage, verification, and distribution parity.
- `PASSED`, `FAILED`, and `NOT RUN` keep verification honest.

## Adopting this kit in a different Replit project

This kit ships with two profiles out of the box: `generic-replit` (the default - universal protections only, no project-specific paths) and `metco` (the first adopting project's own profile, with its own protected trees and business file). Dropping a submodule or vendored copy of this kit into a different Replit project without any change already works under `generic-replit`, but a project that wants its own write roots, its own extra protected paths, or its own business-file ground truth needs its own profile.

### Setup process: `tools/init-profile.py`

Running the kit against a new project is not a one-line env var and a hand-edit - it is a real setup step with two outputs (a profile entry and a business file), so it is automated as one command instead of a checklist to follow by hand:

```
python3 tools/init-profile.py --profile acme --frontend-root client/src --backend-root server/src
```

This does two things in one pass, then verifies the result actually imports and resolves correctly before writing anything to disk:

1. Appends a new entry to both `PROFILES` and `PROTECTED_PATHS` in `tools/opsgate_contracts.py` - the new profile's own `frontend_root`/`backend_root` become its `normal_write_paths`, and any `--extra-never-access <glob>` (repeatable) is added on top of the same universal baseline every profile gets (`.git/**`, `.env`, `node_modules/**`, `.github/workflows/**`, `.claude/**`, `.agents/memory/**`). It never edits an existing profile - re-running with a profile key that already exists refuses and tells you to edit it by hand.
2. Generates a starter business file (default `canonical/references/ai/<profile>.md`, matching the new `business_file` field) from the same template structure `ai/metco.md` follows - Responsibility, Activation, Inputs, a `## Business Facts` section left as fill-in placeholders, `Must Not`, `Start record`, `Workflow`, `Output Evidence` - so the new project's business ground truth has one obvious place to live instead of needing to be reverse-engineered from `ai/metco.md`'s example.

After running it: fill in the generated business file's `## Business Facts` section with the new project's real domain facts, then `python3 tools/build-distributions.py && python3 tools/validate-kit.py`, then set `OPSGATE_PROFILE=acme` (a Repl Secret is the usual place) or pass `"profile": "acme"` on individual requests - the request field takes precedence over the environment variable, which is useful for testing a profile without changing the environment.

### Doing it by hand instead

If you'd rather not run the script - or need something the flags don't cover - the two things it automates can be done directly:

1. Add a new entry to `PROFILES` and `PROTECTED_PATHS` in `tools/opsgate_contracts.py` (copy the `generic-replit` entry as a starting point) rather than editing the `metco` entry or hardcoding the new paths into `generic-replit` - a profile should describe one project's own paths, not accumulate every adopting project's paths in one shared bucket.
2. Write `canonical/references/ai/<profile>.md` following the same structure as `ai/metco.md`, and point the new profile's `business_file` field at it.

Everything else in the kit - routing, capability gates, the HITL protocol, the lexical scoring/tie detection, MCP tool wiring - is already project-agnostic and needs no change to adopt elsewhere.

### Why `ai/*.md` files mention "protected paths" without listing any

Files under `ai/` (`backend.md`, `database.md`, `maintenance.md`, and the rest, including each project's own business file like `ai/metco.md`) use "protected", "locked", and "restricted" only as behavioral vocabulary - instructions like "do not touch protected paths without authorization." None of them declare or duplicate an actual glob list. The one and only source of truth for what counts as protected on a given profile is `PROTECTED_PATHS`/`protected_paths_for(request)` in `tools/opsgate_contracts.py`; every `ai/*.md` reference to "protected" defers to whatever that function resolves for the active profile, so there is nothing to keep in sync by hand when a profile's protected paths change.

## Maintenance

Edit canonical files under `references/`, `templates/`, and `specifications/`, rebuild generated distributions, validate all skill folders, and keep packaged/source copies identical.
