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

This kit was originally built for one project (the `metco` profile in `manifests/profiles.json`), whose protected paths (`metco-api/**`, `pipeline/**`) and write roots are specific to that project. Dropping a submodule or vendored copy of this kit into a different Replit project without any change still works, but inherits those project-specific paths, which are meaningless - and can be misleading - anywhere else.

To adopt it elsewhere:

1. Set the `OPSGATE_PROFILE` environment variable (a Repl Secret is the usual place) to `generic-replit`. This switches `route-request.py`, `preflight.py`, and `check-paths.py` to a profile with only universal protections (`.git/**`, `.env`, `node_modules/**`, `.github/workflows/**`, `.claude/**`, `.agents/memory/**`) and none of the original project's specific ones.
2. If the new project has its own protected trees that deserve the same treatment `metco-api/**`/`pipeline/**` get in the original profile, add a new entry to `PROFILES` and `PROTECTED_PATHS` in `tools/opsgate_contracts.py` (copy the `generic-replit` entry as a starting point) rather than editing the `metco` entry or hardcoding the new paths into `generic-replit` - a profile should describe one project's own paths, not accumulate every adopting project's paths in one shared bucket.
3. `OPSGATE_PROFILE` can also be set per-request via an optional `"profile"` field on the request JSON itself, which takes precedence over everything except the environment variable - useful for testing a profile without changing the environment.

Everything else in the kit - routing, capability gates, the HITL protocol, the lexical scoring/tie detection, MCP tool wiring - is already project-agnostic and needs no change to adopt elsewhere.

## Maintenance

Edit canonical files under `references/`, `templates/`, and `specifications/`, rebuild generated distributions, validate all skill folders, and keep packaged/source copies identical.
