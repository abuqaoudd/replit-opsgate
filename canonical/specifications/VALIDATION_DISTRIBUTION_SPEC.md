# Validation and Distribution Specification

Specification version: 6

## 1. Canonical sources

| Canonical path | Distribution copies |
|---|---|
| `references/replit.md` | Both Claude skill `references/replit.md` |
| `references/ai/**` | Replit task-builder `references/ai/**` |
| `references/replit-skills/**` | Replit task-builder `references/replit-skills/**` |
| `templates/REPLIT_TASK_TEMPLATE.md` | Task-builder `task-template.md`; router `replit-task-template.md` |
| `templates/REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md` | Both skill phase-template references |
| `templates/HITL_DECISION_TEMPLATE.md` | Both skill HITL references |
| Other artifact templates | Router template references |
| `templates/PROMPT_REQUEST_FORM.md` | Both skills’ `request-form.md` |
| `specifications/PROCESS_MODES_SPEC.md` | Both skills’ `process-modes-spec.md` |
| `specifications/SKILL_ROUTING_SPEC.md` | Router `routing-spec.md` |
| `specifications/ARTIFACT_CONTRACTS_SPEC.md` | Router `artifact-contracts-spec.md` |
| `specifications/REPLIT_EXECUTION_SPEC.md` | Task-builder `replit-execution-spec.md` |
| `specifications/HITL_SPEC.md` | Task-builder `hitl-spec.md` |
| `specifications/SCENARIO_SKILL_CONTRACTS_SPEC.md` | Task-builder `scenario-skill-contracts-spec.md` |
| `specifications/OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` | Both skills’ `object-oriented-instructions-spec.md` |

## 2. Required validation

- `DIST-001`: Every skill folder name MUST match its frontmatter `name`.
- `DIST-002`: Skill frontmatter MUST contain only `name` and `description`.
- `DIST-003`: Skill descriptions MUST identify output and triggering contexts.
- `DIST-004`: Skill descriptions MUST name the skill's own folder/frontmatter `name` so Claude's Skill tool can select it by name without a separate interface file.
- `DIST-005`: Every referenced local file MUST exist in the distributed context.
- `DIST-006`: Canonical files and distribution copies MUST be byte-identical where mapped.
- `DIST-007`: User-facing templates and examples MUST contain no manual mode, primary-skill, complexity, or execution-profile fields.
- `DIST-008`: HITL wording MUST contain only the three triggers and strict full-task pause.
- `DIST-009`: Archives MUST pass integrity tests.
- `DIST-010`: Archived version markers and critical behavior MUST match source.
- `DIST-011`: Canonical `references/ai/**` Markdown files SHOULD expose the instruction object contract sections: `Responsibility`, `Activation`, `Inputs`, `Must Not`, `Workflow`, and `Output Evidence`.

## 3. Behavioral forward tests

At minimum, test:

1. a business request routes to the business template;
2. an implementation-ready request routes to the specification template;
3. an ordinary frontend task selects the frontend skill without user labels;
4. a complex cross-surface change produces a phase plan and only one executable phase;
5. explicit migration work selects the migration skill but still checks authorization;
6. a fully specified task does not trigger HITL;
7. each HITL case emits one decision request;
8. invalid `DECIDE` input remains paused;
9. valid `DECIDE` input resumes the exact blocked step.

## 4. Upgrade package

The archive MUST contain:

- root project instructions;
- canonical templates;
- complete references and Replit scenario skills;
- specification suite;
- examples;
- source skill folders;
- packaged router and task-builder ZIPs;
- README with Replit installation and version upgrade mapping.

## 5. Release acceptance

A release is ready only when:

- no canonical/distribution mismatch remains;
- no obsolete manual workflow field remains in user-facing prompts;
- no protected-path rule was weakened;
- skill validation succeeds or an equivalent parser records the unavailable dependency;
- forward tests satisfy routing, phase, and HITL contracts;
- both source and archive searches confirm the release version.
