# Development-data seeding

Act as a senior TypeScript backend and PostgreSQL engineer. Build a deterministic, idempotent development seed system in the existing Replit backend.

## Load and scope

Read `replit.md` and the active profile's business file (e.g. `ai/metco.md`), if it has one. Automatically route this outcome to the non-production seeding process and the most specific installed skill; do not ask the user to choose a mode or skill. Then read `ai/database.md`, `ai/backend.md`, `ai/security.md`, `ai/testing.md`, and that skill.

- Write only the explicitly authorized established seed paths and directly related backend tests.
- Use minimum read-only access to the Replit-owned schema and current services/validators.
- Never access this project's protected paths (resolved from its active profile - see `protected_paths_for(request)`), production data, packages, config, environment files, or deployment files.
- Do not change schema/migrations or place seed inserts in migration SQL.

Assume `PRODUCTION_ACCESS: NO` and destructive reset is not authorized.

## Acceptance criteria

1. Provide deterministic `reference`, `demo`, and `all` profiles when compatible with existing conventions.
2. Use coherent role, tenant, ownership, and cross-module scenarios with fake data only.
3. Re-running any profile creates no duplicates and repairs safe partial state.
4. Refuse production execution and never reset existing data by default.
5. Preserve foreign keys, unique constraints, statuses, authorization assumptions, and audit behavior.

## Execute

Capture scoped Git status/diff. Inventory current schema relationships, seed utilities, identity patterns, services, validators, and tests. Record reuse/creation decisions, then implement in dependency order. Prefer existing services when business invariants require them; justify direct ORM use for immutable reference data.

## Verify and report

Run the narrowest existing checks for first run, second run, partial state, counts, relationships, uniqueness, tenant isolation, production guard, and cleanup limits. Label each result `PASSED`, `FAILED`, or `NOT RUN` with exact evidence.

Report profiles, records/scenarios, files, idempotency strategy, integrity/security checks, limitations, final scoped diff, and confirmation that no protected, production, schema, migration, package, or config area was accessed or changed.
