---
name: metco-form-workflow
description: Build or repair a create/edit form, multi-step workflow, validation flow, dialog/drawer form, or mutation feedback experience in this project's frontend source root, with optional existing-backend integration. Use when form state, payload mapping, duplicate submission, errors, permissions, and accessibility are central.
---

# METCO Form Workflow

Automatically select internal mode `FORM_WORKFLOW_IMPLEMENTATION`. This selects procedure, not authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes, returns Gate Blocked (a deterministic gate needs authorization), or emits the required HITL decision request (a Judgment gate found genuine ambiguity). Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md` and `../../../ai/{metco,frontend,ui-ux,testing}.md`; add backend/security/database for server changes.
2. Define create/edit modes, actors, editable fields, initial values, transformations, validation sources, mutation contract, and success/cancel behavior.
3. Trace shared fields/form/dialog patterns, feature types/validation/service/hooks, backend validator/allowlist, and existing tests.
4. Reuse existing controls and schemas; complete creation gates before new form infrastructure.
5. Preserve input on recoverable failure, prevent duplicate submit, handle field/global/server/permission/conflict errors, and confirm destructive actions.
6. Verify keyboard/focus, labels/errors, responsive dialog/page behavior, payload allowlist, success refresh/navigation, and failure recovery.
7. Report field-to-payload mapping, ownership, reuse, and exact checks.

Stop for unauthorized contract/schema/package/config changes or guessed validation/business rules.
