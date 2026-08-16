---
name: table-reporting-workflow
description: Build or improve operational tables, lists, dashboards, filters, search, sorting, pagination, row actions, summaries, or report screens. Use when bounded query behavior, role-scoped data, stable client state, responsive presentation, and empty/no-results/error states require coordinated design.
---

# Table and Reporting Workflow

Automatically select internal mode `TABLE_REPORTING_IMPLEMENTATION`. This selects procedure, not authority.

1. Read `../../../replit.md` and the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, relevant `../../../ai/{frontend,ui-ux,testing,backend,database,security}.md` files.
2. Define columns/metrics, actors and data scope, filters, sort allowlist/default, pagination, actions, export limits if already supported, and all observable states.
3. Trace shared table/report components, URL/query state, feature service/hook/types, endpoint filters/sorts, repository bounds, and tests.
4. Reuse the established table/filter/pagination/action architecture; do not build a page-local framework.
5. Enforce server-side scope and bounded allowlisted query behavior; preserve stable metadata and response shapes.
6. Verify data, empty versus no-results, invalid filters, sort/pagination boundaries, nested actions, roles, loading/error/retry, 375/768/1280px, and keyboard/table semantics.
7. Report query/UI contracts, reuse, and exact evidence.

Stop for new export dependencies, unbounded data access, schema changes, or protected data sources.
