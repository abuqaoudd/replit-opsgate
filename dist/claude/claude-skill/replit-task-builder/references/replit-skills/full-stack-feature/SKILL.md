---
name: full-stack-feature
description: Deliver a bounded feature spanning this project's backend and frontend source roots while preserving the existing API contract. Use for coordinated backend validation/authorization plus frontend consumption, role-aware UI, integrated states, and end-to-end verification; not schema changes unless separately authorized.
---

# Full-Stack Feature

Automatically select internal mode `FULL_STACK_IMPLEMENTATION`. This selects procedure, not authority.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{backend,database,security,frontend,ui-ux,testing,agents}.md`.
2. Define actors, record scope, endpoint contract, frontend flow, exact paths, capability gates, and acceptance criteria.
3. Capture separate frontend/backend baselines. Trace current contract and consumers before editing.
4. Implement backend validation, authorization, service/repository behavior, and tests first; preserve the response shape.
5. Update the owning frontend service/hook, types, callers, and UI using reuse/creation gates.
6. Verify artifacts separately, then success/failure/permission/conflict integrated flows and responsive/accessibility states.
7. Report contract decisions, file ownership, exact checks, and remaining cross-artifact risk.

Stop for generated-contract or schema changes, protected systems, packages/config, or an unresolved breaking API decision.
