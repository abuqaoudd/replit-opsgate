# Replit Project Instructions

Instruction version: 7 engine package  
Content baseline: 7  
Purpose: Govern Replit Agent work on this project's own frontend and backend artifacts, whichever project this file has been installed into - resolved via the active profile (Section 2), never assumed.

## 1. Authority

Apply: platform/safety → this file → routed `ai/**` → applicable `.agents/skills/**` → user task → discovered notes. A task may narrow scope, never broaden it. Skills provide workflow, not permission.

## 2. Scope

Normal application writes are limited to this project's own frontend and backend source roots, plus directly related tests inside those trees. Never assume a specific project's folder names - resolve the actual roots in this order:

1. Call `opsgate_show_profile` (registered by this engine's MCP server) to get this project's tenant profile, `frontend_root`, and `backend_root` - resolved from the caller's own tenant identity, never guessed.
2. If the resolved roots are unset, use only the exact paths the current task explicitly authorizes as write scope - never guess a folder name from convention or from another project.

Default deny everything else. Read supporting Python contracts or named contracts only when needed and never edit them without explicit authority for the exact target.

### Never access

Never open, list, search, index, inspect, compare, execute, test, reference, copy, or modify:

- Any path the active tenant's `never_access` list marks protected (see Section 2 for how to resolve it) - a tenant can add its own protected paths on top of the universal baseline below
- `.git/**`, `.env`, `.env.*`, `node_modules/**`, `.github/workflows/**`, `.claude/**`, `.agents/memory/**` - universal baseline, protected under every profile
- aliases, links, mounts, mirrors, caches, or generated copies resolving to protected content
- CI/CD, release, deployment, or production automation

If a path may resolve to protected content, treat it as protected and report the dependency without inspecting it.

### Locked by default

Do not create, edit, delete, rename, regenerate, or reformat packages, lockfiles, dependencies, workspace/build/lint/format config, `.replit*`, environment/secrets, deployment, infrastructure, generated contracts/clients, schema, migrations, seeds, `.agents/memory/**`, instructions, unrelated docs, or source outside approved trees.

## 3. Skill-driven routing and capability gates

The user provides an outcome, allowed scope, source evidence, and explicit authorizations. Do not ask the user to select a mode, skill, complexity label, or execution profile.

Before inspection:

1. Read this file and the active tenant's business file, if it has one.
2. Determine the current observable outcome and affected domain.
3. Select the most specific installed `.agents/skills/**/SKILL.md` automatically.
4. Read only the triggered `ai/**` files and the selected skill.
5. Confirm the requested writes are permitted by the gates below.

A selected skill defines workflow only. It never grants permission, broadens scope, or overrides protected and locked paths.

Select exactly one internal mode automatically and record it in the final report:

| Internal mode | Use | Primary skill |
|---|---|---|
| `FRONTEND_IMPLEMENTATION` | Ordinary React/client behavior | `frontend-development` |
| `API_IMPLEMENTATION` | API/service/repository behavior | `api-server-development` |
| `FULL_STACK_IMPLEMENTATION` | Current phase writes coordinated client and backend behavior | `full-stack-feature` |
| `AUTH_PERMISSION_IMPLEMENTATION` | Authentication, authorization, tenant, role, or object scope | `auth-permission-workflow` |
| `FORM_WORKFLOW_IMPLEMENTATION` | Form state, validation, save/cancel, mutations | `form-workflow` |
| `TABLE_REPORTING_IMPLEMENTATION` | Tables, filters, sorting, pagination, exports, reporting | `table-reporting-workflow` |
| `FRONTEND_ARCHITECTURE_REFACTOR` | Broad frontend ownership or consolidation | `frontend-architecture-refactor` |
| `DATABASE_SCHEMA_EVOLUTION` | Schema, mapping, migration, index, backfill, compatibility | `database-schema-migration` |
| `NONPRODUCTION_DATA_SEEDING` | Deterministic development/test data | `data-seeding` |
| `BUG_DIAGNOSIS` | Reproduction and root-cause evidence | `bug-diagnosis` |
| `PERFORMANCE_OPTIMIZATION` | Measured performance bottleneck | `performance-optimization` |
| `UI_UX_REVIEW` | Visual, responsive, accessibility, or usability review | `ui-ux-review` |
| `SAFE_VERIFICATION` | Read-only QA, regression, compliance, or release evidence | `safe-verification` |
| `INSTRUCTION_SYSTEM_MAINTENANCE` | `replit.md`, `ai/**`, or `.agents/skills/**` | `instruction-maintenance` |

The selected internal mode is a trace label, not user input or authority. Select it again for each phase from the phase's actual outcome. If a specialized mode applies, prefer it over frontend, API, or full-stack general modes. HITL is never a mode.

Legacy labels `NORMAL_IMPLEMENTATION`, `APPROVED_ARCHITECTURE_REFACTOR`, `AUDIT_ONLY`, `INSTRUCTION_MAINTENANCE`, `DATABASE_SCHEMA_MIGRATION`, and `DATA_SEEDING` are obsolete. Never emit or request them. Use the internal modes above plus the independent capability gates below.

| Requested capability | Required authority |
|---|---|
| Ordinary frontend/backend implementation | Exact outcome and scope inside normal application trees |
| Diagnosis, audit, or verification without a requested fix | Read-only work; no writes |
| Broad architecture or ownership refactor | Explicit broad outcome, named approved source tree, preserved contracts, phased rollback |
| Instruction maintenance | Explicit request and exact `replit.md`, `ai/**`, or `.agents/skills/**` targets |
| Schema, migration, mapping, or backfill | Explicit request, approved target mapping, named established paths, safe non-production environment, rollback |
| Data seeding | Explicit request, named established seed paths, safe non-production environment, approved profiles/scale, idempotency |
| Contract change, deletion, or destructive cleanup | Explicit changed boundary, consumer evidence, compatibility, and recovery |
| Package, configuration, environment, deployment, or generated-file change | Exact explicit authorization and task-specific safety prerequisites |

If a capability gate is not satisfied, do not perform that capability. Request only missing authority when the next step is otherwise known. Migration and seeding skills never authorize production access, protected paths, packages, or invented business rules.

### Human-in-the-loop decision pause

Activate HITL only when one of these cases is encountered:

1. Replit cannot determine the answer or cannot determine how to proceed after bounded, approved inspection.
2. Replit finds two materially correct answers and no governing requirement, existing convention, or evidence selects between them.
3. Replit would have to answer a question itself in a way that changes or expands the approved scope.

Do not classify every task or phase. Do not activate HITL merely because work is complex, high-risk, destructive, security-related, or ready for review. Capability gates, authorization requirements, protected paths, and stop conditions remain separate controls. If a rule already permits, requires, or prohibits the action, follow that rule rather than asking a HITL question.

Before pausing, check the approved evidence and direct conventions using `FAST_ACCURATE`. Do not ask when the answer is discoverable within scope, only one answer satisfies the requirements, or a safe low-risk assumption stays inside the approved outcome and contracts.

When a case applies, pause the entire task before making the decision. This is a resumable checkpoint, not task completion, cancellation, or failure. Do not inspect more files, run commands or checks, edit anything, prepare later work, or continue an independent step. Return only one concise decision request containing:

- stable ID `HITL-[task]-P[phase]-Q[number]`, omitting the phase for bounded work;
- which of the three cases occurred;
- the exact question;
- evidence already checked and what remains unknown;
- an `Options` section with 2-4 labeled choices (`A`, `B`, `C`, `D`), each with the exact scope effect;
- for case 1, include a conservative `A` option that keeps the current approved scope and a separate option for each valid next step Replit can name;
- for case 2, include both correct options, their material tradeoffs, and no hidden default;
- for case 3, include one option that stays inside the current boundary and one option that explicitly expands scope;
- the smallest decision needed, the effect of each answer, and the exact resume point;
- required response `DECIDE [HITL-ID]: [answer and exact scope]`.

The task is paused, unfinished, and waiting for the next user message. This is not a workflow selection, risk level, approval gate, completion, cancellation, or failure. Do not claim progress after the pause. Do not say the task has stopped; say it is paused at the named resume point.

Resume only through this sequence:

1. Accept a reply in the form `DECIDE [HITL-ID]: [answer and exact scope]`.
2. Confirm the ID matches the latest unresolved decision request and the answer resolves its exact question within the governing capability gates and permanent protections.
3. If the ID is wrong or the answer is incomplete or ambiguous, return one narrowed follow-up using the same unresolved ID and remain paused. Do no task work.
4. If the answer is valid, record the human decision and its resulting scope.
5. Before editing, run only a minimal scoped drift check: scoped status/diff plus the directly relevant evidence that may have changed while waiting. If drift invalidates the decision or prerequisites, issue an updated HITL request and pause again.
6. Otherwise update the bounded plan and resume from the exact blocked step. Reuse completed discovery and checks; do not restart the task or repeat finished phases.
7. Continue until completion or another one of the three HITL cases occurs.

The final report must record each HITL ID, question, human answer, scope effect, resumed step, and post-resume checks. A HITL answer never overrides permanent protections or capability gates.

### Per-Action Gate

The Mandatory HITL Gate below runs once before editing, once before each phase, and once before the final report. Between those checkpoints, run this lighter check before every individual action that changes state — one file edit, one destructive command, one move to the next workflow step. Do not batch several actions before checking, and do not defer this to a later report.

Before acting, confirm all three, using the same three cases defined above:

1. Known — the exact next step for this specific action is still known without inventing anything (case 1).
2. Single — exactly one materially correct way to do this specific action remains; no unresolved tie (case 2).
3. Bounded — this specific action stays inside the currently approved scope; nothing expands (case 3).

State the result inline, before the action, in one line: `Gate: OK — proceeding` or `Gate: BLOCKED — see decision below`. A `BLOCKED` result stops the entire task immediately and requires the full decision-request format from the Human-in-the-loop section above — do not continue to a different action, and do not fold a blocked action into a later report instead of pausing now.

The Per-Action Gate checks the same three cases as the Mandatory HITL Gate, at finer grain and lower cost, so it can run before every action instead of only at the checkpoints below. It does not replace the Mandatory HITL Gate's full evidence table, and passing it never substitutes for that table at the checkpoints where the table is required.

### Mandatory HITL Gate (per phase and final report)

Call `opsgate_preflight` (see Section 9) to compute the Deterministic rows below - `scope_gate`, `capability_gate`, and `protected_path_gate` - directly; do not re-derive them by hand. The Judgment rows have no tool that can see them - they are the three HITL cases above, surfacing only during the work itself - and remain the agent's own reasoning either way.

Every row below is checked the same way, but two different kinds of failure resolve differently, and only one of them is actually a HITL case:

- **Deterministic** rows have one correct answer and no judgment involved — a failure means an explicit authorization, evidence, or scope grant is missing. Name the gate, state exactly what is missing, and stop. This is a blocked task, not a decision request — there is nothing to choose between, so never use the `DECIDE` reply format for one of these.
- **Judgment** rows are the three real HITL cases from the section above (unknown next step, two tied valid options, self-made scope-expanding decision) — only these use the HITL decision-required format.

Before editing, before each phase, and before final report, complete this gate explicitly:

| Check | Kind | Answer | Evidence |
|---|---|---|---|
| Is the exact owner/path known? | Judgment | YES/NO | |
| Is the write scope explicitly authorized? | Deterministic | YES/NO | |
| Are protected paths excluded? | Deterministic | YES/NO | |
| Are package/config/schema/seed/destructive changes needed? | Deterministic | YES/NO | |
| If risky changes are needed, are they explicitly authorized? | Deterministic | YES/NO/NA | |
| Are there two materially valid implementation choices? | Judgment | YES/NO | |
| Would proceeding require inventing a business rule, permission rule, data rule, or API contract? | Judgment | YES/NO | |
| Is verification possible in a safe environment? | Deterministic | YES/NO | |

Stop immediately on any failing row. If every failing row is Deterministic, name each one and the exact grant it needs, then stop:

```text
# Gate blocked

Blocked gate: name the exact failed gate (scope_gate / capability_gate / protected_path_gate / verification_gate)
Missing: the exact authorization, evidence, or scope change needed to pass
Effect: task remains paused until that authorization is explicitly granted — this is not a HITL question and does not use the DECIDE reply format
```

If any failing row is Judgment — it takes priority when both kinds fail together — return only:

```text
# HITL decision required

ID: HITL-task-Pphase-Qnumber
Blocked check: name the failed gate row
Question: ask the smallest required decision
Evidence checked: list the evidence already inspected
Options:
A. option label - exact scope effect
B. option label - exact scope effect
Exact resume point: phase/step to resume after a valid DECIDE reply
Required reply: DECIDE HITL-id: answer and exact scope
```

Every final report must include `HITL Gate Result`, stating for each failing row whether it resolved as Gate Blocked (Deterministic) or HITL decision (Judgment). A report without that section is incomplete. The final report must also confirm the Per-Action Gate ran before every action taken during the task, not only reconstruct its answers afterward — if any per-action check was skipped, say so explicitly rather than omitting it.

## 4. Route instructions

Always read the active tenant's business file, if it has one. Read only triggered files:

- React/client: `ai/frontend.md`
- API/backend: `ai/backend.md`
- persistence/migration/seed: `ai/database.md`
- authentication, authorization, sensitive data, mutation: `ai/security.md`
- visible UI/accessibility: `ai/ui-ux.md`
- refactor/move/delete: `ai/refactoring.md`
- implementation/audit/verification: `ai/testing.md`
- multi-domain/phased work: `ai/agents.md`
- instruction updates: `ai/maintenance.md`

Use the most specific `.agents/skills/**/SKILL.md` available.

## 5. Lifecycle

Determine execution shape internally. Use one bounded batch when the outcome can be safely inspected, implemented, verified, and rolled back together. Use separate authorized phases for multiple independently reversible surfaces; schema, migration, backfill, or seeding; authentication, tenant, sensitive-data, or public-contract change; broad refactors; staged compatibility; destructive cleanup; or work that cannot be verified and rolled back as one batch.

A phase prompt grants authority only for that phase; prior reports are evidence, and later phases remain deferred. Each phase must define prerequisites, one bounded outcome, exact scope, checks, stop conditions, rollback boundary, and handoff evidence. Select the skill again from each phase's actual outcome.

Default execution profile: `FAST_ACCURATE`.

- Fail fast on missing authority, prerequisites, safe environment, or exact scope before deep inspection.
- Start with named paths, direct imports/callers, and directly related tests. Expand one dependency hop only when current evidence cannot establish ownership, contract, consumers, or risk.
- Stop discovery once the owner, affected contract, direct consumers, pre-existing changes, and relevant checks are identified. Do not keep searching for additional confirmation without a concrete unresolved risk.
- Reuse a prior phase's verified handoff when scoped status and relevant files show it is still current. Do not repeat completed discovery.
- Run independent read-only inspections or checks in parallel when safe. Keep writes sequential at ownership or phase boundaries.
- Use one short plan and concise evidence records. Do not produce role-by-role narration or restate loaded instructions.
- Verify by changed behavior and risk. Broaden checks only after a targeted failure or evidence of wider impact.

1. Determine domain, outcome, capability gates, accepted risk, stop conditions, execution shape, and whether one of the three HITL cases is actually encountered.
2. State write scope, minimum reads, locked/protected areas, expected files, and checks.
3. Capture scoped Git status and diff; preserve user changes.
4. Trace current behavior and ownership until the discovery stop threshold is met.
5. Complete reuse/creation gates only where applicable.
6. Implement one bounded batch.
7. Run the narrow risk-based checks defined in `ai/testing.md`; do not install or reconfigure.
8. Review scoped diff and report evidence.

### Ownership order

Frontend: owning feature → service/API → types → utilities/constants/validation → hooks → consumers/caller props → component internals → new unit.

Backend: route registration → middleware/validation → service → repository/data access → types/utilities → controller internals → new unit.

Inspecting a layer does not authorize changing it. Select the layer that owns the behavior. Prefer existing configuration/composition before changing internals.

### Creation gate

Before adding a component, hook, service, repository, utility, type, validator, route, or abstraction, record: requirement; approved search scope/terms; closest candidates; why reuse/extension fails; exact destination/layer; shared versus feature ownership; public interface; duplication prevention.

## 6. Engineering rules

- Preserve routes, fields, response shapes, authorization, data meaning, and visible behavior unless explicitly changed.
- Keep pages/routes orchestration-focused; keep business logic out of JSX and transport code; keep persistence out of route handlers.
- Reuse existing UI, services, types, validators, and query patterns before creating.
- Do not bypass types, validation, tests, errors, authorization, auditability, or data isolation.
- Do not add secrets, unsafe logging, development bypasses, unbounded queries, or destructive defaults.
- Delete only after all consumers, exports, routes, registries, tests, and dynamic references are checked.
- Never reset, clean, stash, stage, commit, or discard user work unless explicitly requested.
- Scope every scan and command to approved paths; never run repository-wide discovery or tests.

## 7. Verification and evidence

Use existing scripts and safe environments. Report each check as `PASSED`, `FAILED`, or `NOT RUN`, with command/target and exit status or manual evidence. Never infer success from an unrun check.

Final report: outcome; files changed; ownership/reuse/creation decisions; checks; preserved behavior and user work; failures/limitations; remaining risk; confirmation that protected and locked areas were not accessed or changed.

## 8. Stop conditions

Stop before accessing or changing protected content, unknown/production services, packages/config, generated contracts, unsupported public contracts, unauthorized schema/migration/seed files, destructive data, weakened security, or code with unresolved overwrite/deletion risk. Request only the smallest missing authorization or decision. When one of the three HITL cases applies, use the full-task pause and resume sequence above.

## 9. MCP tool availability

This engine's own gate tools (`opsgate_` prefix, configurable via the request's `mcp.tool_prefix` field - e.g. `opsgate_check_capability`, `opsgate_check_paths`, `opsgate_preflight`, `opsgate_record_decision`, plus routing/lint tools) are registered as real MCP tools. Call them directly; never re-derive the gate table in prose:

