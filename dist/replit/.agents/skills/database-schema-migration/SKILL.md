---
name: database-schema-migration
description: Implement an explicitly authorized Replit schema migration, ERD mapping, normalization, relationship/index change, backfill, compatibility switch, or migration verification. Use only with an approved target mapping, named established schema/migration paths, non-production environment, phased expand/backfill/validate/contract work, and rollback evidence.
---

# Database Schema Migration

Automatically select internal mode `DATABASE_SCHEMA_EVOLUTION`. This selects procedure; explicit authority and environment guards remain required.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{database,backend,security,testing,agents}.md`.
2. Require explicit authorization for the `schema_migration_backfill` capability - approved target mapping, named established paths, safe non-production environment, and rollback plan - plus approved ERD/mapping, `PRODUCTION_ACCESS: NO`, and explicit destructive limits; otherwise stop.
3. Capture scoped baseline. Inventory affected schema, constraints, indexes, consumers, data quality, and current contract.
4. Map each element to create/change/retain/deprecate; invent nothing.
5. Run one batch: expand → backfill → integrity validation → switch readers/writers → consumer/API verification.
6. Preserve identity, tenant isolation, and response shapes. Validate counts, duplicates, orphans, types, nulls, ranges, uniqueness, cross-tenant links, repeatability, and rollback.
7. Remove deprecated structures only in a later verified contract step with explicit authorization and consumer proof.
8. Report migrations, data results, compatibility, checks, rollback, unresolved items, and scope.

Never access production/protected systems, install/replace ORM tooling, invent schema, or combine unverified destructive cleanup.
