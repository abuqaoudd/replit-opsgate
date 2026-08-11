# Scenario Skill Contracts Specification

Specification version: 6

## 1. Shared contract

Every scenario skill MUST:

1. declare its mapped internal mode;
2. load root, common, triggered domain instruction objects, and testing instructions;
3. validate capability gates before writes;
4. identify exact outcome, scope, ownership, consumers, and preserved behavior;
5. reuse before creating;
6. perform one bounded batch or one current phase;
7. verify changed behavior and risk;
8. report selected instruction objects, object inputs, routing, files, evidence, limitations, and scope compliance.

Mode and skill selection never grants authority.

Triggered instruction objects contribute responsibilities, inputs, `Must Not` boundaries, workflow guidance, and output evidence. Skills MUST NOT treat a loaded object as expanded authority.

## 2. Frontend implementation

Mode: `FRONTEND_IMPLEMENTATION`

Required inputs:

- user-visible outcome and affected roles;
- named feature/page/component scope;
- UI states and preserved behavior;
- existing contract or data source.

Workflow:

1. locate the owning feature and route;
2. trace client service, types, validation, hooks, callers, and UI owner;
3. reuse established design-system and state patterns;
4. implement typed success, loading, empty, error, retry, and permission states;
5. verify behavior, keyboard/focus, responsive layout, and affected callers.

Completion evidence: scoped diff, reuse/creation decision, typed check, targeted tests, and manual state coverage.

## 3. API implementation

Mode: `API_IMPLEMENTATION`

Required inputs:

- operation and observable contract;
- actor, permission, tenant/object scope;
- named backend resource paths;
- validation, errors, and compatibility expectations.

Workflow:

1. trace route registration, middleware, validation, service, repository, and types;
2. enforce authorization and field allowlists server-side;
3. preserve response/error shapes unless explicitly changed;
4. use bounded parameterized data access and safe logging;
5. verify success, invalid, unauthenticated, forbidden, not-found, conflict, and failure behavior.

Completion evidence: route-to-repository ownership, contract comparison, focused checks, and leakage/security review.

## 4. Full-stack implementation

Mode: `FULL_STACK_IMPLEMENTATION`

Required inputs:

- one coordinated cross-surface outcome;
- stable or explicitly changed API contract;
- actor and record scope;
- exact frontend and backend paths.

Workflow:

1. prove the contract and cross-surface invariants;
2. implement backend validation/authorization first;
3. verify backend behavior independently;
4. implement typed frontend consumption and all visible states;
5. verify integrated success, denial, validation, failure, and compatibility.

Use separate phases when either surface is independently reversible or the contract is changing.

## 5. Authentication and permissions

Mode: `AUTH_PERMISSION_IMPLEMENTATION`

Required inputs: actor/action/resource matrix, identity source, object/tenant rules, sensitive fields, denial behavior, and audit needs.

Workflow:

1. derive identity server-side;
2. enforce permissions at route/service/data boundaries;
3. prevent cross-object and cross-tenant disclosure;
4. keep client visibility consistent without treating it as enforcement;
5. verify allowed, denied, stale-role, unassigned, cross-tenant, and sensitive-field cases.

Completion evidence: authorization matrix coverage and explicit information-leakage assessment.

## 6. Form workflow

Mode: `FORM_WORKFLOW_IMPLEMENTATION`

Required inputs: create/edit intent, fields, initial values, transformations, validation, mutation contract, and save/cancel outcomes.

Workflow:

1. map source data to form state and payload;
2. reuse field, validation, dialog/drawer, and mutation patterns;
3. implement field and cross-field validation;
4. guard duplicate submissions and preserve user input on recoverable failure;
5. verify create/edit, invalid, denied, conflict, server error, cancel, keyboard, focus, and responsive behavior.

## 7. Table and reporting

Mode: `TABLE_REPORTING_IMPLEMENTATION`

Required inputs: columns, role-scoped data, filtering, sorting, pagination, actions, summaries, and export expectations.

Workflow:

1. define server/client ownership for query state;
2. use stable allowlisted sorts and bounded queries;
3. preserve URL or state conventions;
4. implement loading, empty, no-results, error, retry, selection, and action feedback;
5. verify permissions, large/edge data, responsive behavior, and accessibility.

