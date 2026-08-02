# METCO UI/UX Instruction Object

Applies to visible work in `artifacts/metco/src/**`.

## Responsibility

Own visible experience guidance for design-system reuse, interaction hierarchy, feedback states, responsive behavior, accessibility, destructive safeguards, and UI review evidence.

## Activation

Use this object when a selected frontend workflow changes visible UI, layout, interaction, content, feedback states, responsive behavior, or accessibility. It complements the frontend object and does not authorize new routes, backend contracts, or design-system replacement.

## Inputs

- User-visible outcome, affected roles, current UI patterns, design-system primitives, viewport expectations, and accessibility requirements.
- Approved paths, preserved behavior, applicable feedback states, and direct user flows.
- Existing shell/header, controls, tables, forms, dialogs, icons, tokens, spacing, typography, color, and breakpoints.

## Must Not

- Create a second design system, use arbitrary page-local styling, apply broad global fixes, or redesign unrelated surfaces.
- Use production emojis, unrelated visual effects, mixed styling systems, or static inline styles.
- Hide unavailable actions without preserving accessible affordances and permission feedback where applicable.

## Design system first

Inspect and reuse existing shell/header, buttons/actions, form controls, filters/search, tables/pagination, dialogs/drawers, feedback states, badges/cards/tabs/menus, icons, tokens, spacing, typography, color, radius, shadow, and breakpoints. Do not create a second design system or page-local copy.

Preserve established METCO visual identity and icon library. No production emojis, unrelated gradients/glass/neon, excessive decoration, mixed styling systems, arbitrary values, static inline styles, or global fixes for local problems.

## Interaction

- Keep one clear primary action and predictable secondary/destructive placement.
- Favor compact scannability, grouped controls, business language, and progressive disclosure.
- Distinguish empty data from filtered no-results.
- Preserve input after recoverable failure; prevent duplicate submission and accidental destructive actions.
- Consider loading, refresh, empty, no-results, recoverable error/retry, permission, pending, success, conflict/stale, and confirmation only when applicable.
- For complex builders, separate navigation, selection, work surface, and properties; keep unsaved-work protection and non-drag alternatives.

## Responsive and accessible

Verify around 375px, 768px, and 1280px: no unintended overflow, reachable actions, scrolling dialogs, predictable filter/table behavior, safe wrapping, and unobscured content.

Use semantic controls, visible labels, accessible names, keyboard operation, visible focus, logical order, dialog focus management, table semantics, error associations, readable contrast, and non-color status cues.

## Workflow

1. Inspect existing UI patterns and pick reuse, configuration, or narrow extension before creation.
2. Preserve METCO visual identity, hierarchy, density, interaction placement, and business language.
3. Cover applicable loading, empty, no-results, error/retry, permission, pending, success, conflict, and confirmation states.
4. Verify responsive behavior around 375px, 768px, and 1280px.
5. Verify semantic controls, labels, focus, keyboard flow, table/dialog semantics, contrast, and non-color status cues.

## Output Evidence

Confirm reuse, hierarchy/density, role-relevant actions, applicable feedback states, responsive behavior, keyboard/accessibility, destructive safeguards, and no unrelated redesign.
