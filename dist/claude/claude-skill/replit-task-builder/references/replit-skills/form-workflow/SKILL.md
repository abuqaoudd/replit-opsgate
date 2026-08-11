---
name: form-workflow
description: Build or repair a create/edit form, multi-step workflow, validation flow, dialog/drawer form, or mutation feedback experience in this project's frontend source root, with optional existing-backend integration. Use when form state, payload mapping, duplicate submission, errors, permissions, and accessibility are central.
---

# Form Workflow

Automatically select internal mode `FORM_WORKFLOW_IMPLEMENTATION`. This selects procedure, not authority.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{frontend,ui-ux,testing}.md`; add backend/security/database for server changes.
2. Define create/edit modes, actors, editable fields, initial values, transformations, validation sources, mutation contract, and success/cancel behavior.
3. Trace shared fields/form/dialog patterns, feature types/validation/service/hooks, backend validator/allowlist, and existing tests.
4. Reuse existing controls and schemas; complete creation gates before new form infrastructure.
5. Preserve input on recoverable failure, prevent duplicate submit, handle field/global/server/permission/conflict errors, and confirm destructive actions.
6. Verify keyboard/focus, labels/errors, responsive dialog/page behavior, payload allowlist, success refresh/navigation, and failure recovery.
7. Report field-to-payload mapping, ownership, reuse, and exact checks.

Stop for unauthorized contract/schema/package/config changes or guessed validation/business rules.
