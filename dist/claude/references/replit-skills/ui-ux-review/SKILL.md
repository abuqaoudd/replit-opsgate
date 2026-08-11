---
name: ui-ux-review
description: Audit or improve visible interfaces in this project's frontend source root for design-system reuse, hierarchy, density, forms, tables, complex builders, feedback states, responsiveness, accessibility, and role-aware actions. Use for UI-focused work; remain read-only for recommendations and implement changes only when explicitly requested.
---

# UI/UX Review

Automatically select internal mode `UI_UX_REVIEW`. This selects procedure; the user request determines whether writes are authorized.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{ui-ux,testing}.md`; add frontend for implementation and refactoring for consolidation.
2. Identify mode, user role, primary workflow, friction, exact paths, and measurable UI outcome.
3. Inspect existing shells, controls, forms, tables, dialogs, states, icons, tokens, and styles.
4. In explicitly requested implementation, complete reuse/creation gates and use established styling; during review-only work, do not edit.
5. Review hierarchy, action placement, density, terminology, relevant feedback/conflict states, and destructive safeguards.
6. Verify 375/768/1280px behavior, keyboard/focus, labels/names, semantics, contrast, and errors.
7. Report evidence and prioritized findings or exact changed behavior.

Stop for design-system replacement, packages/global config, unsupported contracts, or protected paths.
