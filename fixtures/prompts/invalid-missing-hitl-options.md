# METCO Vendor approvals

## Scope

| Access | Paths |
|---|---|
| Write | `artifacts/metco/src/features/vendor-approvals/**` |
| Never access | `metco-api/**`, `pipeline/**` |

## Mandatory HITL Gate

Before editing, before each phase, and before final report, answer this gate explicitly.

If blocked, return only:

# HITL decision required

Question: What should I do?

## Acceptance Criteria

- Loading state is visible.

## Final Report

Include checks as PASSED/FAILED/NOT RUN.
