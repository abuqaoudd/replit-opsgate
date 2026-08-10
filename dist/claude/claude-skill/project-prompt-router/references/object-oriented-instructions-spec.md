# Object-Oriented Instructions Specification

Specification version: 6

## 1. Purpose

Object-oriented instructions organize agent-facing Markdown as instruction objects with explicit responsibilities, activation rules, inputs, boundaries, workflows, and output evidence. The goal is clearer ownership without replacing Python contracts, routing, capability gates, or authoritative root instructions.

## 2. Instruction object contract

Every domain file in `ai/**` SHOULD expose this contract:

| Section | Purpose |
|---|---|
| Responsibility | The behavior or decision area owned by the object |
| Activation | When routing or task evidence should load the object |
| Inputs | Evidence the object requires before work begins |
| Must Not | Boundaries the object cannot cross or authorize |
| Workflow | The smallest ordered behavior the object contributes |
| Output Evidence | What the final report, handoff, audit, or artifact must prove |

An instruction object guides work only inside approved scope. Loading an object never grants authority, expands write paths, weakens protected paths, or replaces HITL rules.

## 3. Required object family

| Object | Source |
|---|---|
| TaskControlInstruction | the active profile's business file, e.g. `ai/metco.md` for the `metco` profile |
| AgentCoordinationInstruction | `ai/agents.md` |
| FrontendInstruction | `ai/frontend.md` |
| BackendApiInstruction | `ai/backend.md` |
| DataMigrationSeedingInstruction | `ai/database.md` |
| SecurityInstruction | `ai/security.md` |
| VerificationInstructionObject | `ai/testing.md` |
| RefactoringInstruction | `ai/refactoring.md` |
| InstructionMaintenanceObject | `ai/maintenance.md` |
| UiUxInstruction | `ai/ui-ux.md` |

When a template's instruction-objects table shows a domain placeholder (for example `[DomainInstructionObject]` or `[Audit/DomainInstructionObject]`), substitute the exact name from this table for the `ai/**` file the phase actually routes to. Do not invent a new object name.

## 4. Template alignment

Templates that produce Replit prompts, phase plans, task backlogs, audits, change records, or implementation-ready specifications MUST ask for:

- selected instruction objects;
- routing evidence for each object;
- object inputs used;
- object authority boundaries;
- object output evidence.

Business and specification artifacts may mention objects only as implementation guidance. They must still keep business requirements and normative specifications separate from implementation procedure.

## 5. Source of truth

Python contracts remain the machine-readable source of truth for routing, gates, protected paths, schemas, and distributions. Markdown instruction objects explain how agents apply those contracts. If an object conflicts with a Python contract or `replit.md`, fix the source and validation before release.

## 6. Release acceptance

An object-oriented instruction release is valid only when:

- all canonical `ai/**` files expose the object contract;
- relevant templates request object-aware routing, inputs, boundaries, and evidence;
- generated Claude and Replit distributions are rebuilt from canonical sources;
- validation passes without distribution drift;
- compiled prompts still preserve HITL, protected paths, scope, acceptance criteria, and result labels.
