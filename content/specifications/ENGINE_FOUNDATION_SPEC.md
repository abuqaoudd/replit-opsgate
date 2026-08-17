# Engine Foundation Specification

Specification version: 7

## 1. Purpose

The engine foundation makes this engine programmable without replacing the agent-facing Markdown. Markdown remains the instruction and artifact layer. Python contracts define the machine-readable contract used by routing, validation, and prompt compilation.

## 2. Source model

- `content/**` is the source of truth for domain knowledge (instruction objects, skill workflows, specifications) - read live, at call time, by `tools/opsgate_knowledge.py`. There is no separate generated copy to keep in sync; a change to a source file takes effect on its next read.
- `tools/opsgate_contracts.py` is the source of truth for every machine-readable contract (routing, capability gates, protected paths, schemas).
- `tools/opsgate_tenants.py`'s `tenants/registry.json` is the source of truth for tenant profiles - not a file baked into this repo.
- A release is valid only after `validate-engine` and `test-all` pass.

## 3. Engine contracts

| Contract | File |
|---|---|
| Engine release metadata | `tools/opsgate_contracts.py` |
| Routing and skill selection | `tools/opsgate_contracts.py` |
| Capability gates | `tools/opsgate_contracts.py` |
| Protected and locked paths (universal baseline) | `tools/opsgate_contracts.py` |
| Request intake | `tools/opsgate_contracts.py` |
| HITL decision shape | `tools/opsgate_contracts.py` |
| Run, phase, and handoff state | `tools/opsgate_contracts.py` |
| Parsed final report | `tools/opsgate_contracts.py` |
| Tenant profiles and protected paths | `tools/opsgate_tenants.py` |
| Instruction object guidance | `content/specifications/OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` |

## 4. Required tools

- `validate-engine` checks Python contracts, skill metadata, protected rules, fixtures, compiler output, run state, and report parsing.
- `route-request` returns the selected artifact, mode, skill, references, execution shape, and missing authority.
- `compile-prompt` creates a first operational prompt from request data and routing output.
- `init-state` creates structured run state.
- `parse-report` extracts structured evidence from a final report.

## 5. Markdown cleanup rule

When a rule exists in a Python contract, Markdown should explain how the agent should apply it. Markdown should not become a second independent source of truth for the same table or gate. If the Python contract and Markdown conflict, fix the source and validation before release.

Markdown domain files under `ai/**` should use the instruction object contract defined in `OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md`: responsibility, activation, inputs, `Must Not`, workflow, and output evidence. This structure organizes agent behavior but does not replace machine-readable Python contracts.

## 6. Release acceptance

A release must pass `validate-engine`, `test-all`, routing fixture checks, HITL fixture checks, and protected-path regression checks.
