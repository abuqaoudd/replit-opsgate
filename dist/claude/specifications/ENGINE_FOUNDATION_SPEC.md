# METCO Engine Foundation Specification

Specification version: 6

## 1. Purpose

The engine foundation makes the METCO kit programmable without replacing the agent-facing Markdown. Markdown remains the instruction and artifact layer. Python contracts define the machine-readable contract used by routing, validation, building, and future prompt compilation.

## 2. Source model

- `canonical/**` is the source of truth.
- `dist/claude/**` and `dist/replit/**` are generated outputs.
- Distribution files must be rebuilt, not hand-edited.
- A release is valid only after build and validation pass.

## 3. Engine contracts

| Contract | File |
|---|---|
| Kit release metadata | `tools/metco_contracts.py` |
| Routing and skill selection | `tools/metco_contracts.py` |
| Capability gates | `tools/metco_contracts.py` |
| Protected and locked paths | `tools/metco_contracts.py` |
| Request intake | `tools/metco_contracts.py` |
| HITL decision shape | `tools/metco_contracts.py` |
| Template metadata | `tools/metco_contracts.py` |
| Run, phase, and handoff state | `tools/metco_contracts.py` |
| Parsed final report | `tools/metco_contracts.py` |
| Distribution build map | `tools/metco_contracts.py` |
| Project profiles | `tools/metco_contracts.py` |
| Instruction object guidance | `canonical/specifications/OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` |

## 4. Required tools

- `build-distributions.py` generates Claude and Replit outputs.
- `validate-kit.py` checks Python contracts, skill metadata, protected rules, generated drift, archives, fixtures, compiler output, run state, and report parsing.
- `route-request.py` returns the selected artifact, mode, skill, references, execution shape, and missing authority.
- `compile-prompt.py` creates a first operational prompt from request data and routing output.
- `init-state.py` creates structured run state.
- `parse-report.py` extracts structured evidence from a final report.
- `diff-upgrade.py` compares kit roots during upgrades.

## 5. Markdown cleanup rule

When a rule exists in a Python contract, Markdown should explain how the agent should apply it. Markdown should not become a second independent source of truth for the same table or gate. If the Python contract and Markdown conflict, fix the source and validation before release.

Markdown domain files under `ai/**` should use the instruction object contract defined in `OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md`: responsibility, activation, inputs, `Must Not`, workflow, and output evidence. This structure organizes agent behavior but does not replace machine-readable Python contracts.

## 6. Release acceptance

A release must pass build generation, validation, routing fixture checks, HITL fixture checks, ZIP integrity checks, generated-distribution drift checks, and protected-path regression checks.
