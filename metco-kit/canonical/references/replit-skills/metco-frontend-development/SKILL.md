---
name: metco-frontend-development
description: Implement or debug a bounded METCO React/TypeScript page, component, hook, route, state, style, or client behavior in artifacts/metco/src. Use for ordinary frontend-only work requiring reuse discovery, correct ownership, strict typing, established styling, UI states, and scoped verification; not broad architecture refactors.
---

# METCO Frontend Development

Automatically select internal mode `FRONTEND_IMPLEMENTATION`. This selects procedure, not authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes or emits the required HITL decision request. Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md` and `../../../ai/{metco,frontend,ui-ux,testing}.md`.
2. State behavior, roles, exact paths, expected owner, capability gates, and stop conditions.
3. Capture scoped baseline. Trace feature → service/API → types/utilities/validation → hooks → callers/props → component.
4. Search shared/feature patterns; prefer reuse, composition, and existing props. Complete the creation gate before adding a unit.
5. Keep pages orchestration-focused, feature logic feature-owned, requests in existing boundaries, types strict, and styling consistent.
6. Handle only applicable loading/empty/error/permission/pending/success/conflict states.
7. Verify function, UI, architecture, 375/768/1280px, keyboard, accessibility, and regression risks using narrow checks.
8. Review scoped diff and report reuse/ownership decisions and exact results.

Stop for protected paths, packages/config, generated contracts, schema/migrations/seeds, or unsupported API changes.
