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

ID: HITL-vendor-approvals-P1-Q1
Blocked check: Is the exact owner/path known?
Question: Which existing vendor approvals owner should receive the loading-state change?
Evidence checked: scoped feature paths and direct vendor approvals references
Options:
A. Existing page owner - resume in `artifacts/metco/src/features/vendor-approvals/VendorApprovalPage.tsx`
B. Existing hook owner - resume in `artifacts/metco/src/features/vendor-approvals/useVendorApprovals.ts`
Exact resume point: phase 1 ownership selection before editing
Required reply: DECIDE HITL-vendor-approvals-P1-Q1: answer and exact scope

## Acceptance Criteria

- Loading state is visible.

## Final Report

Include checks as PASSED/FAILED/NOT RUN.
