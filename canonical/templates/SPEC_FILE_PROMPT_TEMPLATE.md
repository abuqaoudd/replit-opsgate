# Specification file generation

Act as a senior product and technical specification author. Create or update **[spec file name]** for **[feature/system/change]**.

## Inputs

- Approved business requirements: [file/path or pasted requirements]
- Current system evidence: [code areas, API/schema docs, UI, logs, tests]
- Constraints and explicit decisions: [list]
- Existing specification: [path or none]
- Delta spec request: [module name, business documentation link/path, existing spec link/path, or none]
- Intended implementation surface: [frontend/backend/data/integration]

Do not convert assumptions into requirements. Use `OPEN QUESTION` when a missing decision changes security, data integrity, public contracts, destructive behavior, or scope.

## Delta spec generation

When the request is to generate a delta specification for a module:

1. Check the business documentation file for **[module name] module** at **[business documentation link/path]**.
2. Check the existing spec file for the **[module name] module** at **[existing spec link/path]**.
3. Compare the new business MD against the existing spec and generate a delta spec file documenting only the new, changed, removed, or newly clarified requirements.
4. Follow the same spec template, metadata format, structure, terminology, and writing style as the existing spec files.
5. Name the file using the same spec filename template: `spec-[module-name]-YYYY-MM-DD.md`. For example, for the roles module on 2026-07-26, use `spec-roles-2026-07-26.md`.

The delta spec must preserve existing approved behavior unless the business documentation explicitly changes it. It must distinguish confirmed deltas from inferred gaps, mark missing decisions as `OPEN QUESTION`, and keep all requirement IDs traceable to the governing business documentation and prior spec sections.

## Deliverable

Write an implementation-ready specification containing:

1. Document control: ID, version, status, owner, reviewers, date, revision history, and governing sources.
2. Objective, system context, scope, exclusions, glossary, assumptions, and explicit decisions.
3. Requirement traceability from business/change IDs to `REQ-*`, `NFR-*`, `SEC-*`, `DATA-*`, and `UX-*`.
4. Actors, authentication context, permissions, tenant/object scope, field-level access, and authorization matrix.
5. Functional flows with triggers, preconditions, success, alternate, validation, empty, loading, conflict, error, retry, cancellation, and recovery states.
6. State transitions with allowed transitions, guards, side effects, audit events, and invalid-transition behavior.
7. Interfaces and contracts: operation, input/output fields, validation, errors, pagination, idempotency, compatibility, and versioning.
8. Data ownership, entities, relationships, lifecycle, source of truth, retention, integrity, concurrency, migration/backfill implications, and auditability.
9. UI information architecture, interactions, responsive states, keyboard/focus behavior, accessibility, feedback, destructive safeguards, and content.
10. Measurable performance, security, privacy, reliability, availability, observability, capacity, and operational limits.
11. Architecture boundaries, ownership, reuse candidates, dependencies, integration assumptions, and prohibited changes.
12. Relevant instruction object set, object responsibilities affected, required inputs, authority boundaries, and expected output evidence.
13. Compatibility, rollout, feature control, rollback/recovery, monitoring, and support expectations.
14. Acceptance criteria in observable Given/When/Then or equivalent form.
15. Verification matrix, safe test data, environments, failure injection, and evidence requirements.
16. Risks, decisions, and open questions, including only questions eligible for the three-case HITL protocol.

## Functional requirement record

For every `REQ-*`, include:

| Field | Content |
|---|---|
| Behavior | One atomic required behavior |
| Source IDs | Governing business/change IDs |
| Actor and scope | Role, tenant, object, and field scope |
| Preconditions and trigger | Required state, permission, and event |
| Main result | Observable success behavior |
| Alternate/error result | Validation, denial, conflict, failure, retry |
| Data effects | Reads, writes, audit, and side effects |
| Contract impact | UI/API/event/schema compatibility |
| Acceptance IDs | Linked testable criteria |

## Interface contract record

For each API, event, form, import/export, or integration contract, specify owner and consumers; operation and transport; authentication and authorization; complete field definitions; success and side effects; stable error taxonomy and retry; idempotency, ordering, pagination, limits, and timeout; backward compatibility; and safe observability.

## Verification matrix

Map every requirement to positive behavior, permission and object-scope denial, validation and boundary values, empty/loading/conflict/error/recovery states, compatibility and regression coverage, and exact automated or manual evidence.

## Instruction object contract

For each affected implementation surface, include:

| Object | Responsibility | Activation reason | Inputs needed | Must-not boundary | Output evidence |
|---|---|---|---|---|---|
| `[InstructionObject]` | [owned behavior] | [why applicable] | [source evidence] | [scope/gates] | [checks/artifacts] |

## Quality rules

- Describe required behavior and contracts; avoid prescribing code unless an architecture decision is approved.
- Use stable IDs and map every acceptance criterion to one or more requirement IDs.
- State exact units and thresholds for measurable requirements.
- Preserve existing contracts unless the source explicitly authorizes a change.
- Distinguish schema work, backfill, seeding, consumer migration, and cleanup.
- Identify contradictions between business requirements, current behavior, and technical constraints.
- Use exact units, limits, and ownership. Never use “fast,” “secure,” “user-friendly,” or “handle errors” without measurable behavior.
- Separate normative requirements from implementation notes and recommendations.

## Final check

Confirm traceability, actor and data scope, success and failure behavior, compatibility, testability, rollout/rollback, and unresolved decisions. Return only the polished specification unless asked for commentary.
