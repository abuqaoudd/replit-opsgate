# Engine Specification Index

Specification version: 6

This directory defines the normative behavior of the Claude Project Prompt Engine. Root instructions remain the runtime authority; these files define the design contract used to build, audit, and evolve them.

## Specification map

| Specification | Governs |
|---|---|
| `ENGINE_FOUNDATION_SPEC.md` | Python contract, tool, generated-distribution, state, and report contracts |
| `SYSTEM_ARCHITECTURE_SPEC.md` | Authority, components, boundaries, state, and traceability |
| `OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` | Instruction object contract, required object family, and template alignment |
| `PROCESS_MODES_SPEC.md` | Complete internal mode catalog and automatic selection rules |
| `SKILL_ROUTING_SPEC.md` | Automatic artifact and Replit workflow selection |
| `SCENARIO_SKILL_CONTRACTS_SPEC.md` | Inputs, workflow, evidence, and completion contract for every Replit mode |
| `ARTIFACT_CONTRACTS_SPEC.md` | Business, specification, audit, backlog, and change artifacts |
| `REPLIT_EXECUTION_SPEC.md` | Bounded work, complex phases, capability gates, verification, and reports |
| `HITL_SPEC.md` | The only three HITL triggers and strict pause/resume protocol |
| `VALIDATION_DISTRIBUTION_SPEC.md` | Canonical copies, validation, packaging, and upgrade checks |

## Requirement notation

- `SYS-*`: system architecture
- `MODE-*`: internal process modes
- `ROUTE-*`: routing
- `ART-*`: artifact contracts
- `EXEC-*`: Replit execution
- `HITL-*`: human-in-the-loop
- `DIST-*`: validation and distribution
- `ENG-*`: engine foundation
- `OOI-*`: object-oriented instruction contract

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative.

## Source-of-truth order

1. Platform and safety rules
2. `references/replit.md`
3. Routed `references/ai/**`
4. Automatically selected `references/replit-skills/**/SKILL.md`
5. User outcome, scope, and explicit authorizations
6. These design specifications
7. Examples

If a lower source conflicts with a higher source, the higher source wins. A skill selects a workflow but never grants authority.

## Change discipline

Any material engine change MUST:

1. update the affected normative specification;
2. update canonical runtime files and templates;
3. update Python-backed rules where applicable;
4. rebuild generated distributions;
5. validate references, frontmatter, fixtures, reports, and archives;
6. forward-test realistic routing and failure cases.
