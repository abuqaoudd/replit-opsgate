---
name: auth-permission-workflow
description: Implement or audit authentication, role permissions, object/tenant ownership, assignment scope, protected mutations, route visibility, or sensitive-field filtering across the Replit backend and frontend. Use when authorization correctness is the primary risk.
---

# Auth and Permission Workflow

Automatically select internal mode `AUTH_PERMISSION_IMPLEMENTATION`. This selects procedure, not authority.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{backend,database,security,frontend,testing}.md`; omit frontend when backend-only.
2. Determine read-only review versus explicitly requested implementation from the user outcome; define actor × action × resource-scope matrix and expected error-information behavior.
3. Trace identity middleware, permission utilities, service/repository scope, response mapping, frontend guards/actions, and tests.
4. Enforce server-derived identity, action permission, object/tenant scope, allowed transition, field allowlists, and filtered output.
5. Keep frontend controls role-aware but never treat hidden UI as enforcement.
6. Verify unauthenticated, allowed role, denied role, wrong object/tenant, stale transition, forged identity/ownership fields, and sensitive-field leakage.
7. Report the matrix and exact evidence without exposing sensitive data.

Stop for bypasses, secret/config changes, protected identity systems, or invented permission rules.
