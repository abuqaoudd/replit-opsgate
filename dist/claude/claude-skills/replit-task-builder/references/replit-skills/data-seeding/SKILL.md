---
name: data-seeding
description: Implement or verify a deterministic, idempotent Replit development/test data seed system. Use only with an explicit seeding request, named established seed paths, a non-production environment, approved profiles and scale, coherent role/tenant scenarios, no destructive reset default, and repeat-run integrity checks.
---

# Data Seeding

Automatically select internal mode `NONPRODUCTION_DATA_SEEDING`. This selects procedure; explicit authority and environment guards remain required.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{database,backend,security,testing,agents}.md`.
2. Require explicit authorization for the `data_seeding` capability - named established seed paths, safe non-production environment, approved profiles/scale, and idempotency - plus `PRODUCTION_ACCESS: NO` and explicit cleanup limits; otherwise stop.
3. Inventory schema relationships, existing seed utilities, services/validators, identity/auth patterns, and representative business workflows.
4. Define deterministic profiles (`reference`, `demo`, `all` when applicable), stable development identities, dependency order, and coherent cross-module scenarios.
5. Add a hard production guard, idempotent upserts/existence rules, no destructive reset default, no real personal data/secrets, and no migration SQL seeds.
6. Verify clean first run, second run, partial state, counts, relationships, unique constraints, roles/tenant isolation, production guard, and documented cleanup.
7. Report profiles, records/scenarios, strategy, checks, and limits.

Stop for schema/package/config changes, production access, destructive reset, invented business rules, or protected systems.