- A deterministic gate (`capability_gate`, `protected_path_gate`, `scope_gate`) failing from a tool's response is reported the same way regardless - name the gate, state what's missing, stop. It is never a HITL decision.
- Reserve the HITL decision format for ambiguity none of the tools can see (unknown next step, tied valid choices, a self-made scope-expanding decision) - these only surface during the work itself.
- If a human answers a HITL question, call `opsgate_record_decision` with the HITL id and answer before resuming, so the decision is persisted outside the conversation.

If a tool call errors or the MCP connection is unreachable, say so explicitly in the Final Report - the gate ran on inference instead of a computed result. MCP tool availability changes how a gate result is obtained, never what the gate requires or what counts as protected, locked, or authorized.

This file, and this project's own `ai/**`/`.agents/skills/**`, can drift out of date against the engine's canonical versions - or be missing entirely on a brand-new project. Call `opsgate_sync_instructions` to check: it returns every current file (this one, every `ai/*.md` instruction object, every skill workflow), each with its own target install `path` - skill files install under `.agents/skills/`, a different directory name than this engine's own `replit-skills/` source. Write each returned file to its `path`, creating anything missing and overwriting anything that differs, then re-read each to confirm the write succeeded before continuing. This tool never creates tenants or tokens - that stays a separate, deliberate step outside this file's scope. See `ai/maintenance.md` for the full instruction-maintenance workflow.

The same substitution applies inside a selected skill's own workflow steps, not only at the Mandatory HITL Gate checkpoints. Where a skill's numbered steps say to state or verify exact paths, expected owner, or applicable capability gates by hand, call `opsgate_preflight`/`opsgate_check_paths`/`opsgate_show_profile` for that instead - the answer is the same either way, a tool call is just the more reliable way to get it. Skills are not rewritten per mode to say this themselves; this paragraph is the one place it needs to be said.
