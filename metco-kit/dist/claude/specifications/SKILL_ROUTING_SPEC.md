# METCO Skill Routing Specification

Specification version: 6

## 1. Routing principles

- `ROUTE-001`: Select by immediate deliverable and observable outcome, never by a single keyword.
- `ROUTE-002`: Users MUST NOT be asked to choose or name a mode, skill, complexity class, or execution profile.
- `ROUTE-003`: Select one primary Replit scenario skill from the actual current write outcome.
- `ROUTE-004`: Load only root instructions, `ai/metco.md`, triggered domain instruction objects, testing when applicable, and the selected skill.
- `ROUTE-005`: Multi-deliverable requests MUST preserve dependency order and return only requested artifacts.
- `ROUTE-006`: Complex execution MUST generate only the next authorized phase prompt.
- `ROUTE-007`: A skill choice MUST be recomputed when a later phase has a different write outcome.
- `ROUTE-008`: An unresolved `DECIDE` response MUST route to continuation of the paused task.

## 2. Artifact routing

| Immediate need | Artifact |
|---|---|
| Why, value, scope, actors, business rules, success | Business file |
| Implementation-ready behavior, contracts, states, data, NFRs | Specification |
| Evidence-based findings without implementation | Audit |
| Dependency-aware work breakdown | Task backlog |
| Controlled amendment to an approved baseline | Change/improvement record |
| One reversible implementation batch | Bounded Replit prompt |
| Multiple dependent or separately verifiable batches | Phased Replit prompt |
| Human decision under one of three cases | HITL decision request |

Dependency order:

1. business definition;
2. implementation specification;
3. audit or approved change;
4. task backlog;
5. implementation prompt;
6. verification evidence.

## 3. Replit scenario routing

| Outcome evidence | Primary skill |
|---|---|
| Ordinary React/client behavior | `metco-frontend-development` |
| API route/service/repository behavior | `metco-api-server-development` |
| Coordinated client and Replit backend feature | `metco-full-stack-feature` |
| Authentication, authorization, tenant or permission behavior | `metco-auth-permission-workflow` |
| Form state, validation, mutations, save/cancel | `metco-form-workflow` |
| Tables, filtering, sorting, pagination, reporting | `metco-table-reporting-workflow` |
| Broad frontend ownership or architectural consolidation | `metco-frontend-architecture-refactor` |
| Schema, mapping, migration, backfill, compatibility | `metco-database-schema-migration` |
| Deterministic non-production seed data | `metco-data-seeding` |
| Unknown defect cause or evidence-only diagnosis | `metco-bug-diagnosis` |
| Measured performance bottleneck | `metco-performance-optimization` |
| Visual hierarchy, responsive behavior, accessibility | `metco-ui-ux-review` |
| Read-only QA, regression, compliance, or verification | `metco-safe-verification` |
| `replit.md`, `ai/**`, or `.agents/skills/**` changes | `metco-instruction-maintenance` |

## 4. Tie-breaking

When several skills appear relevant:

1. choose the skill owning the current phase’s write result;
2. prefer a specialized workflow over a general domain workflow;
3. use domain instruction objects as supporting rules, not additional primary skills;
4. select full-stack only when the current phase truly writes both client and backend;
5. select safe verification for a no-write phase;
6. use HITL case 2 only if two materially correct routing choices remain after these rules.

## 5. Internal complexity decision

The router determines execution shape without exposing a classification field.

Use sequential phases when work includes any of:

- more than one independently reversible surface;
- schema, migration, backfill, or seeding;
- authentication, tenant, sensitive-data, or public-contract changes;
- broad refactor or uncertain consumers;
- staged compatibility or destructive cleanup;
- verification or rollback that cannot be proven in one bounded batch.

Otherwise generate one bounded task.

## 6. Routing output contract

Generated prompts state:

- outcome and acceptance criteria;
- exact write and minimum read scope;
- required instruction files to load;
- task-specific decisions and explicit authorizations;
- execution steps, checks, stop conditions, and report.

Generated prompts MUST NOT state:

- `Mode:`;
- `Primary skill:`;
- `Complexity:`;
- `Execution profile:`;
- instructions asking the user to choose those values.

The runtime may report the automatically selected internal mode and skill for transparency after routing, but neither is a user input or authority source. See `PROCESS_MODES_SPEC.md`.
