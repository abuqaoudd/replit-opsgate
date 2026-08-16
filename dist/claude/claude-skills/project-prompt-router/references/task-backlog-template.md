# Task generation

Act as a senior delivery planner. Convert **[approved business/spec/audit/change source]** into a bounded, dependency-aware task backlog. Do not implement changes.

## Inputs

- Source of truth: [paths/files]
- Delivery outcome: [outcome]
- Allowed systems and paths: [scope]
- Constraints, owners, milestones, and exclusions: [list]
- Required verification or release evidence: [list]

## Method

1. Extract source requirement IDs and unresolved blockers.
2. Classify work internally by domain, risk, dependency, execution shape, and automatically selected process mode.
3. Assign the relevant instruction object set for each task, including `TaskControlInstruction`, domain object, and `VerificationInstructionObject` where implementation or verification is expected.
4. Split tasks by independently verifiable outcome, not by generic activity.
5. Keep discovery, decisions, schema change, backfill, seeding, implementation, verification, rollout, and cleanup separate where relevant.
6. For complex implementation work, create a phase plan and use `REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md`; do not emit one oversized Replit prompt.

## Task format

For each task provide:

- Task ID, title, outcome, and priority.
- Source requirement IDs.
- Dependencies and explicit prerequisites.
- Exact in-scope and out-of-scope boundaries.
- Acceptance criteria and required evidence.
- Risk and rollback/recovery note.
- Automatic process mode and routed skill family, with one-sentence routing evidence; these are not user inputs or authority.
- Selected instruction objects, object inputs, and authority boundaries.
- Bounded batch or phased execution shape, with one-sentence rationale.
- Any unresolved decision matching one of the three HITL cases and the exact task it blocks.

Use this complete task record:

| Field | Required content |
|---|---|
| Task ID and title | Stable `TASK-*` ID and outcome-focused title |
| Source traceability | Business, specification, finding, and change IDs |
| Outcome | One independently verifiable result |
| Routing | Automatically selected internal mode and skill family |
| Instruction objects | Loaded object set, object inputs, and `Must Not` boundaries |
| Scope | Exact included, excluded, protected, and unchanged areas |
| Dependencies | Predecessors, external prerequisites, and parallel-safe relationships |
| Acceptance | Positive, negative, edge, and preservation criteria |
| Implementation boundary | Ownership layer and allowed capability gates |
| Verification | Checks, environment, fixtures, manual evidence, and result labels |
| Recovery | Rollback, retry, compatibility, or data recovery boundary |
| Handoff | Evidence required before downstream work |
| Blockers | Decision ID, missing evidence, or authorization |

## Phase grouping

When phased execution is required, separate discovery/contract proof, additive foundation, migration or service behavior, consumer switch, integrated verification, and destructive cleanup. Every phase must be independently stoppable, verifiable, and recoverable.

## Backlog quality

- Avoid overlapping ownership and duplicate acceptance criteria.
- Do not hide unresolved business or contract decisions inside implementation tasks.
- Make dependency order explicit and identify parallel-safe work.
- Do not combine destructive cleanup with initial implementation.
- Mark tasks blocked when the source lacks a material decision.
- Do not create HITL checkpoints merely for risk, complexity, review, or routine authorization.
- Do not write “implement feature” as one task when ownership, data, consumer, verification, or rollback boundaries require separate outcomes.
- Do not include acceptance criteria that cannot be traced to an approved source or explicit decision.

## Report

Return the ordered backlog, dependency summary, phase groupings, blockers, and requirement coverage. End with the recommended next task or phase and why.
