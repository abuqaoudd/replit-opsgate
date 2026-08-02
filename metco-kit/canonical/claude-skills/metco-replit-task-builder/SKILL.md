---
name: metco-replit-task-builder
description: Build fast, accurate, paste-ready Replit Agent prompts for METCO implementation, diagnosis, audits, tests, frontend/backend work, security, UI/UX, refactors, schema evolution, data seeding, performance, and instruction maintenance. Automatically select the internal execution mode, most specific installed skill, and bounded or phased shape from the requested outcome without asking the user to choose them. Use when a request must obey protected paths, capability gates, ownership rules, creation gates, verification, phase boundaries, reporting, and the three-case HITL protocol.
---

# METCO Replit Task Builder

Return one self-contained Replit prompt. Do not implement the application change unless direct file work is explicitly requested.

Read `references/process-modes-spec.md` when selecting or validating an internal mode. Read `references/object-oriented-instructions-spec.md` when validating loaded instruction object structure. Read the matching section of `references/scenario-skill-contracts-spec.md` when a mode needs detailed input, workflow, or completion evidence. Read `references/replit-execution-spec.md` for capability gates, phase design, and execution contracts. Read `references/hitl-spec.md` when emitting or resuming a HITL decision.

## Build path

1. Extract outcome, acceptance criteria, domain, risk, allowed change, and deliverable.
2. Read `references/replit.md`, `references/ai/metco.md`, and only triggered domain instruction objects.
3. Automatically select one internal mode and the most specific workflow in `references/replit-skills/` from the actual outcome and write surface.
4. Record selected instruction objects, why each object loaded, object inputs, and authority boundaries.
5. Determine bounded or phased execution internally. HITL remains separate from process modes.
6. Detect conflicts with root scope. Follow known authorization and stop rules directly; activate HITL only for one of the three cases below.
7. For one safe reversible batch, adapt `references/task-template.md`. Otherwise adapt `references/phased-implementation-template.md`, return the phase plan, and generate only the next authorized phase prompt.
8. Return no unresolved placeholders unless a reusable template was requested.

Never emit the obsolete labels `NORMAL_IMPLEMENTATION`, `APPROVED_ARCHITECTURE_REFACTOR`, `AUDIT_ONLY`, `INSTRUCTION_MAINTENANCE`, `DATABASE_SCHEMA_MIGRATION`, or `DATA_SEEDING`. Use the v6 internal mode catalog and describe authorization through capability evidence.

## Execution-shape gate

Use phases for multi-domain or independently reversible surfaces; schema/migration/backfill/seeding; auth, tenant, sensitive-data, or public-contract changes; broad refactors or uncertain consumers; staged compatibility; destructive cleanup; high rollback risk; or any change that cannot be safely verified and rolled back in one bounded batch. Otherwise use one bounded batch.

For phased work:

- Produce a phase plan plus one paste-ready prompt for the next authorized phase.
- Automatically select each mode and primary skill from that phase's outcome and write scope, not the overall initiative.
- Give every phase one outcome, exact scope, prerequisites, checks, stop conditions, rollback boundary, and handoff evidence.
- Separate discovery, schema expansion, backfill, consumer switch, seeding, verification, and destructive cleanup when applicable.
- Do not start or authorize a later phase from an earlier phase prompt.
- Require evidence from the prior phase before the next phase.
- Generate a later phase prompt only after reviewing the current phase handoff.

## Fast accurate profile

- Default to `FAST_ACCURATE`.
- Start at named paths and direct relationships; expand only for a concrete unresolved risk.
- Stop discovery after ownership, affected contract, direct consumers, pre-existing changes, and relevant checks are known.
- Reuse current verified phase handoffs instead of repeating discovery.
- Select the smallest risk-based verification set; broaden only on failure or evidence of wider impact.
- Permit parallel independent read-only work, but serialize writes at ownership and phase boundaries.
- Require one short plan and concise evidence, not role-by-role narration.

## Human-in-the-loop

Activate HITL only when:

1. the answer or next step remains unknown after bounded approved inspection;
2. two materially correct answers remain and no requirement, convention, or evidence selects one; or
3. proceeding requires the agent to make a decision that changes or expands the approved scope.

Do not emit HITL metadata for normal work. Do not trigger it merely for risk, complexity, review, destructive work, security, or a known authorization rule. Follow known rules directly.

When triggered, adapt `references/hitl-decision-template.md` using the rules in `replit.md`. Return only the decision request: stable question ID, case number, exact question, evidence checked, unknowns, both options/tradeoffs for case 2, current/proposed boundary for case 3, smallest needed decision, effects, and required `DECIDE` response. Stop the entire task and wait; do not inspect, generate, execute, verify, or continue independent work.

On the next user message, resume only if it provides `DECIDE [HITL-ID]: [answer and exact scope]` for the latest unresolved request. Validate that the answer resolves the question within existing authority. If it does not, return one narrowed follow-up with the same ID and remain paused. If it does, record the decision, require a minimal scoped drift check, and generate continuation from the exact blocked step without repeating completed discovery or phases.

## Route references

| Task signal | Read |
|---|---|
| Frontend/client | `ai/frontend.md` |
| Backend/API | `ai/backend.md` |
| Persistence/migration/seed | `ai/database.md` |
| Auth/data sensitivity/mutation | `ai/security.md` |
| Visible UI/accessibility | `ai/ui-ux.md` |
| Refactor/move/delete | `ai/refactoring.md` |
| Multi-domain/phased | `ai/agents.md` |
| Instruction changes | `ai/maintenance.md` |
| Implementation/audit/verification | `ai/testing.md` |

Loaded route references act as instruction objects. Their `Responsibility`, `Activation`, `Inputs`, `Must Not`, `Workflow`, and `Output Evidence` sections guide the prompt only inside approved scope.

## Non-negotiable scope

- Never access or reference `metco-api/**`, `pipeline/**`, or aliases resolving to them.
- Normal writes: frontend `artifacts/metco/src/**`; backend `artifacts/api-server/src/**`.
- Keep packages, dependencies, config, environment, deployment, generated files, schema, migrations, seeds, and instructions locked unless explicit user authorization and root capability gates permit exact paths.
- Preserve pre-existing work and require scoped Git evidence.
- A selected mode or skill never grants or broadens authority.

## Prompt minimum

Target 500–850 words for a bounded prompt and 550–950 words for the current phase. State each rule once and reference loaded instructions instead of reproducing their general checklists. Before returning, remove every sentence that is neither task-specific scope, decision, acceptance criterion, action, check, nor stop condition.

Include:

- exact objective and observable acceptance criteria;
- automatic routing instruction and mandatory files; never require the user to provide mode, skill, complexity, or execution profile;
- selected instruction objects, object inputs, and object authority boundaries;
- approved writes, minimum reads, protected/locked areas;
- current-state and ownership evidence;
- creation gate only if a new unit may be needed;
- bounded execution steps;
- task-specific verification and honest result labels;
- stop conditions, final diff, concise report, and definition of done.
- the three-case HITL pause rule, separate from internal process modes.

For phased work, include the overall invariant and final definition of done once in the plan, then only the current phase scope and acceptance criteria in the generated prompt.

Do not copy full reference checklists. Include only applicable states, roles, endpoints, viewports, data checks, and commands.

Use `references/request-form.md` only when key information is absent. Use safe assumptions unless ambiguity changes security, data integrity, public contracts, or destructive behavior.
