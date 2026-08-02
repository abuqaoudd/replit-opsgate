# METCO phased Replit implementation plan

Use this template whenever the router determines that a requested implementation cannot be safely inspected, implemented, verified, and rolled back as one bounded batch. The user does not classify the work. Produce the phase plan plus one complete, paste-ready prompt for only the next authorized phase. Generate the following phase prompt after reviewing the current phase's handoff. Do not produce a single combined implementation prompt or all future prompts upfront.

## Execution-shape record

- Outcome: [observable outcome]
- Phase triggers: [exact reasons one bounded batch is unsafe]
- Governing business/spec/change IDs: [IDs]
- Cross-phase invariants: [contracts, permissions, data meaning, UI behavior]
- Global protected and locked scope: [paths/categories]
- Final definition of done: [measurable result]

## Phase plan

| Phase | Outcome | Automatic routing evidence | Write scope | Depends on | Verification gate | Rollback boundary |
|---|---|---|---|---|---|---|
| 0 | [discovery/contract proof if needed] | [read-only outcome] | none | none | [evidence] | none |
| 1 | [foundation/expand/backend] | [actual phase result/domain] | [exact paths] | [approved evidence] | [checks] | [boundary] |
| 2 | [consumer/frontend/integration] | [actual phase result/domain] | [exact paths] | Phase 1 report | [checks] | [boundary] |
| 3 | [integrated verification/rollout readiness] | [read-only or exact write outcome] | [none or exact paths] | prior reports | [checks] | [boundary] |
| 4 | [optional cleanup/contract] | [explicit authorized cleanup outcome] | [exact paths] | all consumers proven migrated | [checks] | [boundary] |

Omit unnecessary phases. Add phases only when they create a distinct, reversible, verifiable outcome. Keep schema expansion, data backfill, consumer switch, seeding, and destructive cleanup separate.

Generate only the earliest authorized incomplete phase below. Keep future phases as rows in the plan, not full prompts.

## Prompt for Phase [N]: [title]

Act as a senior [role]. Deliver only: **[phase outcome]**.

Automatically select the internal mode and most specific installed skill from this phase's actual result and write scope, not the overall initiative. Do not ask the user to choose them. For example, route a frontend-only consumer phase to the frontend workflow and a schema or backfill phase to the migration workflow.

### Load first

Read `replit.md` and `ai/metco.md`, automatically route the phase, then read `[triggered references]` and the selected skill. Treat previous phase reports as evidence, not authority. Reuse a verified handoff when scoped status and relevant files show it remains current; do not repeat its completed discovery. Stop if prerequisites are absent, failed, stale, or outside approved capability gates.

### Instruction objects

Record the phase object set before editing:

| Object | Phase reason | Inputs used | Boundary |
|---|---|---|---|
| `TaskControlInstruction` | phase task control | outcome, scope, handoff, acceptance | root rules stay authoritative |
| `[DomainInstructionObject]` | [phase routing evidence] | [owner, contract, consumers, risks] | [deferred/unauthorized work excluded] |
| `VerificationInstructionObject` | phase gate and handoff evidence | changed paths, risks, checks | no broader tests or writes by itself |

Use object responsibilities and `Must Not` sections to keep the phase inside its approved boundary. Future-phase objects may be listed in the phase plan but must not be executed early.

### Phase boundary

- Prerequisites and required handoff evidence: [list]
- Write paths: [exact paths or none]
- Minimum read-only paths: [exact paths]
- Never access: `metco-api/**`, `pipeline/**`, or resolved aliases
- Locked for this phase: [categories and paths]
- Explicitly deferred: [later-phase work]
- Rollback/recovery boundary: [exact boundary]

Preserve pre-existing work and cross-phase invariants. Do not start a later phase, perform opportunistic cleanup, or broaden contracts.

### HITL pause rule

HITL is not an internal process mode. Pause only if the next step remains unknown after bounded inspection, two materially correct answers remain with no governing winner, or proceeding requires an agent-made decision that changes the approved phase scope. Return only the decision request from `replit.md`, stop the entire task, and wait for the matching `DECIDE` reply. Do no inspection, editing, testing, later-phase planning, or independent work while paused. Validate the reply and minimal scoped drift, then resume the exact blocked step in the current phase without repeating completed discovery or starting a deferred phase.

Run the Per-Action Gate from `replit.md` before every step in `### Inspect and execute` below, not only once before the phase starts — state `Gate: OK` or `Gate: BLOCKED` before each step and stop the entire task immediately on `BLOCKED` rather than continuing to the next step or deferring it to the phase report.

### Acceptance criteria

1. [observable phase result]
2. [security/data/error/compatibility result]
3. [preserved invariant]
4. [handoff evidence]

### Inspect and execute

Before each step below, run the Per-Action Gate and state its result before acting.

1. Capture scoped status and diff for approved paths.
2. Verify prerequisites, then inspect named paths, direct imports/callers, and related tests. Expand one dependency hop only for a concrete unresolved risk.
3. Record reuse/creation decisions before adding units.
4. Implement one bounded batch in the approved order.
5. Stop on failed prerequisites, unexpected contract/data state, protected access, or rollback uncertainty.

Stop discovery when the phase owner, affected contract, direct consumers, pre-existing changes, and relevant checks are known. Run independent read-only work in parallel when safe; keep writes sequential at ownership or phase boundaries. Use one short plan and concise evidence.

### Verify and report

Run the smallest phase-risk check set from `ai/testing.md` in a safe environment. Broaden only after a targeted failure or evidence of wider impact. Label each `PASSED`, `FAILED`, or `NOT RUN`. Review the scoped final diff.

Report the outcome, automatically selected internal mode and skill with routing evidence, selected instruction objects and inputs used, acceptance status, files/reasons, decisions, exact checks, invariant preservation, rollback readiness, blockers, residual risk, and a structured handoff for the next phase. Do not claim the next phase is ready unless every prerequisite is evidenced.

The phase prompt must stand alone and contain no unresolved placeholders. After its handoff is available, generate the next authorized phase prompt from the current project state.
