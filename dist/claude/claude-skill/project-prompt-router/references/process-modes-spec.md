# Internal Process Modes Specification

Specification version: 6

## 1. Purpose

Internal modes provide deterministic process selection, reporting, and validation across any project using this engine. Routers and skills select them automatically. Users describe outcomes and scope; they do not need to know, choose, or type mode identifiers.

## 2. Rules

- `MODE-001`: Every routed process MUST select exactly one primary internal mode.
- `MODE-002`: Selection MUST be automatic from outcome, requested deliverable, domain, write surface, and explicit authorization.
- `MODE-003`: A mode selects procedure only; it MUST NOT grant authority.
- `MODE-004`: User-facing request templates MUST NOT contain a required `Mode:` field.
- `MODE-005`: Runtime reports MAY state the selected mode for traceability.
- `MODE-006`: A phase MUST select its own mode from that phase’s actual outcome.
- `MODE-007`: Supporting concerns are loaded as references, not additional primary modes.
- `MODE-008`: HITL is never a mode, level, gate, or risk classification.
- `MODE-009`: If two modes remain materially correct after routing rules, use HITL case 2.
- `MODE-010`: If no mode is applicable because required authority is absent, stop at the capability gate.
- `MODE-011`: Never emit legacy v5.4 mode labels; translate old inputs to the corresponding internal mode and capability evidence.

Obsolete labels: `NORMAL_IMPLEMENTATION`, `APPROVED_ARCHITECTURE_REFACTOR`, `AUDIT_ONLY`, `INSTRUCTION_MAINTENANCE`, `DATABASE_SCHEMA_MIGRATION`, and `DATA_SEEDING`.

## 3. Artifact-generation modes

| Mode | Select when the immediate deliverable is | Primary contract |
|---|---|---|
| `BUSINESS_DEFINITION` | Business need, value, actors, scope, rules, success | Business file |
| `IMPLEMENTATION_SPECIFICATION` | Implementation-ready behavior, contracts, states, data, NFRs | Specification |
| `EVIDENCE_AUDIT` | Findings against a baseline without fixes | Audit |
| `DELIVERY_BACKLOG` | Dependency-aware tasks from approved sources | Task backlog |
| `CHANGE_CONTROL` | Amendment or improvement to an approved baseline | Change record |
| `PROMPT_INTAKE` | Structured collection of missing request data | Request form |
| `REPLIT_PROMPT_BUILD` | One executable bounded Replit prompt | Bounded prompt |
| `REPLIT_PHASE_PLAN` | Sequential plan plus only the next executable phase | Phased prompt |

## 4. Replit execution modes

| Mode | Observable process | Primary skill |
|---|---|---|
| `FRONTEND_IMPLEMENTATION` | React/client feature or defect implementation | `frontend-development` |
| `API_IMPLEMENTATION` | API route, service, repository, or backend behavior | `api-server-development` |
| `FULL_STACK_IMPLEMENTATION` | Coordinated client and Replit backend outcome in one authorized phase | `full-stack-feature` |
| `AUTH_PERMISSION_IMPLEMENTATION` | Authentication, authorization, tenant, role, or object-scope behavior | `auth-permission-workflow` |
| `FORM_WORKFLOW_IMPLEMENTATION` | Form state, validation, mutations, save/cancel, and errors | `form-workflow` |
| `TABLE_REPORTING_IMPLEMENTATION` | Tables, filters, sorts, pagination, exports, or reporting | `table-reporting-workflow` |
| `FRONTEND_ARCHITECTURE_REFACTOR` | Broad ownership, reuse, decomposition, or consolidation | `frontend-architecture-refactor` |
| `DATABASE_SCHEMA_EVOLUTION` | Schema, ERD mapping, migration, index, backfill, compatibility | `database-schema-migration` |
| `NONPRODUCTION_DATA_SEEDING` | Deterministic development/test seed data | `data-seeding` |
| `BUG_DIAGNOSIS` | Unknown defect cause, reproduction, or evidence-only root cause | `bug-diagnosis` |
| `PERFORMANCE_OPTIMIZATION` | Measured latency, render, query, memory, or bundle bottleneck | `performance-optimization` |
| `UI_UX_REVIEW` | Visual, interaction, responsive, accessibility, or usability review | `ui-ux-review` |
| `SAFE_VERIFICATION` | Read-only QA, regression, security, compliance, or release evidence | `safe-verification` |
| `INSTRUCTION_SYSTEM_MAINTENANCE` | `replit.md`, `ai/**`, or `.agents/skills/**` changes | `instruction-maintenance` |

## 5. Supporting domain concerns

These concerns modify checks and references but do not replace the primary mode unless their process is the immediate outcome:

- security and sensitive data;
- database access without schema change;
- accessibility and responsive behavior;
- testing and verification;
- refactor/move/delete risk;
- observability and error handling;
- compatibility and rollback;
- multi-phase coordination.

## 6. Automatic selection algorithm

1. Identify the immediate deliverable.
2. Determine whether the task is artifact generation or Replit execution.
3. Determine the current phase’s observable result and actual write surface.
4. Select the most specialized matching mode.
5. Select the mapped primary skill.
6. Load supporting domain instruction objects.
7. Check capability gates and explicit authorization.
8. Determine bounded or phased execution internally.
9. Record the selected mode in internal planning and final reporting.

## 7. Specificity rules

- Form behavior selects `FORM_WORKFLOW_IMPLEMENTATION` over general frontend.
- Table/report behavior selects `TABLE_REPORTING_IMPLEMENTATION` over general frontend.
- Permission behavior selects `AUTH_PERMISSION_IMPLEMENTATION` even when it spans UI and API.
- A schema phase selects `DATABASE_SCHEMA_EVOLUTION`; a later consumer phase selects its own client or backend mode.
- A no-write validation phase selects `SAFE_VERIFICATION`.
- Full-stack applies only when both surfaces belong to the current authorized phase.
- Instruction changes always select `INSTRUCTION_SYSTEM_MAINTENANCE`.

## 8. Expansion

Add a new mode only when an outcome has a distinct workflow, evidence contract, and verification strategy not covered by an existing mode. A new mode requires:

1. a specification update;
2. a scenario skill or explicit mapping to an existing skill;
3. routing rules;
4. capability-gate analysis;
5. forward tests;
6. distribution-copy validation.