## 8. Frontend architecture refactor

Mode: `FRONTEND_ARCHITECTURE_REFACTOR`

Required inputs: explicit broad outcome, named tree, baseline, preserved contracts, exclusions, and phased rollback.

Workflow:

1. collect bounded baseline metrics;
2. classify files and duplicate groups;
3. choose retained owners and reuse targets;
4. stabilize shared foundations before consumer migration;
5. migrate one reversible batch;
6. delete only after complete consumer proof;
7. compare behavior and same-method metrics.

## 9. Database schema evolution

Mode: `DATABASE_SCHEMA_EVOLUTION`

Required inputs: explicit request, approved target mapping, established paths, non-production environment, compatibility strategy, and rollback.

Workflow:

1. inventory schema and consumers;
2. map create/change/retain/deprecate;
3. expand additively;
4. backfill separately and idempotently;
5. validate integrity and counts;
6. switch readers/writers;
7. verify all consumers;
8. contract/remove only in a later authorized phase.

Never infer schema fields, run production changes, or combine unverified destructive cleanup.

## 10. Non-production data seeding

Mode: `NONPRODUCTION_DATA_SEEDING`

Required inputs: explicit request, seed paths, environment, profiles, scale, data scenarios, idempotency, and cleanup limits.

Workflow:

1. enforce production guard;
2. model dependency-aware deterministic identities;
3. create coherent role/tenant/business scenarios;
4. preserve real and pre-existing data;
5. verify first run, second run, and partial-state repair;
6. check integrity, uniqueness, permissions, and cleanup behavior.

## 11. Bug diagnosis

Mode: `BUG_DIAGNOSIS`

Required inputs: symptom, expected behavior, environment, actors/data, reproduction, logs/errors, and named scope.

Workflow:

1. reproduce or establish the nearest reliable signal;
2. trace the shortest behavior path;
3. test competing hypotheses with discriminating evidence;
4. identify root cause and blast radius;
5. recommend the smallest remedy;
6. implement only if explicitly requested and authorized.

Do not confuse correlation with cause or alter code during a read-only diagnosis.

## 12. Performance optimization

Mode: `PERFORMANCE_OPTIMIZATION`

Required inputs: reproducible scenario, data scale, baseline metric, target, environment, and correctness constraints.

Workflow:

1. measure before changing;
2. attribute cost to a specific owner;
3. change one bounded bottleneck;
4. compare using the same method;
5. verify correctness and regressions;
6. report absolute and relative results with limitations.

No speculative optimization.

## 13. UI/UX review

Mode: `UI_UX_REVIEW`

Required inputs: user role, primary journey, screens/states, design-system evidence, target viewports, and accessibility expectations.

Workflow:

1. review hierarchy, terminology, actions, density, feedback, and destructive safeguards;
2. review loading, empty, no-results, error, success, denial, and conflict states;
3. test keyboard, focus, semantics, labels, contrast, and responsive behavior;
4. distinguish standards violations from preferences;
5. remain read-only unless implementation is explicitly requested.

## 14. Safe verification

Mode: `SAFE_VERIFICATION`

Required inputs: governing criteria, exact paths, risk model, environment, and available tests.

Workflow:

1. capture scoped state;
2. map criteria to evidence;
3. run the smallest risk-based checks;
4. inspect changed behavior and direct consumers;
5. label `PASSED`, `FAILED`, or `NOT RUN`;
6. report limitations without implementing fixes.

## 15. Instruction-system maintenance

Mode: `INSTRUCTION_SYSTEM_MAINTENANCE`

Required inputs: explicit instruction-change request, exact paths, desired behavior, version target, and distribution targets.

Workflow:

1. inventory precedence, modes, paths, references, and duplicates;
2. update normative specifications first;
3. change canonical runtime files and skills;
4. preserve application and protected paths;
5. synchronize distribution copies;
6. validate frontmatter, references, mode-to-skill mapping, and parity;
7. forward-test routing, phases, and HITL;
8. rebuild and inspect archives.
