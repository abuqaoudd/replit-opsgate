# Audit

Act as a senior independent reviewer. Audit **[artifact/system/process]** against **[business file, specification, policy, acceptance criteria, or standard]**.

Write access: none

Route this request automatically through the evidence-audit contract. For a Replit code audit, select the read-only verification or diagnosis skill from the requested outcome. Do not ask the user to choose a mode or skill.

## Instruction objects

Identify the read-only instruction object set before judging compliance:

| Object | Why loaded | Evidence inputs | Boundary |
|---|---|---|---|
| `[Audit/DomainInstructionObject]` | [audit dimension] | [approved evidence] | read-only |
| `VerificationInstructionObject` | check labeling and coverage | requirements, risks, inspected evidence | no writes or unsafe services |

Use object responsibilities and `Output Evidence` sections as audit criteria only when they apply to the approved scope.

## Scope

- Approved inspection scope: [exact files/modules/documents/flows]
- Exclusions and protected areas: [list]
- Evidence available: [files, tests, logs, screenshots, metrics]
- Audit dimensions: [requirements, correctness, security, data, UI/UX, performance, maintainability]
- Risk scale: `CRITICAL / HIGH / MEDIUM / LOW`

Do not change files, broaden the scope, infer an unobserved pass, or inspect protected locations.

## Method

1. Establish the governing requirements and current-state evidence.
2. Build a traceability checklist before judging compliance.
3. Test the highest-risk claims with the narrowest safe evidence.
4. Separate confirmed findings, risks, observations, and evidence gaps.
5. Check contradictions, omissions, stale requirements, and unverifiable acceptance criteria.
6. Label each check `PASSED`, `FAILED`, or `NOT RUN`; explain every `NOT RUN`.

## Finding format

For each actionable finding include:

- ID and concise title.
- Severity and confidence.
- Status: confirmed, conditional, evidence gap, or accepted risk.
- Governing requirement or expected behavior.
- Exact evidence and location.
- Reproduction or verification method.
- User/business/technical impact.
- Affected actors, data, contracts, and scope.
- Root cause when supported; otherwise label the cause unconfirmed.
- Smallest recommended remediation.
- Verification needed after remediation.
- Any exact question that matches one of the three HITL cases; HITL is separate from internal process modes.

## Coverage and severity

For every governing requirement record:

| Requirement | Evidence inspected | Result | Finding IDs | Confidence | Limitation |
|---|---|---|---|---|---|

Use `PASSED`, `FAILED`, or `NOT RUN`. A pass requires direct evidence. A missing test is not automatically a product defect; report the exact assurance gap.

- `CRITICAL`: active severe safety, security, privacy, integrity, or continuity exposure.
- `HIGH`: likely material impact, major contract violation, or broad user blockage.
- `MEDIUM`: bounded functional, operational, accessibility, performance, or maintainability risk.
- `LOW`: limited impact or hardening opportunity supported by an explicit standard.

State likelihood and impact separately when severity could be disputed.

Do not report a style preference as a defect unless it violates an explicit standard or creates measurable risk.

## Report

Return:

1. Executive summary and audit opinion.
2. Scope, exclusions, evidence, and limitations.
3. Requirement coverage table.
4. Findings ordered by severity, then confidence.
5. Checks with `PASSED`, `FAILED`, and `NOT RUN`.
6. Prioritized remediation backlog with dependency, owner, acceptance evidence, and recovery note.
7. Positive controls and compliant behavior worth preserving.
8. Instruction object coverage, open decisions, residual risk, and recommended next artifact or Replit process.
