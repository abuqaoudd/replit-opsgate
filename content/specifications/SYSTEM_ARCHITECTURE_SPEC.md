# System Architecture Specification

Specification version: 7

## 1. Purpose

The engine converts a user’s desired outcome and allowed scope into governed project artifacts or executable Replit instructions. Users describe what they need; routing logic and skills determine how to perform it.

## 2. Core requirements

- `SYS-001`: User-facing prompts MUST NOT require users to choose a mode, primary skill, complexity label, or execution profile.
- `SYS-002`: The router MUST select workflows from the requested deliverable, observable outcome, affected domain, scope, and risk evidence.
- `SYS-003`: A selected skill MUST NOT expand write access, protected paths, or explicit authorization.
- `SYS-004`: Root instructions MUST define permanent boundaries and capability gates.
- `SYS-005`: Detailed domain procedure MUST live in progressively loaded references or skills.
- `SYS-006`: Every generated implementation prompt MUST be self-contained for its current bounded batch or current authorized phase.
- `SYS-007`: Complex work MUST be decomposed internally; the user does not classify it.
- `SYS-008`: HITL MUST activate only under the three cases in `HITL_SPEC.md`.
- `SYS-009`: Facts, decisions, assumptions, recommendations, open questions, and authorizations MUST remain distinguishable.
- `SYS-010`: Stable identifiers MUST trace business requirements through specifications, changes, tasks, implementation, and verification.

## 3. Components

| Component | Responsibility | Must not do |
|---|---|---|
| Claude project instructions | Route artifact generation and load references | Implement application code without a direct request |
| Artifact router skill | Select one immediate artifact contract | Merge unrelated deliverables silently |
| Replit task-builder skill | Generate bounded or sequential phased prompts | Ask users to select workflow labels |
| `replit.md` | Enforce authority, routing lifecycle, HITL, and permanent safety | Duplicate all domain instructions |
| `ai/**` instruction objects | Supply triggered domain responsibilities, inputs, boundaries, workflows, and output evidence | Grant broader authority |
| Replit scenario skills | Execute the selected workflow | Self-authorize protected or exceptional work |
| Templates | Provide output structure and minimum evidence | Expose internal router labels as user inputs |
| Specifications | Define normative engine behavior and traceability | Override runtime authority |

## 4. Input contract

The minimum useful request contains:

- desired outcome;
- affected product or artifact;
- allowed scope or named target;
- source evidence when available;
- acceptance evidence or definition of done.

The system SHOULD infer low-risk details from approved evidence. It MUST use HITL only when an unresolved choice matches one of the three cases.

## 5. Authorization model

Authority comes from the root rules and explicit user intent, not from a selected skill.

Ordinary application work is limited to the normal frontend and Replit-backend trees. Exceptional capabilities require explicit user authorization and exact targets:

- broad architecture or ownership refactoring;
- instruction-system maintenance;
- schema, migration, mapping, or backfill work;
- non-production data seeding;
- deletion, contract change, or destructive cleanup;
- package, configuration, environment, deployment, or generated-file changes.

Selecting a migration or seeding skill proves workflow relevance only. It does not prove authorization, environment safety, or scope.

## 6. Runtime state model

| State | Entry | Allowed action | Exit |
|---|---|---|---|
| Routing | New request or continuation | Load minimum authority and select skill | Workflow selected or real blocker |
| Inspecting | Authorized workflow selected | Bounded evidence collection | Owner and checks known, or HITL |
| Executing | Scope and prerequisites satisfied | One sequential bounded write batch | Verification, HITL, or stop |
| Verifying | Batch complete | Risk-based checks and scoped diff | Complete, corrective batch, or HITL |
| Paused | One HITL case occurs | Return one decision request and wait | Valid matching human decision |
| Complete | Acceptance evidence collected | Final report only | New request |

Internal state names are implementation concepts. They MUST NOT become user-selectable modes. Internal process modes are defined separately in `PROCESS_MODES_SPEC.md` and are automatically selected.

## 6.1 Instruction object model

Domain Markdown under `ai/**` is structured as instruction objects. Each object owns one responsibility area, declares when it activates, lists required inputs, states `Must Not` boundaries, defines a compact workflow, and names required output evidence. Loaded objects guide the selected workflow only inside approved scope; they never grant authority, expand paths, or override Python contracts, root rules, or HITL.

## 7. Traceability

Recommended identifier chain:

`BUS-*` → `REQ-*`/`NFR-*` → `CHG-*` → `TASK-*` → `PHASE-*` → verification evidence.

Each downstream artifact MUST preserve applicable upstream IDs and identify any derived requirement.

## 8. Quality attributes

- Accuracy: decisions are evidence-backed and checks are honestly labeled.
- Speed: load only triggered references and stop discovery at a defined threshold.
- Safety: permanent protections and explicit capability gates remain central.
- Resumability: HITL and phased work continue from exact handoffs.
- Maintainability: one canonical source per rule, read live rather than copied.
