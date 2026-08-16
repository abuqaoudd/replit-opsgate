# [task title]

Act as a senior [role]. Deliver: **[observable outcome]**.

Keep this bounded prompt between 500 and 850 words. State each rule once; rely on loaded instructions for general policy. Delete non-task-specific prose before returning.

Use this template only when the work can be implemented, verified, and rolled back as one bounded batch. If the work meets any complexity trigger in `REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md`, stop and switch to that template, generating only the next authorized phase prompt.

## Load first

Read `replit.md` and the active profile's business file (e.g. `ai/metco.md`), if it has one. Automatically select the most specific internal mode and installed scenario skill from this outcome; do not ask the user to choose either. Then read `[only relevant ai files]`, the selected skill, and `ai/testing.md` for implementation or verification. Stop if a capability gate or required scope is not authorized.

## Instruction objects

Record the loaded object set before editing:

| Object | Why loaded | Inputs used | Authority boundary |
|---|---|---|---|
| `TaskControlInstruction` | every task | outcome, acceptance, scope, selected mode/skill | does not override `replit.md` |
| `[DomainInstructionObject]` | [routing evidence] | [task-specific evidence] | [unauthorized surfaces excluded] |
| `VerificationInstructionObject` | required checks/reporting | acceptance, risks, changed paths | does not authorize broader tests or writes |

Use each object's `Responsibility`, `Inputs`, `Must Not`, `Workflow`, and `Output Evidence` sections as the operating contract. A loaded object guides behavior only inside already approved scope.

## Scope

| Access | Paths |
|---|---|
| Write | `[exact paths]` |
| Minimum read-only | `[exact paths]` |
| Never access | `[never_access paths for the active profile - see protected_paths_for(request)]`, resolved aliases |
| Locked | `[task-relevant locked categories]` |

Preserve pre-existing work. Do not perform unrelated cleanup or change public contracts unless explicitly listed below.

## HITL pause rule

Do not add HITL classifications to routine work. Pause only if: the answer or next step remains unknown after bounded inspection; two materially correct answers remain with no evidence-based winner; or proceeding requires an agent-made decision that changes this scope. Return only the decision request defined in `replit.md`, stop the entire task, and wait for the matching `DECIDE` reply. Do no inspection, editing, testing, or independent work while paused. Validate the reply and minimal scoped drift, then resume from the exact blocked step without restarting completed work. HITL is not an internal mode.

Run the Per-Action Gate from `replit.md` before every step in `## Execute` below, not only once before this task starts — state `Gate: OK` or `Gate: BLOCKED` before each step and stop immediately on `BLOCKED` rather than continuing to the next step or deferring it to the final report.

## Decisions

- `[decision/authorization]: [value]`
- `[assumption]: [value]`

Do not reconfirm listed decisions. Stop only when an unresolved choice changes security, data integrity, public contracts, or destructive behavior.

## Acceptance criteria

1. [observable behavior]
2. [role/error/edge behavior]
3. [preserved contract or UI behavior]
4. [verification evidence]

## Inspect before editing

1. Capture scoped `git status --short -- [paths]` and `git diff -- [paths]`.
2. Start with named paths, direct imports/callers, and related tests. Expand one dependency hop only for a concrete unresolved ownership, contract, consumer, or risk question.
3. Follow the applicable ownership order from `replit.md`.
4. Record the selected change owner and why.
5. Before adding a unit, record search scope, closest candidates, reuse/extend decision, destination, ownership, and duplication prevention.

Stop discovery when the owner, affected contract, direct consumers, pre-existing changes, and relevant checks are known. Do not continue searching for redundant confirmation.

## Execute

Before each step below, run the Per-Action Gate and state its result before acting.

1. [bounded implementation step]
2. [bounded implementation step]
3. Verify the batch before cleanup or deletion.
4. Remove code only after proving no approved-path consumer remains.

Fail fast on a missing prerequisite. Run independent read-only inspection or checks in parallel when safe; keep writes sequential at ownership boundaries. Use one short plan and do not narrate role-by-role activity.

Task-specific requirements:

- [validation/security/data/UI requirement]
- [failure/loading/conflict/accessibility requirement]
- [behavior that must not change]

## Verify

Use existing scripts and the smallest risk-based check set from `ai/testing.md`. Broaden only after a targeted failure or evidence of wider impact. Do not install dependencies, run the full suite by default, or use unknown/production services.

| Check | Target | Expected evidence |
|---|---|---|
| [type/test/runtime/manual] | [scope] | `PASSED`, `FAILED`, or `NOT RUN` plus command/status or observation |

Review final scoped status and diff. Confirm every changed line belongs to this task and no protected or locked path changed.

## Report

Return:

1. Outcome and acceptance criteria status.
2. Automatically selected internal mode and skill, with one-sentence routing evidence.
3. Selected instruction objects, object inputs used, and authority boundaries honored.
4. Files changed and reason per file.
5. Reuse/creation/ownership decisions.
6. Checks with exact results; explain `FAILED` and `NOT RUN`.
7. Limitations, remaining risks, and blockers.
8. Scope compliance and preservation of pre-existing work.

Begin with instruction loading, automatic routing, and the scoped baseline. Do not edit until ownership and the bounded plan are clear.
