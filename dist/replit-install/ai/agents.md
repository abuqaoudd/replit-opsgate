# METCO Agent Coordination Instruction Object

Use these roles as a lightweight checklist, not separate permission sources. Run only roles relevant to the task.

## Responsibility

Own coordination guidance for decomposing complex work into relevant review roles, preserving phase boundaries, reusing handoffs, and serializing decisions and writes at ownership, contract, data, and phase boundaries.

## Activation

Use this object when a task spans multiple concerns, requires a phased handoff, needs parallel-safe read-only checks, or benefits from a lightweight role checklist. Role selection never grants authority and never replaces the routed primary skill.

## Inputs

- Selected internal mode, primary skill, approved scope, phase state, and loaded domain instruction objects.
- Current outcome, acceptance criteria, dependencies, cross-phase invariants, risks, and verification expectations.
- Previous handoff evidence, decisions, blockers, and pre-existing work.

## Must Not

- Simulate a large team, produce role-by-role prose when one concise record is enough, or use roles as permission sources.
- Start deferred phases, repeat verified discovery without scoped drift, or continue while HITL is paused.
- Serialize independent read-only work unnecessarily or parallelize writes across ownership/contract/data boundaries.

## Role Objects

| Role | Output |
|---|---|
| Scope guardian | Mode, paths, baseline, stop conditions; final scope check |
| Requirements analyst | Observable criteria, roles/scope, edge states |
| Architecture mapper | Ownership, consumers, reuse map, refactor classification |
| Creation reviewer | Reuse/extend/create evidence and destination |
| Frontend engineer | Typed, reusable, accessible client implementation |
| API engineer | Validated, authorized, layered backend implementation |
| Data/security reviewer | Identity, object scope, allowlists, queries, transactions, leakage |
| UI reviewer | Design-system reuse, hierarchy, responsive/accessibility states |
| QA verifier | Risk-based checks with honest results |
| Final reporter | Outcome, files, decisions, checks, risk, compliance |

## Workflow

- Bounded frontend: guardian → analyst/mapper → creation review if needed → frontend → UI/QA → guardian/report.
- Backend/data: guardian → analyst/mapper → creation review if needed → API → data/security → QA → guardian/report.
- Full stack: guardian → contract/requirements → backend/data/security → frontend/UI → integrated QA → guardian/report.
- Refactor: guardian → baseline/mapper/classification → one batch → reviewers/QA → repeat → guardian/report.
- Audit/debug: guardian → mapper/relevant reviewers → QA/evidence → report; no implementation when the requested outcome is read-only.
- Migration/seed: guardian → inventory/mapping → one data batch → API compatibility/security → data QA → report.

For each multi-step batch record outcome, allowed files, dependencies/contracts, risks, checks, rollback boundary, and result. Do not simulate a large team or produce role-by-role prose when one concise decision record is enough.

For complex changes, execute only the current authorized phase. Require the previous phase's explicit handoff evidence, preserve cross-phase invariants, and do not begin deferred consumer migration, cleanup, or destructive work early.

Reuse a current verified handoff instead of repeating discovery. Validate only its prerequisites and scoped file state, then continue. Run independent read-only role checks in parallel when safe; serialize decisions and writes at ownership, contract, data, and phase boundaries.

Select an internal mode and primary skill automatically for every phase from its actual outcome. HITL is not a process mode. Pause only when the current phase encounters an unknown next step, two materially correct answers with no evidence-based winner, or a self-made decision that would change scope. Return only the decision request from `replit.md`, stop the entire task, and wait for a matching `DECIDE` reply. Validate the reply and scoped project drift, then resume the exact blocked phase step without repeating completed work. Reuse the human answer in later phases only while its question, scope, and evidence remain unchanged.

## Output Evidence

Report the selected role objects, why they applied, which work was parallel-safe, which writes or decisions were serialized, reused handoff evidence, current phase boundary, blockers, and final scope compliance.
