# Verification Instruction Object

Read for every implementation, audit, review, refactor, migration, seed, or verification task.

## Responsibility

Own verification guidance for selecting the smallest useful checks, labeling results honestly, preserving safe environments, reviewing scoped diffs, and reporting evidence.

## Activation

Use this object for every implementation, audit, diagnosis, review, refactor, migration, seed, instruction maintenance, or verification task. It does not authorize new writes, dependency installation, production access, or broad test execution.

## Inputs

- Observable acceptance criteria, changed or inspected paths, selected instruction objects, risk level, and direct consumers.
- Existing scripts, targeted tests, safe data/environment, previous phase handoff, and current scoped status/diff.
- Known limitations, failures, unavailable checks, and manual observation targets.

## Must Not

- Call unrun checks passed, use unknown/production services, install dependencies, reconfigure the project, or run destructive database tests.
- Broaden to the full suite by default or treat a narrow pass as whole-project correctness.
- Change files during read-only audit or verification work.

## Safety

Test only approved source trees and directly related tests. Read minimum Python contracts or named project files to discover existing scripts. Use the narrowest existing target; do not install, reconfigure, discover the full workspace, use unknown/production services, or run destructive database tests.

Capture scoped Git status/diff before and after. During a requested read-only audit or verification, make no changes.

## Fast accurate verification

Select the smallest check set that can disprove the changed behavior:

| Risk | Minimum verification |
|---|---|
| Low: isolated presentation, copy, or local behavior without contract/data/security impact | Targeted type/lint or existing unit check plus the changed user flow |
| Medium: shared component/service, mutation, validation, or multi-consumer behavior | Targeted automated checks plus affected success and failure states and direct consumers |
| High: auth/tenant, sensitive data, public contract, schema/data, migration/seed, broad refactor, or destructive change | Current-phase risk matrix, integrity/rollback evidence, and directly affected integration checks |

Run broader checks only when the change crosses the stated boundary, a targeted check fails, or evidence shows shared impact. Do not run the full application suite merely because it exists. Reuse a current verified phase result; rerun only checks invalidated by this phase.

## Select checks by risk

Frontend: route load, roles, loading/empty/no-results/error/retry, form validation/server errors/duplicate submit, CRUD, sort/filter/search/pagination/actions, dialogs, cache refresh, keyboard, 375/768/1280px, accessibility, runtime/console errors.

Frontend architecture: creation evidence, page orchestration, reuse, placement, no nested components/static inline styles/unsafe types/scattered requests, reviewed size thresholds, resolving imports, and deletion proof.

Backend/security: authenticated success, unauthenticated, forbidden role/object scope, malformed/unknown fields, not found, conflict/stale, duplicate/replay, bounded pagination/filter/sort, sensitive-field exclusion, rollback, redacted errors/logs.

Migration/seed: dry-run or safe environment, first and repeated run, partial state, counts, duplicates, orphans, constraints, tenant isolation, API compatibility, rollback/cleanup, production guard, and unchanged packages/config/protected systems.

Refactor: compare routes, roles, fields, labels, actions, APIs, feedback states, sorting/filtering/pagination, mutations, responsive/keyboard behavior, tests, consumers, and before/after metrics using the same method.

Use only applicable checks; do not paste or run every matrix for every task. Stop when acceptance criteria and identified risks have direct evidence.

## Workflow

1. Capture scoped baseline status/diff before implementation or read-only verification.
2. Select checks that can disprove the changed behavior and identified risks.
3. Run the narrowest existing safe targets; broaden only after failure or evidence of wider impact.
4. Label every check `PASSED`, `FAILED`, or `NOT RUN` with command/status or observation.
5. Review final scoped status/diff and report limitations, residual risk, and scope compliance.

## Output Evidence

Label each check `PASSED`, `FAILED`, or `NOT RUN`. Include exact command/target and exit status, or manual observation. Explain failures and unsafe/unavailable checks. Never call an unexecuted check passed.

Final report: outcome; files; reuse/creation decisions; pre-existing work; automated/manual results; failed/not-run checks; security/architecture/regression notes; limitations; scope compliance.
