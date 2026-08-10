---
name: metco-frontend-architecture-refactor
description: Perform an explicitly approved METCO frontend architecture refactor in artifacts/metco/src. Use for broad component consolidation, oversized pages, incorrect placement, duplicate hooks/services/types, static-style cleanup, and verified dead-code removal requiring baseline metrics, classification, reuse mapping, phased batches, and behavior comparison.
---

# METCO Frontend Architecture Refactor

Automatically select internal mode `FRONTEND_ARCHITECTURE_REFACTOR`. This selects procedure; explicit broad-refactor authority remains required.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes, returns Gate Blocked (a deterministic gate needs authorization), or emits the required HITL decision request (a Judgment gate found genuine ambiguity). Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md` and `../../../ai/{metco,frontend,refactoring,ui-ux,testing,agents}.md`.
2. Require explicit broad-refactor authority; name the exact source tree and exclusions.
3. Capture scoped baseline, same-method metrics, architecture inventory, current failures, and pre-existing changes.
4. Build the reuse map and classify every in-scope file using `ai/refactoring.md`.
5. Plan independent batches with exact file operations, retained implementation, preserved behavior, tests, and rollback boundary.
6. Complete creation gates; stabilize shared foundations before consumer migrations.
7. Implement and verify one batch before deletion or the next batch.
8. Recalculate metrics; report behavior comparison, completed/remaining classifications, checks, and scope.

Stop a batch for uncertain consumers/rules, protected paths, locked files, or unsupported contracts; continue independent safe batches.
