---
name: metco-database-schema-migration
description: Implement an explicitly authorized METCO Replit schema migration, ERD mapping, normalization, relationship/index change, backfill, compatibility switch, or migration verification. Use only with an approved target mapping, named established schema/migration paths, non-production environment, phased expand/backfill/validate/contract work, and rollback evidence.
---

# METCO Database Schema Migration

Automatically select internal mode `DATABASE_SCHEMA_EVOLUTION`. This selects procedure; explicit authority and environment guards remain required.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes or emits the required HITL decision request. Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md` and `../../../ai/{metco,database,backend,security,testing,agents}.md`.
2. Require `DATABASE_SCHEMA_MIGRATION`, approved ERD/mapping, named paths, `PRODUCTION_ACCESS: NO`, backup/rollback plan, and explicit destructive limits; otherwise stop.
3. Capture scoped baseline. Inventory affected schema, constraints, indexes, consumers, data quality, and current contract.
4. Map each element to create/change/retain/deprecate; invent nothing.
5. Run one batch: expand → backfill → integrity validation → switch readers/writers → consumer/API verification.
6. Preserve identity, tenant isolation, and response shapes. Validate counts, duplicates, orphans, types, nulls, ranges, uniqueness, cross-tenant links, repeatability, and rollback.
7. Remove deprecated structures only in a later verified contract step with explicit authorization and consumer proof.
8. Report migrations, data results, compatibility, checks, rollback, unresolved items, and scope.

Never access production/protected systems, install/replace ORM tooling, invent schema, or combine unverified destructive cleanup.
