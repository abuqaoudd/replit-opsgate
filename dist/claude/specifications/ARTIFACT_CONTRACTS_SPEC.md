# Artifact Contracts Specification

Specification version: 6

`compile_artifact_prompt()` and `compile_replit_prompt()` in `tools/opsgate_prompts.py` emit a condensed, deliverable-specific "Required Output" checklist derived from this spec for the routed skill to build the actual artifact from - not a verbatim restatement of every required section below, since a generation prompt is bounded in length while the artifact it produces is not. A shorter or differently-ordered checklist is expected and is not by itself spec drift. The stable-ID prefixes this spec assigns per deliverable (`BUS-RULE-*`, `BUS-CAP-*`, `REQ-*`, `NFR-*`, `FIND-*`, `TASK-*`, `CHG-*`) are the one part that MUST still appear verbatim in the compiled checklist wherever this spec requires stable IDs for that deliverable - they are not optional generation detail.

## 1. Shared contract

Every artifact MUST:

- identify its title, status, owner or audience, version, date, and authoritative sources;
- state purpose, included scope, excluded scope, assumptions, dependencies, and constraints;
- use stable IDs for traceable statements;
- separate confirmed facts from proposals and unresolved questions;
- contain measurable acceptance or review evidence;
- avoid inventing business rules, contracts, permissions, or data behavior;
- omit irrelevant sections rather than filling them with generic prose.

## 2. Business file

Purpose: define the business need before solution design.

Required sections:

1. document control and source authority;
2. executive summary and problem statement;
3. desired business outcomes and measurable success;
4. actors, stakeholders, and responsibilities;
5. current-state and target-state workflows;
6. scope, non-scope, dependencies, and constraints;
7. business rules as `BUS-RULE-*`;
8. capabilities as `BUS-CAP-*`;
9. acceptance outcomes and operational measures;
10. risks, assumptions, decisions, and open questions;
11. traceability table.

The business file MUST NOT prescribe implementation architecture unless it is an approved business constraint.

For module audit updates, the business file MUST identify the audited module, the existing business MD link or path, inspected evidence, confirmed behavior, outdated or missing requirements, conflicting evidence, unsupported claims, open questions, and the final requirement changes. It MUST preserve valid requirements, retire or change obsolete ones with rationale, add missing business requirements, and remain implementation-neutral.

## 3. Implementation specification

Purpose: make behavior implementable and verifiable.

Required sections:

1. document control and governing business/change IDs;
2. system context and affected boundaries;
3. actors, permissions, tenant/object scope;
4. functional requirements as `REQ-*`;
5. non-functional requirements as `NFR-*`;
6. user journeys, state transitions, and edge cases;
7. UI states and accessibility expectations when applicable;
8. API operations, request/response/error contracts when applicable;
9. data entities, validation, ownership, lifecycle, and migration effects;
10. security, privacy, logging, and auditability;
11. compatibility, rollout, rollback, and observability;
12. test matrix and acceptance criteria;
13. requirement-to-source and requirement-to-test traceability;
14. unresolved decisions eligible for HITL.

Each functional requirement SHOULD include actor, preconditions, trigger, behavior, result, failure behavior, and verification.

For delta specifications, the spec MUST identify the module, business documentation link or path, existing spec link or path, comparison method, date, and filename. It MUST document only new, changed, removed, or newly clarified requirements; preserve unchanged approved behavior by reference; follow the existing spec files' metadata format, structure, terminology, and writing style; and name the file as `spec-[module-name]-YYYY-MM-DD.md`, for example `spec-roles-2026-07-26.md`.

## 4. Audit

Purpose: compare evidence to an explicit baseline without implementing fixes.

Required sections:

1. audit objective, baseline, scope, exclusions, and method;
2. evidence inventory and limitations;
3. executive conclusion;
4. findings with stable `FIND-*` IDs;
5. severity, confidence, affected requirement, evidence, impact, and recommendation per finding;
6. compliant controls and positive evidence;
7. coverage gaps and unverified claims;
8. prioritized remediation sequence;
9. traceability from finding to evidence and source requirement.

Audits MUST distinguish absence of evidence from evidence of absence. Checks not run MUST be labeled `NOT RUN`.

## 5. Task backlog

Purpose: turn approved requirements and changes into executable, dependency-aware work.

Each task MUST contain:

- `TASK-*` ID and title;
- source requirement/change IDs;
- observable outcome;
- exact included and excluded scope;
- prerequisites and dependencies;
- acceptance criteria;
- implementation notes without prescribing unnecessary internals;
- verification evidence;
- rollback or recovery boundary;
- completion evidence and handoff;
- internally routed skill family, if helpful for automation—not as a user-selected field.

Complex work MUST be split at contract, data, ownership, deployment, or rollback boundaries.

## 6. Change or improvement record

Purpose: control a proposed deviation from an approved baseline.

Required sections:

1. `CHG-*` ID, status, owner, date, and affected baselines;
2. problem/opportunity and evidence;
3. proposed behavior and non-goals;
4. requirement additions, changes, and removals;
5. impact by business, UX, API, data, security, operations, and testing;
6. compatibility and migration strategy;
7. risk, rollback, and observability;
8. options considered and decision rationale;
9. implementation sequence and acceptance;
10. traceability and approvals.

The record MUST make changed requirements explicit; it MUST NOT silently rewrite the original baseline.

## 7. Replit prompt

Purpose: authorize and guide only the current executable batch.

Required sections:

- outcome;
- instructions to route through installed skills automatically;
- exact scope and permanent protections;
- task-specific decisions and explicit authorizations;
- acceptance criteria;
- bounded inspection and ownership evidence;
- execution steps;
- verification matrix;
- HITL rule;
- final report.

Internal routing fields MUST NOT be exposed as user inputs.
