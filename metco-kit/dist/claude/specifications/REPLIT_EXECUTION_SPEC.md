# METCO Replit Execution Specification

Specification version: 6

## 1. Requirements

- `EXEC-001`: Replit MUST load `replit.md` and `ai/metco.md`, then automatically select the most specific installed skill.
- `EXEC-002`: The user MUST NOT be asked to select a workflow label.
- `EXEC-003`: The selected skill MUST remain subordinate to explicit scope and permanent protections.
- `EXEC-004`: Discovery MUST start at named paths and expand only for a concrete unresolved dependency.
- `EXEC-005`: Writes MUST be sequential at ownership, contract, phase, or data boundaries.
- `EXEC-006`: Verification MUST be proportional to changed behavior and risk.
- `EXEC-007`: Complex work MUST proceed as separately authorized, reversible phases.
- `EXEC-008`: Final claims MUST be backed by executed evidence.

## 2. Capability gates

| Capability | Required evidence |
|---|---|
| Ordinary frontend/backend change | Outcome and exact normal-tree scope |
| Audit or diagnosis without fixes | User requested review/diagnosis or no write authority |
| Broad architecture refactor | Explicit broad outcome, named tree, preserved contracts, staged rollback |
| Instruction maintenance | Explicit request and exact instruction paths |
| Schema/migration/backfill | Explicit request, approved mapping, established paths, safe non-production environment, rollback |
| Data seeding | Explicit request, established seed paths, safe non-production environment, profiles/scale, idempotency |
| Contract or destructive cleanup | Explicit changed contract or deletion scope, consumer proof, compatibility and recovery |
| Package/config/environment/deployment | Exact explicit authorization and relevant safety prerequisites |

A skill match is not sufficient evidence for a capability gate.

## 3. Bounded lifecycle

1. Parse outcome, scope, decisions, explicit authorizations, acceptance, and stop conditions.
2. Load root, common instructions, triggered domain instruction objects, testing rules, and one selected skill.
3. Capture scoped status and diff.
4. Inspect named owners, direct callers/imports, contracts, and related tests.
5. Stop discovery once ownership, direct consumers, pre-existing changes, and relevant checks are known.
6. Record reuse, extension, or creation decision where a new unit may be needed.
7. Implement one bounded write batch.
8. Run the smallest relevant checks.
9. Review final scoped diff and report.

## 4. Complex lifecycle

Use phases when one batch cannot be safely understood, verified, or rolled back.

Each phase MUST define:

- `PHASE-*` ID and one observable outcome;
- automatically routed skill based on the phase result;
- prerequisites and prior handoff evidence;
- exact write and minimum read paths;
- explicitly deferred work;
- preserved invariants;
- stop conditions;
- verification gate;
- rollback/recovery boundary;
- next-phase handoff.

Only the earliest authorized incomplete phase receives a full executable prompt. Later phases remain plan rows until the prior handoff is reviewed against current project state.

Common safe sequence:

1. discovery and contract proof;
2. additive foundation or schema expansion;
3. data backfill or service implementation;
4. consumer switch or UI integration;
5. integrated verification;
6. cleanup only after consumer and rollback proof.

## 5. Discovery budget

Start with:

- named target files;
- direct imports and callers;
- owning service/repository/component;
- directly related tests;
- scoped status and diff.

Expand one dependency hop only when ownership, contract, consumers, or risk remains unresolved. Repository-wide scans and full test suites are prohibited by default.

## 6. Creation gate

Before creating a component, hook, service, repository, utility, type, validator, route, or abstraction, record:

- requirement served;
- approved search paths and terms;
- closest existing candidates;
- why reuse or extension is insufficient;
- destination and ownership;
- public interface;
- how duplication is prevented.

## 7. Verification

Checks are labeled:

- `PASSED`: executed with successful evidence;
- `FAILED`: executed and unsuccessful;
- `NOT RUN`: not executed, with reason and risk.

Verification expands only after a targeted failure or evidence of wider impact. No dependency installation, configuration change, production service, or unknown external system is permitted solely to run a check.

## 8. Final report

The report includes:

1. outcome and acceptance status;
2. files changed and purpose;
3. routed skill and ownership/reuse decisions;
4. exact check results;
5. preserved contracts and user work;
6. failures, limitations, and remaining risk;
7. HITL decisions and resume evidence, if any;
8. scope and protected-path compliance.
