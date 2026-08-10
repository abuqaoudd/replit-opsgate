# METCO Backend/API Instruction Object

Applies to approved work inside this project's backend source root (see `replit.md` §2 - the active profile's `backend_root`, or the task's explicitly authorized backend path when no profile applies).

## Responsibility

Own backend/API implementation guidance for route contracts, controllers, services, repositories, validation, authorization, data access, error mapping, logging, and compatibility.

## Activation

Use this object only after routing selects an API, backend, full-stack backend phase, permission, or persisted behavior workflow whose approved write scope is inside this project's backend source root. Selection of this object does not authorize schema, migration, package, config, generated, protected, or destructive changes.

## Inputs

- Operation, observable contract, actor, permission, tenant/object scope, and acceptance criteria.
- Exact approved write paths, minimum read-only paths, existing route/resource owner, and direct consumers.
- Current validation, error, transaction, repository, mapper, and logging conventions.
- Explicitly authorized contract changes, if any.

## Must Not

- Change routes, methods, statuses, response shapes, auth requirements, schema, migrations, packages, config, or protected files without explicit authority.
- Spread request bodies into writes or trust client-provided identity, roles, tenant scope, or object ownership.
- Expose sensitive data, internals, raw errors, secrets, SQL, paths, stacks, or unauthorized record existence.
- Create a parallel backend architecture.

## Architecture

Follow the dominant pattern: route (path/middleware/delegation), controller (HTTP mapping), service (business rules/authorization/transactions), repository (bounded persistence), validation (external input/allowlists), mapper (stable output). Do not create a parallel architecture.

Before adding a unit, record the creation-gate evidence from `replit.md`.

## Contract and input

- Preserve routes, methods, field names, statuses, response shapes, and auth requirements unless explicitly authorized.
- Validate path, query, body, relevant headers, uploads, pagination, filters, sorting, identifiers, and dates.
- Allowlist writable and sortable fields; never spread request bodies into writes.
- Stop if a generated contract must change without authorization.

## Authorization and data

For protected operations verify server-derived identity, action permission, object/tenant scope, allowed transition, and response filtering. Role checks alone are insufficient.

Use existing connections/repositories, parameterized bounded queries, required-field selection, and short transactions for atomic multi-write workflows. Avoid N+1 access, unbounded in-memory pagination, arbitrary ordering, and external calls inside transactions.

## Errors and logs

Use existing error mapping. Distinguish validation, authentication, authorization, not found, conflict, and internal failure. Do not turn errors into success or expose stacks, SQL, paths, tokens, secrets, raw bodies, or sensitive rows.

## Workflow

1. Trace route registration, middleware, validation, controller, service, repository, mapper, types, and tests.
2. Preserve or explicitly gate every contract, permission, and data-shape change.
3. Enforce server-derived authorization, allowlisted input, bounded parameterized data access, and safe transactions.
4. Implement one bounded backend batch inside the selected owner.
5. Verify success, malformed, unauthorized, forbidden, not-found, conflict, rollback, list bounds, field filtering, and redacted errors/logs as applicable.

## Output Evidence

Verify applicable success, malformed input, unknown fields, unauthenticated, forbidden role/scope, not found, conflict/stale state, duplicate/replay, rollback, bounded list behavior, field filtering, and redacted errors/logs. Confirm no protected, locked, schema, migration, package, or config file changed.
