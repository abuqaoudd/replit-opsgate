---
name: metco-auth-permission-workflow
description: Implement or audit METCO authentication, role permissions, object/tenant ownership, assignment scope, protected mutations, route visibility, or sensitive-field filtering across the Replit backend and frontend. Use when authorization correctness is the primary risk.
---

# METCO Auth and Permission Workflow

Automatically select internal mode `AUTH_PERMISSION_IMPLEMENTATION`. This selects procedure, not authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes or emits the required HITL decision request. Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md` and `../../../ai/{metco,backend,database,security,frontend,testing}.md`; omit frontend when backend-only.
2. Determine read-only review versus explicitly requested implementation from the user outcome; define actor × action × resource-scope matrix and expected error-information behavior.
3. Trace identity middleware, permission utilities, service/repository scope, response mapping, frontend guards/actions, and tests.
4. Enforce server-derived identity, action permission, object/tenant scope, allowed transition, field allowlists, and filtered output.
5. Keep frontend controls role-aware but never treat hidden UI as enforcement.
6. Verify unauthenticated, allowed role, denied role, wrong object/tenant, stale transition, forged identity/ownership fields, and sensitive-field leakage.
7. Report the matrix and exact evidence without exposing sensitive data.

Stop for bypasses, secret/config changes, protected identity systems, or invented permission rules.
