# METCO business file generation

Act as a senior business analyst. Create or update **[business file name]** for **[initiative/product/process]**.

## Inputs

- Business request: [request]
- Source evidence: [interviews, current files, policies, metrics, screenshots]
- Stakeholders and users: [roles]
- Known constraints: [budget, timeline, policy, technology, operations]
- Existing file to preserve or revise: [path or none]
- Module audit request: [module name, existing business MD link/path, module scope, or none]

Treat source files as evidence, not permission to invent missing policy. Mark material unknowns as `OPEN QUESTION` and state their decision owner.

## Module audit update

When the request is to check and audit a module before updating its business file, audit the full **[module name] module** against current product behavior, source evidence, related files, and existing documentation. Then update the business file MD for the **[module name]** module at **[business MD link/path]**.

Capture:

- Module scope: routes, screens, APIs, tables, workflows, permissions, reports, jobs, and external touchpoints included in the audit.
- Existing business file: path or link to preserve, revise, or replace.
- Evidence inspected: files, screenshots, policies, current app behavior, logs, user notes, and related documentation.
- Audit result: confirmed behavior, missing requirements, outdated requirements, conflicting evidence, unsupported claims, and open questions.
- Update goal: new module business file, revised existing file, gap correction, or full audit refresh.

Preserve still-valid business requirements, change or retire outdated requirements, add missing requirements, mark unsupported claims as `OPEN QUESTION`, and keep the file implementation-neutral.

## Deliverable

Write a decision-ready business file containing:

1. Document control: title, ID, version, status, owner, approvers, date, revision history, and authoritative sources.
2. Executive summary, desired business outcome, and decision requested.
3. Current problem, supporting evidence, affected users, frequency, severity, and cost/risk of inaction.
4. Target operating outcome and measurable value hypothesis.
5. In-scope capabilities, out-of-scope boundaries, and explicitly unchanged behavior.
6. Stakeholders, user groups, responsibilities, decision owners, and approval owners.
7. Business capabilities (`BUS-CAP-*`) and atomic business requirements (`BUS-REQ-*`).
8. Business rules (`BUS-RULE-*`), roles, record/tenant scope, approvals, exceptions, and escalation.
9. Current-state and target-state journeys, including alternate, rejection, failure, recovery, and handoff paths.
10. Business data concepts, ownership, sensitivity, retention expectations, reporting, and audit needs; do not design schema here.
11. Assumptions, constraints, dependencies, risks, mitigations, and operational readiness.
12. Success measures with baseline, target, measurement method, owner, and observation window.
13. Business acceptance outcomes and evidence required for approval.
14. Decisions, recommendations, open questions, and traceability linking evidence to requirements.

## Requirement record

For every `BUS-REQ-*`, include:

| Field | Content |
|---|---|
| Statement | One implementation-neutral required outcome |
| Rationale | Business value or risk addressed |
| Actors | Roles affected |
| Preconditions | Business conditions required |
| Rule references | Applicable `BUS-RULE-*` IDs |
| Priority | Must/Should/Could with rationale |
| Acceptance outcome | Observable business evidence |
| Source | Exact evidence reference |
| Status | Proposed/Approved/Changed/Retired |

## Workflow and traceability

For each material workflow, document trigger, actor, prerequisites, normal steps, decisions, exceptions, rejection, recovery, completion evidence, ownership transfer, and downstream reporting.

Trace evidence → capability → requirement → business rule → acceptance outcome. Link every open question to affected IDs and a decision owner. Link every changed or retired requirement to its replacement or rationale.

## Quality rules

- Separate facts, decisions, assumptions, and recommendations.
- Make each requirement atomic, testable, implementation-neutral, and uniquely identified.
- Resolve duplicate or conflicting source statements explicitly.
- Do not invent dates, owners, permissions, business rules, integrations, or compliance claims.
- Preserve still-valid content from an existing file and identify changed or retired requirements.
- Use concise tables where they improve comparison or traceability.
- Do not embed solution architecture, database tables, component names, or implementation tasks unless they are approved constraints.
- State whether each metric is leading, lagging, quality, compliance, or operational.

## Final check

Confirm coverage of the requested outcome, source traceability, measurable acceptance, unresolved decisions, exclusions, and contradictions. Return only the polished business file unless asked for commentary.
