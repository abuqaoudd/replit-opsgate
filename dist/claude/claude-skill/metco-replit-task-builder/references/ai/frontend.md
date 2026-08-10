# METCO Frontend Instruction Object

Applies to approved work inside this project's frontend source root (see `replit.md` §2 - the active profile's `frontend_root`, or the task's explicitly authorized frontend path when no profile applies).

## Responsibility

Own frontend implementation guidance for routes, pages, feature components, hooks, client services, typed UI state, accessibility, responsive behavior, and design-system reuse.

## Activation

Use this object only after routing selects a frontend-visible workflow or a phase whose immediate outcome changes this project's frontend source root. Selection of this object does not authorize backend, schema, package, generated, protected, or cross-contract changes.

## Inputs

- Observable user-facing outcome, affected roles, and acceptance criteria.
- Exact approved write paths and minimum read-only paths.
- Existing route, page, feature owner, API/data contract, and direct consumers.
- Applicable UI states, preserved behavior, and verification expectations.

## Must Not

- Treat client visibility as security enforcement.
- Create a parallel design system, duplicate feature tree, or replacement route family.
- Change public API/data contracts, backend authorization, packages, generated files, or protected paths without explicit capability authority.
- Add new shared units before recording reuse and creation-gate evidence.

## Ownership and placement

- `pages/**`: route parameters, permissions, feature hooks, composition, page-level state, and feedback-state selection only.
- `components/ui/**`: generic cross-feature controls; no feature API/business rules.
- `components/layout/**`: shells, navigation, and shared layout.
- `features/<feature>/**`: feature components, hooks, services/API, types, validation, and utilities.
- `hooks/**`: genuinely cross-feature hooks.
- `lib/**`: shared clients and pure cross-feature utilities, not feature dumping.

Follow existing structure; do not create parallel `new`, `v2`, `final`, or temporary trees.

## Reuse gate

Search the owning feature, shared UI/layout/report components, features, hooks, lib, and relevant pages by names, labels, props, primitives, classes, endpoints, hooks, and behavior. Decide in order: reuse → compose/configure → extend generically → merge → feature wrapper → feature-owned unit → shared unit.

Before creating, use the root creation gate. Text, columns, labels, icons, or data differences alone do not justify a new table, form, dialog, state, API wrapper, or design pattern.

## React and TypeScript

- Declare components at module scope; keep one coherent responsibility.
- Keep business calculations and complex mutation flows out of JSX.
- Use named handlers, early returns, pure helpers, stable keys, and correct effect dependencies/cleanup.
- Do not use effects for render-time derivation or duplicate prop/server state.
- Use the narrowest state location; do not introduce a state library.
- Reuse exact domain/API types; no `any`, suppression comments, broad casts, duplicate interfaces, or contract renames.
- Review files over 400 lines and functions over 70 lines for mixed responsibility; decompose when it improves ownership, not merely line count.

## Data and styling

Use existing API clients/services/hooks; do not scatter requests through presentation code. Preserve routes and contracts. Client visibility never replaces backend authorization.

Use existing tokens, utilities, variants, CSS variables, icons, and breakpoints. No static inline styles, large style objects, arbitrary repeated values/colors, second styling system, or broad global/`!important` fixes. Allow a documented runtime-calculated inline value only when existing styling cannot express it.

## Workflow components

Forms: reuse fields/validation, preserve input after recoverable failure, prevent duplicate submit, allowlist/transform payloads, and handle create/edit, validation, pending, success, failure, permission, cancel, and destructive confirmation.

Tables/lists: reuse sorting/filter/search/pagination/status/action patterns; preserve stable ordering, bounded pagination, selection, nested-control events, keyboard, responsive, empty, and no-results states.

## Workflow

1. Confirm approved scope, owner, direct consumers, and current behavior.
2. Search for reusable UI, layout, hooks, services, validation, types, and state patterns.
3. Record reuse, extension, or creation evidence before adding units.
4. Implement the smallest complete typed frontend batch inside the selected owner.
5. Verify applicable roles, UI states, responsive behavior, keyboard/accessibility, contracts, and scoped tests.

## Output Evidence

Verify ownership/reuse evidence, correct placement, strict types, no duplicate framework/nested component/unjustified inline style, relevant loading/empty/error/permission/pending/success/conflict states, routes/roles/contracts, responsive widths, keyboard/accessibility, and scoped tests.
