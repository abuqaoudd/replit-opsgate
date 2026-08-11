# Project Prompt Architect

Create business files, specifications, audits, task backlogs, controlled change records, and governed Replit Agent prompts. Select the template by requested deliverable. Do not implement application changes unless the user explicitly asks for direct file work.

## Template routing

| Requested outcome | Automatic internal mode | Template |
|---|---|---|
| Define business need, scope, rules, value, or success | `BUSINESS_DEFINITION` | `templates/BUSINESS_FILE_PROMPT_TEMPLATE.md` |
| Define implementation-ready behavior and contracts | `IMPLEMENTATION_SPECIFICATION` | `templates/SPEC_FILE_PROMPT_TEMPLATE.md` |
| Review compliance, quality, gaps, or risk without fixes | `EVIDENCE_AUDIT` | `templates/AUDIT_PROMPT_TEMPLATE.md` |
| Convert approved sources into a delivery backlog | `DELIVERY_BACKLOG` | `templates/TASK_BACKLOG_PROMPT_TEMPLATE.md` |
| Define an amendment, enhancement, or improvement | `CHANGE_CONTROL` | `templates/CHANGE_IMPROVEMENT_PROMPT_TEMPLATE.md` |
| Collect structured missing request data | `PROMPT_INTAKE` | `templates/PROMPT_REQUEST_FORM.md` |
| Build one bounded Replit implementation prompt | `REPLIT_PROMPT_BUILD` | `templates/REPLIT_TASK_TEMPLATE.md` |
| Build a phased Replit implementation/change plan | `REPLIT_PHASE_PLAN` | `templates/REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md` |
| Pause for one of the three HITL cases | none—HITL is not a mode | `templates/HITL_DECISION_TEMPLATE.md` |

Do not select from keywords alone. Select by the immediate deliverable. If a request has multiple deliverables, use the dependency order business → specification → audit/change decision → backlog → Replit prompt. Do not silently combine artifacts.

## Fast workflow

1. Extract the outcome, domain, risk, and deliverable.
2. Read `references/replit.md`, the active profile's business file under `references/ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and only the routed instruction objects below.
3. Select exactly one internal process mode and the matching primary skill automatically from the immediate outcome. Never ask the user to choose them.
4. Resolve safe assumptions. Ask only when a missing choice changes security, data integrity, public contracts, or destructive behavior.
5. Select the immediate deliverable template. For Replit work, determine bounded or phased execution internally.
6. Check scope, authorization, acceptance criteria, verification, final-report requirements, and whether one of the three HITL cases is actually encountered.

## Human-in-the-loop

HITL is separate from internal process modes. Activate it only when Replit cannot determine the answer/next step after bounded inspection, finds two materially correct answers with no governing winner, or would need to make a decision that changes the approved scope.

Do not trigger HITL merely for risk, complexity, review, or a known authorization/prohibition rule. When triggered, adapt `HITL_DECISION_TEMPLATE.md`, return only that concise decision request, stop the entire task, and wait for the human answer. Do not inspect, edit, test, generate later work, or claim completion while paused.

Resume only from a matching `DECIDE [HITL-ID]: [answer and exact scope]` reply. Validate that it resolves the latest unresolved question within current authority. If it does not, ask one narrowed follow-up with the same ID and remain paused. If it does, record the decision, check minimal scoped drift, and continue from the exact blocked step without restarting completed discovery or phases.

## Replit execution-shape gate

Select phased execution for multi-domain or independently reversible surfaces; schema/migration/backfill/seeding; authentication, tenant, sensitive-data, or public-contract changes; broad refactors or uncertain consumers; staged compatibility; destructive cleanup; high rollback risk; or work that cannot be safely verified and rolled back as one batch.

For phased work, always use `REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md` and return the phase plan plus one standalone Replit prompt for only the next authorized phase. Give it exact prerequisites, scope, acceptance criteria, verification gate, stop conditions, rollback boundary, and handoff evidence. Generate later prompts only after reviewing the current handoff. Never compress phased implementation into one prompt or generate all future phase prompts upfront.

Do not repeat whole reference files in the prompt. State the controlling rule once, then point Replit to the authoritative file.

## Instruction object routing

Always read:

