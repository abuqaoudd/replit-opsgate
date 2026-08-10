# METCO Task Control Instruction Object

Read for every task. `replit.md` remains authoritative.

## Responsibility

Own the cross-project task record: outcome, scope, selected instruction objects, authority, ownership, pre-existing work, verification plan, evidence, final reporting, and scope compliance.

## Activation

Use this object for every task before any other domain object. It coordinates loaded instructions but does not override `replit.md`, capability gates, protected paths, or explicit user scope.

## Inputs

- User outcome, acceptance criteria, allowed write/read scope, preserved behavior, and explicit authorizations.
- Automatically selected internal mode, primary skill, relevant domain instruction objects, and current run/phase state.
- Current project evidence, owners, consumers, tests, pre-existing changes, and stop conditions.

## Must Not

- Ask the user to choose internal modes, skills, complexity labels, or execution profiles.
- Treat selected mode, selected skill, loaded object, or recommendation as authority.
- Invent business rules, permissions, data rules, API contracts, owners, dates, or acceptance evidence.
- Expand scope, touch protected paths, or perform destructive work without explicit authorization.

## Start record

Before edits record:

- outcome and observable acceptance criteria;
- automatically selected internal mode, primary skill, and routing evidence;
- approved writes and minimum reads;
- protected/locked categories and stop conditions;
- owning entry point, current behavior, consumers, tests, and expected files;
- relevant instructions/skill;
- verification plan and known pre-existing changes.

Use the narrowest safe interpretation. Ask only when ambiguity changes security, data integrity, public contracts, or destructive behavior.

## Automatic routing and change budget

Select the most specific internal mode and skill from `replit.md`; never ask the user to choose them. Apply the corresponding budget:

- ordinary implementation: smallest complete change plus directly related tests;
- broad architecture refactor: smallest independently verifiable batch;
- diagnosis/audit/verification: evidence and recommendations unless a fix was explicitly requested;
- instruction maintenance: exact authorized instruction files only;
- schema evolution: approved schema/migration batch only;
- data seeding: approved non-production seed system only.

The selected mode and skill do not grant authority.

## Acceptance coverage

Include only applicable: roles and record scope; displayed/mutated data; success; validation; unauthorized/forbidden; loading/empty/no-results/error/retry; pending/duplicate/conflict; responsive/keyboard; API/database compatibility; behavior preservation.

Do not invent business rules.

## Cross-artifact work

Confirm the contract, implement server validation/authorization first, preserve response shapes, update the client only after backend behavior is defined, verify each artifact and the integrated flow, and stop for unauthorized generated/schema/protected changes.

## Workflow

1. Record outcome, acceptance criteria, selected mode/skill/object set, approved scope, locked categories, and stop conditions.
2. Identify owner, current behavior, direct consumers, pre-existing changes, and relevant checks before editing.
3. Apply the narrowest safe interpretation and selected object budgets.
4. Coordinate cross-artifact work in the correct order while preserving contracts and evidence.
5. Report changed files, decisions, checks, limitations, residual risk, and scope compliance.

## Output Evidence

Final output must identify changed files, behavior, ownership and reuse decisions, new-unit justification, exact checks/results, pre-existing work preserved, limitations, remaining risk, and scope compliance. Limited checks never prove whole-project correctness.
