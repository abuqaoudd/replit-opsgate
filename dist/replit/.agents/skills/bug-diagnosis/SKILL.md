---
name: bug-diagnosis
description: Diagnose a frontend, backend, data, permission, or integration defect from symptoms, logs, reproduction steps, or failing tests. Use for evidence-first root-cause analysis without writes, or for a tightly bounded fix when the user explicitly requests implementation after diagnosis.
---

# Bug Diagnosis

Automatically select internal mode `BUG_DIAGNOSIS`. This selects procedure, not write authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes, returns Gate Blocked (a deterministic gate needs authorization), or emits the required HITL decision request (a Judgment gate found genuine ambiguity). Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, `../../../ai/{testing}.md`, and only affected domain files.
2. Remain read-only unless a fix is explicitly requested. Define symptom, expected behavior, environment, actors/data, reproduction, and exact approved paths.
3. Capture scoped baseline. Trace entry point → state/contract → service → validation/authorization → persistence → response/UI.
4. Form ranked hypotheses; run the cheapest discriminating safe check for each. Separate cause, trigger, and visible symptom.
5. Record evidence, affected scope, regression risk, and smallest safe remedy. Do not edit in audit-only mode.
6. If implementation is authorized, change only the proven owner and add a regression check; rerun reproduction plus adjacent failure paths.
7. Report reproduced/not reproduced, root cause confidence, evidence, fix if authorized, and remaining unknowns.

Stop when reproduction needs production/unknown data, protected paths, secrets, destructive actions, or a contract decision.