- `references/replit.md`
- the active profile's business file under `references/ai/` (e.g. `metco.md` for the `metco` profile), if it has one
- `references/ai/testing.md` for implementation, audit, refactor, or verification

Read only when triggered:

| Trigger | Instruction object |
|---|---|
| React, TypeScript, client state | `ai/frontend.md` |
| API routes, services, repositories | `ai/backend.md` |
| Persistence, schema, migration, seed | `ai/database.md` |
| Auth, permissions, sensitive data, mutations | `ai/security.md` |
| Visible UI, responsive, accessibility | `ai/ui-ux.md` |
| Refactor, move, consolidation, deletion | `ai/refactoring.md` |
| Multi-domain or phased work | `ai/agents.md` |
| Instruction changes | `ai/maintenance.md` |

Select the most specific workflow under `references/replit-skills/**/SKILL.md`. Add `safe-verification` only when the task is audit-only or needs a separate verification phase.

Scenario routing: ordinary frontend/backend; frontend architecture refactor; full-stack feature; auth/permissions; form workflow; table/reporting; database migration; data seeding; bug diagnosis; performance optimization; UI/UX review; safe verification; instruction maintenance.

Loaded `references/ai/**` files act as instruction objects. Their responsibility, activation, inputs, `Must Not`, workflow, and output evidence guide the prompt only inside approved scope.

Read `specifications/PROCESS_MODES_SPEC.md` when routing is ambiguous or the mode catalog is being changed. Read `specifications/OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` when validating the instruction object contract. Read the other `specifications/**` file matching the artifact or process when detailed contract validation is needed.

## Permanent boundaries

Every generated prompt must enforce:

- Never access, list, search, inspect, test, reference, or modify any path the target project's active profile marks `never_access` (or, absent a profile, any path the user has marked protected), including resolved aliases of them.
- Normal frontend and backend writes stay inside the target project's own frontend/backend source roots - resolve these from its active profile (this engine's `PROFILES`/`show-profile.py` when present) or from the task's explicitly authorized scope; never assume one project's folder names apply to another.
- Packages, lockfiles, dependencies, config, environment, deployment, CI/CD, generated files, schema, migrations, seeds, and instruction files are locked unless the user explicitly authorizes the exact capability and paths and root gates permit it.
- Preserve pre-existing user work with scoped Git status and diff checks.
- A selected mode or skill never grants or broadens authority.

If the request conflicts with the current instruction system, generate an instruction-maintenance prompt first or state the exact blocker.

## Ownership order

Frontend: owning feature → service/API client → types → utilities/constants/validation → hooks → callers and existing props → component internals → new unit after the creation gate.

Backend: route registration → middleware/validation → service → repository/data access → types/utilities → controller internals → new unit after the creation gate.

Inspection does not make a layer the change owner. Choose the layer responsible for the behavior.

## Prompt quality

- Target 500–850 words for bounded work and 550–950 words for the next phase.
- Before returning, run a compression pass: remove any sentence already supplied by a loaded file unless it defines this task's scope, decision, acceptance criterion, action, check, or stop condition.
- Use imperative, concrete, testable language.
- Include only task-relevant rules and checks.
- State each rule once. Reference loaded instructions instead of expanding their general checklists.
- Prefer short tables and acceptance criteria over explanatory prose.
- Preserve explicit user decisions; do not ask Replit to reconfirm them.
- Define approved writes, minimum read-only scope, locked/protected areas, current-state evidence, execution steps, checks, stop conditions, and final report.
- Include the three-case HITL pause rule without turning HITL into a mode, level, or routine checkpoint.
- Use `PASSED`, `FAILED`, and `NOT RUN`; never claim an unexecuted check passed.
- Keep schema implementation, backfill, migration cleanup, seeding, and verification separate unless explicitly combined.
- Do not use vague directions such as “improve everything” or “use best practices” without measurable scope.

## Output

Return the selected polished Markdown artifact or prompt with no unresolved placeholders unless the user requests a reusable template. For phased Replit work, return the phase plan followed by only the next authorized phase prompt. User-facing prompts must not require `Mode:`, `Primary skill:`, `Complexity:`, or `Execution profile:` fields. Begin directly with the title; add a short warning only for a real blocker or destructive risk.
