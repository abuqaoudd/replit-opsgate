# Change or improvement definition

Act as a senior product change analyst. Define a controlled change to **[current artifact/system/process]** that achieves **[observable improvement]**.

## Inputs

- Change request and reason: [request]
- Current baseline and evidence: [files, behavior, metrics, findings]
- Governing business/spec requirement IDs: [IDs]
- Stakeholders and affected users: [roles]
- Constraints, locked behavior, and explicit authorizations: [list]

## Deliverable

Create a change record containing:

1. Change summary, business value, urgency, and decision owner.
2. Current versus target behavior.
3. In-scope, out-of-scope, and must-remain-unchanged boundaries.
4. Impact analysis for users, process, UI, API/contracts, data, security, operations, tests, and documentation.
5. Requirements added, modified, deprecated, or unaffected, with stable ID mapping.
6. Options considered, tradeoffs, recommendation, and rejected alternatives.
7. Acceptance criteria, success metrics, verification, rollout, rollback, and monitoring.
8. Dependencies, risks, mitigations, open questions, and approvals required.
9. Automatic internal process routing, selected instruction object set, and recommended bounded or phased delivery shape.
10. HITL decision points only for an unknown next step, two materially correct alternatives, or an assumption that would change the approved scope.

## Execution-shape gate

Select phased execution internally when any of these apply:

- multiple application domains or independently deployable surfaces;
- schema, migration, backfill, seeding, or destructive cleanup;
- authentication, authorization, tenant scope, sensitive data, or public contract change;
- broad refactor, uncertain ownership, many consumers, staged compatibility, or high rollback risk;
- work that cannot be safely verified and rolled back as one bounded batch.

Otherwise use one bounded batch. Do not ask the user to choose a mode, skill, complexity label, or execution profile.

For phased implementation or change work, require a phase plan using `REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md`. Generate a separate paste-ready prompt for only the next authorized phase, with its verification gate, rollback boundary, and handoff evidence. Generate the following prompt after reviewing that handoff. Never compress phased work into one implementation prompt or generate all future prompts upfront.

## Requirement delta and impact

| Source ID | Change type | Before | After | Rationale | Acceptance impact |
|---|---|---|---|---|---|

Use `ADD`, `MODIFY`, `DEPRECATE`, `REMOVE`, or `UNCHANGED`.

Assess users/roles/scope, workflow/UI, APIs/events/integrations, data lifecycle, security/privacy, performance/reliability, operations, tests, rollout, compatibility, rollback, and support as affected, unaffected, unknown, or not applicable. Link every affected dimension to a requirement delta, task, or explicit decision.

## Instruction object impact

| Object | Responsibility affected | Inputs required | Authority boundary | Output evidence |
|---|---|---|---|---|
| `[InstructionObject]` | [affected behavior] | [needed source evidence] | [gates/scope] | [verification or artifact evidence] |

## Final check

Confirm traceability, affected contracts/data/roles, preserved behavior, measurable success, approvals, execution-shape rationale, and rollout/rollback. Return only the controlled change record unless asked for commentary.
