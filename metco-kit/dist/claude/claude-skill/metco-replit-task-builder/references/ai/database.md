# METCO Data, Migration, and Seeding Instruction Object

Read for persisted-data work in the Replit-owned backend.

## Responsibility

Own persisted-data guidance for existing-schema data access, schema evolution, migration/backfill sequencing, non-production seeding, data integrity, tenant/object isolation, and rollback evidence.

## Activation

Use this object only after routing selects persisted-data work or when an approved backend/API phase affects database reads, writes, migrations, backfills, or seed data. Schema evolution and seeding require their explicit capability gates before any write.

## Inputs

- Approved outcome, data scope, environment, capability authorization, and rollback or cleanup limits.
- Existing schema, repositories, migration/seed paths, consumers, mappings, and current data risks.
- Actor, tenant/object scope, sensitive fields, integrity rules, and verification expectations.

## Must Not

- Infer schema fields, run production changes, combine destructive cleanup with unverified migration, or treat seeding as migration SQL.
- Change packages/config/generated/protected files or access unauthorized data environments.
- Leak unauthorized record existence, concatenate input into SQL, or bypass current ownership/security fields.

## Existing-schema data work

Schema is fixed unless the user explicitly requested schema evolution and its capability gate is satisfied. Use existing repository/query patterns, server-derived identity, record/tenant scope, field allowlists, parameterized bounded queries, minimal selection, explicit sort allowlists, short transactions, stable mappings, existing date/time rules, and current delete/archive semantics.

Protect identifiers, ownership, audit/security fields, immutable values, and sensitive data. Handle expected duplicate, range, dependency, stale-state, and concurrency conflicts consistently. Never concatenate input into SQL or leak unauthorized record existence.

## Schema evolution workflow

The router selects `DATABASE_SCHEMA_EVOLUTION` and its migration skill automatically when this is the immediate outcome. Proceed only with an explicit user request, approved target ERD/mapping, named established schema/migration paths, non-production environment, and rollback strategy.

For each batch:

1. Inventory affected tables, columns, keys, constraints, indexes, defaults, consumers, and current data risks.
2. Map every current element to create/change/retain/deprecate; do not invent fields or rules.
3. Use expand → backfill → validate → switch readers/writers → verify consumers → contract cleanup.
4. Preserve identity and API shapes; validate counts, duplicates, orphans, nullability, types, ranges, cross-tenant links, uniqueness, and rollback.
5. Drop old structures only in a later verified step after all consumers are proven migrated.

Never run against production, replace the ORM/migration system, or combine destructive cleanup with an unverified migration.

## Non-production seeding workflow

The router selects `NONPRODUCTION_DATA_SEEDING` and its seeding skill automatically when this is the immediate outcome. Proceed only with an explicit user request, named seed paths, non-production environment, and approved profiles/data scale.

Require:

- deterministic, idempotent profiles such as `reference`, `demo`, and `all` when applicable;
- production guard and no destructive reset default;
- dependency-aware inserts and coherent role/tenant/business scenarios;
- no secrets or real personal data; deterministic development identities;
- current services/validation when business invariants require them, or justified direct ORM for reference data;
- first-run, second-run, partial-state, integrity, and unauthorized-environment verification.

Seed logic is not migration SQL. Schema change and data seeding remain separate unless explicitly coordinated.

## Workflow

1. Classify the immediate work as existing-schema data access, schema evolution, backfill, seeding, or cleanup.
2. Validate explicit authority, safe environment, approved paths, mappings, rollback, and production guard.
3. Inventory affected data, consumers, constraints, integrity risks, and compatibility requirements.
4. Execute one additive or idempotent batch; keep expansion, backfill, switch, verification, and cleanup separate.
5. Verify counts, duplicates, orphans, constraints, tenant isolation, repeated runs, rollback/cleanup limits, and unchanged contracts as applicable.

## Output Evidence

Report identities/scope, queries/writes, transaction decisions, integrity checks, unchanged contracts, exact migration/seed artifacts, verification, rollback or cleanup limits, and confirmation that no protected or production system was accessed.
