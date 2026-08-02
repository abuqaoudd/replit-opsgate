# METCO Refactoring Instruction Object

Read for behavior-preserving refactors, consolidation, moves, dead-code cleanup, oversized-file remediation, or architecture work.

## Responsibility

Own behavior-preserving refactor guidance for ownership cleanup, consolidation, moves, deletion proof, broad frontend architecture batches, before/after evidence, and rollback boundaries.

## Activation

Use this object when the requested outcome is refactoring, consolidation, code movement, dead-code cleanup, oversized-file remediation, architecture improvement, or a behavior-preserving phase of a larger implementation.

## Inputs

- Explicit refactor outcome, named approved tree/files, preserved contracts, exclusions, baseline method, and rollback strategy.
- Existing owners, consumers, duplicate groups, size thresholds, tests, current failures, and creation/deletion evidence.
- Selected internal mode, capability gate status, and applicable frontend/backend/testing objects.

## Must Not

- Treat line reduction as the goal, change behavior/contracts, delete without consumer proof, or migrate unrelated consumers.
- Perform broad architecture work without explicit broad outcome, named tree, preserved contracts, and phased rollback.
- Touch package/config/schema/generated/protected paths unless separately authorized.

## Automatic routing

- Route a bounded refactor through the owning feature/backend skill when it affects one named feature, file, component category, or resource.
- Route broad frontend ownership or consolidation through `FRONTEND_ARCHITECTURE_REFACTOR` and its dedicated skill.

Do not ask the user to choose the mode. Broad work still requires an explicit broad outcome, named approved source tree, preserved contracts, and phased rollback; routing does not grant that authority.

Preserve behavior/contracts, reduce real duplication, improve ownership/typing/testability, and avoid package/config/schema/generated/protected changes. Line reduction is evidence, not the goal.

## Baseline for broad refactors

Using approved paths only, record file/line counts by relevant extension, largest files and thresholds, module categories, duplicate groups, static inline styles, nested components, presentation-layer requests, tests, and current failures. Exclude dependencies, generated/build/coverage/minified/binary/protected content.

Classify in-scope files as `KEEP`, `REFACTOR_IN_PLACE`, `SPLIT`, `MOVE`, `MERGE`, `REPLACE_WITH_SHARED`, `DELETE_AFTER_VERIFICATION`, or `DO_NOT_TOUCH`. For non-`KEEP`, record problem, target/retained implementation, consumers, preserved behavior, and checks.

## Reuse map and batches

Group competing shells/headers; actions; tables/filters/pagination; forms/validation; dialogs; feedback states; API/hooks/services; types/constants/utilities; and backend route/service/repository/error patterns.

For each group select retained implementation, generic changes, consumers to migrate, delayed deletions, and feature-owned differences.

Each batch targets one component category, feature, oversized page, backend resource, or duplicate utility/service group. Name changed/created/deleted files, retained implementation, preservation checks, tests, and rollback boundary. Stabilize shared foundations before migrating many consumers.

## Deletion gate

Delete only after checking imports, exports, routes/lazy imports, registries, string/dynamic references, flags, and tests; migrating every consumer; verifying replacement; and confirming no approved-path reference remains.

## Workflow

1. Confirm whether the refactor is bounded owner work or broad architecture work.
2. Record approved baseline metrics, owners, duplicate groups, classifications, retained implementations, and rollback boundary.
3. Stabilize shared foundations before migrating consumers.
4. Execute one reversible, independently verifiable batch.
5. Verify same-method before/after behavior, consumers, imports, tests, metrics, and deletion proof before cleanup.

## Output Evidence

For broad work include baseline, classifications, reuse map, completed batches, file operations, creation evidence, behavior comparison, exact checks, same-method before/after metrics, remaining safe batches, and scope compliance. Stop a batch for unsupported contracts, uncertain deletion/business rules, or protected/locked requirements; continue independent safe batches.

For broad work include baseline, classifications, reuse map, completed batches, file operations, creation evidence, behavior comparison, exact checks, same-method before/after metrics, remaining safe batches, and scope compliance. Stop a batch for unsupported contracts, uncertain deletion/business rules, or protected/locked requirements; continue independent safe batches.
