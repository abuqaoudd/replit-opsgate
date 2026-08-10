---
name: api-server-development
description: Implement or debug bounded Replit API routes, middleware, validation, services, repositories, authorization, errors, logging, and persistence in this project's backend source root. Use for backend-only endpoint behavior; use a more specific auth, debugging, performance, full-stack, migration, or seeding skill when that is the primary scenario.
---

# API Server Development

Automatically select internal mode `API_IMPLEMENTATION`. This selects procedure, not authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes, returns Gate Blocked (a deterministic gate needs authorization), or emits the required HITL decision request (a Judgment gate found genuine ambiguity). Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{backend,testing}.md`; add database/security references when triggered.
2. State endpoint, contract, roles/object scope, exact paths, capability gates, and stop conditions.
3. Capture scoped Git status/diff. Trace route → middleware/validation → service → repository → mapper/tests.
4. Preserve method/path/fields/status/response/auth. Complete the creation gate before adding a unit.
5. Validate input and allowlist fields. Derive identity server-side and enforce object scope.
6. Use existing bounded query, transaction, error, and redacted-log patterns.
7. Verify applicable success, malformed/unknown input, unauthenticated, forbidden, not-found, conflict/stale, duplicate, rollback, and sensitive-field cases.
8. Review scoped diff and report decisions and exact results.

Stop for protected access, packages/config, generated contracts, unauthorized schema/migration/seed changes, production data, or breaking contracts.
