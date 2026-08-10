---
name: safe-verification
description: Perform scoped QA, regression checks, code/security review, or read-only audit in approved frontend/backend paths. Use after changes or when evidence without fixes is the requested outcome. Requires risk-based checks, honest PASSED/FAILED/NOT RUN results, scoped diffs, and no fixes unless explicitly requested and rerouted.
---

# Safe Verification

Automatically select internal mode `SAFE_VERIFICATION`. This selects a read-only procedure and grants no fix authority.

Before numbered workflow steps, run the Mandatory HITL Gate from `../../../replit.md`. Do not edit, start a phase, or final-report until the gate passes, returns Gate Blocked (a deterministic gate needs authorization), or emits the required HITL decision request (a Judgment gate found genuine ambiguity). Before each individual numbered step below, also run the lighter Per-Action Gate from `../../../replit.md` — state `Gate: OK` or `Gate: BLOCKED` before acting on that step, and stop the entire task immediately on `BLOCKED` rather than continuing to the next step.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{testing}.md`; add only relevant domain references.
2. State whether this is post-implementation verification or a requested read-only audit, plus exact paths and acceptance criteria.
3. Capture scoped status/diff and inspect only approved paths.
4. Select checks from `ai/testing.md` by changed behavior and risk; do not paste or run irrelevant matrices.
5. Use existing scripts, narrow targets, and safe data/environments.
6. Label every check `PASSED`, `FAILED`, or `NOT RUN` with command/target/status or observation.
7. Compare final diff, preserve pre-existing work, and report regression risk and scope compliance.

Do not edit during read-only verification; never use repository-wide scans, production/unknown data, protected paths, installs, or configuration changes.
