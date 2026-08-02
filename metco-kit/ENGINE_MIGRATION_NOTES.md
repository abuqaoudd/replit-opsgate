# Engine Migration Notes

## Goal

Move METCO from a document-only prompt kit toward a Replit-ready orchestration engine.

## Principle

Do not add more repeated Markdown when a rule can become structured data.

Use:

- Python contracts for rules software must inspect;
- Markdown for human and agent guidance;
- validators for release confidence;
- generated distributions for ChatGPT and Replit packaging.

## Source of truth

Canonical files live under `canonical/`.

Generated outputs live under `dist/` and should be rebuilt with `python3 tools/build-distributions.py`.

## Current engine contracts

- `tools/metco_contracts.py`: deliverable routing, mode/skill/reference mapping, phased-routing rules, capability gates, protected paths, request/report/HITL schemas, distribution mappings, profiles, template metadata, run state, and hard gate registry.
- `tools/metco_fixtures.py`: routing, HITL, state, parsed-report, and gold-standard fixture data used by validation.

## Markdown cleanup strategy

Keep existing Markdown content, but improve it gradually:

1. Remove repeated rule bodies once the rule is represented in a Python contract.
2. Keep Replit-facing files operational and concise.
3. Keep artifact templates focused on final output quality.
4. Keep specifications normative, not repetitive.
5. Reference Python-backed rules instead of restating them in every file.

## Added after foundation pass

- `compile-prompt.py` creates a first ready-to-use prompt from a structured request and routing result.
- `init-state.py` creates a parseable run state for bounded or phased work.
- `parse-report.py` extracts files, checks, HITL mentions, blockers, and residual risk from a Replit final report.
- `diff-upgrade.py` compares old and new kit roots and highlights changed files.
- `intake-request.py` turns a plain-language request into a first structured request object.
- `next-phase-prompt.py` combines run state and parsed report evidence to generate the next phase prompt.
- `build-replit-install.py` creates a clean Replit-only install folder.
- `release-notes.py` generates release notes from upgrade diff output.
- `preflight.py`, `check-paths.py`, and `check-capabilities.py` enforce hard gates before work.
- `lint-prompt.py` and `lint-report.py` reject prompts/reports missing gate evidence.
- `init-run.py` creates a traceable run folder.
- `record-decision.py` appends human decisions to `runs/decisions.pylog`.
- `audit-engine.py` checks root Replit install files against generated kit output.
- `canonical/examples/gold-standard/` captures good request, HITL, and report examples.

## Suggested v6 work

- Make the prompt compiler template-aware for every artifact type, not just a generated operational prompt.
- Replace the lightweight Python schema validator with a fuller validation implementation if dependencies are allowed.
- Add a richer compatibility checker for v6-to-v6 upgrades.
- Add stronger fixture coverage for multi-deliverable requests and invalid HITL resumes.
