---
name: project-prompt-router
description: Automatically select and complete the correct internal process mode and prompt template for business files, detailed implementation specifications, audits, delivery backlogs, controlled changes, and Replit prompts. Use when a user asks to generate, update, audit, plan, change, improve, specify, or implement a project artifact without manually choosing a mode, skill, or execution shape; activate human-in-the-loop only for an unknown answer/next step, two materially correct answers without a governing winner, or a self-made decision that would change scope.
---

# Project Prompt Router

Return the artifact needed for the user's immediate decision or next action. Do not silently merge deliverables.

Read `references/process-modes-spec.md` when selecting the internal artifact mode or resolving a routing tie. Read `references/artifact-contracts-spec.md` when validating detailed artifact completeness. Read `references/object-oriented-instructions-spec.md` when a routed artifact must describe implementation instruction objects. Read `references/routing-spec.md` when changing or auditing routing behavior.

## Route

| Immediate deliverable | Automatic internal mode | Read and use |
|---|---|---|
| Business outcome, rules, scope, value, success | `BUSINESS_DEFINITION` | `references/business-file-template.md` |
| Implementation-ready behavior or contract | `IMPLEMENTATION_SPECIFICATION` | `references/spec-file-template.md` |
| Evidence-based review without fixes | `EVIDENCE_AUDIT` | `references/audit-template.md` |
| Dependency-aware delivery backlog | `DELIVERY_BACKLOG` | `references/task-backlog-template.md` |
| Controlled amendment, enhancement, or improvement | `CHANGE_CONTROL` | `references/change-improvement-template.md` |
| Structured collection of missing inputs | `PROMPT_INTAKE` | `references/request-form.md` |
| Bounded paste-ready Replit task | `REPLIT_PROMPT_BUILD` | `references/replit-task-template.md` |
| Phased Replit implementation/change | `REPLIT_PHASE_PLAN` | `references/phased-implementation-template.md` |
| Decision request after one of the three HITL cases | none—HITL is not a mode | `references/hitl-decision-template.md` |
| Reply to an unresolved `DECIDE [HITL-ID]` request | preserve prior mode | Resume through the `replit-task-builder` skill |

Select by requested output, not a single verb. “Improve the specification” routes to change/improvement if the user wants a change record, to audit if they want findings, or to specification if they want the revised spec itself.

When several deliverables are requested, preserve this dependency order:

1. Business file
2. Specification
3. Audit or change decision
4. Task backlog
5. Bounded or phased Replit prompt

Generate only the requested deliverables. State a blocker when an earlier artifact or material decision is required.

## Build

1. Extract the requested deliverable, source authority, outcome, audience, scope, decisions, evidence, and constraints.
2. Select the internal artifact mode automatically and read only the routed template. For Replit prompts also read `references/replit.md` and invoke the `replit-task-builder` skill when available.
3. Preserve stable requirement IDs and trace sources through downstream artifacts.
4. Separate facts, decisions, assumptions, recommendations, and open questions.
5. Resolve low-risk gaps from evidence. For Replit work, invoke the `replit-task-builder` skill; let it automatically select the execution mode, skill, and instruction objects. If the input answers an unresolved HITL request, preserve its ID and route it as a continuation of the paused task, not a new task.
6. For specifications, audits, changes, backlogs, and Replit prompts, include selected instruction objects only when they clarify implementation responsibility, inputs, authority boundaries, or output evidence.
7. Remove irrelevant sections and every unresolved placeholder unless the user requested a reusable template.
8. Return the polished artifact directly.

## Replit execution-shape gate

Use phased execution when any of these apply:

- multiple domains or independently deployable surfaces;
- schema, migration, backfill, seeding, or destructive cleanup;
- authentication, authorization, tenant scope, sensitive data, or public contract change;
- broad refactor, uncertain ownership/consumers, staged compatibility, or high rollback risk;
- work that cannot be safely verified and rolled back in one bounded batch.

Otherwise use one bounded task. Do not expose mode, primary-skill, complexity, or execution-profile fields for the user to choose.

For phased implementation or change work, require `references/phased-implementation-template.md`. Produce the phase plan and one standalone Replit prompt for only the next authorized phase, with exact prerequisites, scope, acceptance criteria, verification gate, stop conditions, rollback boundary, and handoff evidence. Generate later prompts only after reviewing the current handoff. Automatically select the mode and skill from each phase's actual outcome and write scope. Never produce one oversized implementation prompt or all future prompts upfront.

## HITL continuation

When HITL activates, return only its decision request and stop the entire task. On a later `DECIDE` reply, validate the ID, answer, scope, and permanent boundaries. Keep the task paused and ask one narrowed follow-up if the reply is incomplete, ambiguous, or mismatched. Otherwise require the minimal scoped drift check from `replit.md` and resume the exact blocked step without restarting completed work.
