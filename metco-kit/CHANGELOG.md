# Changelog

## 6.0.6 Per-Action HITL Gate - 2026-07-27

- Added a second, lighter HITL check tier — the Per-Action Gate — distinct from the existing 8-row Mandatory HITL Gate. The Mandatory HITL Gate still runs once before editing, once before each phase, and once before the final report; the Per-Action Gate runs before every individual state-changing action (one edit, one command, one workflow step) and requires an inline `Gate: OK` / `Gate: BLOCKED` statement before acting. Root cause: the Mandatory HITL Gate was only ever being completed once, retroactively, when writing the final report — real evidence from a live run showed a skipped required row, a blank evidence cell, and an ungrounded claim, consistent with the table being backfilled to match a report format rather than actually gating live decisions.
- Wired the Per-Action Gate into `canonical/references/replit.md` (new `### Per-Action Gate` section), all 14 `canonical/references/replit-skills/*/SKILL.md` files (each now requires it before every numbered workflow step, not just once before the first step), both canonical templates (`METCO_REPLIT_TASK_TEMPLATE.md`, `METCO_REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md`), `HITL_SPEC.md` (new §3 "Check frequency", spec sections renumbered accordingly), and `compile-prompt.py`'s machine-generated output.
- Added `validate-kit.py` checks requiring `replit.md`, every scenario skill, and compiled prompt output to mention "Per-Action Gate", so this can't silently regress.
- Fixed `package.py`: `PACKAGE.version` had been stuck at `6.0.1-ooi` since the ChatGPT-to-Claude migration — every version bump since then updated `metco_contracts.py`'s `KIT_MANIFEST.version` but missed this separate field. Both now read `6.0.6-ooi`.

## 6.0.5 Prompt Lint and Object Naming Fixes - 2026-07-27

- Rewrote `lint-prompt.py`'s required-text check. It previously hardcoded literal strings from one narrow compiled-prompt fixture (`## Scope`, `## Mandatory HITL Gate`, `PASSED/FAILED/NOT RUN` as one joined string, etc.), so it failed the kit's own canonical templates (`METCO_REPLIT_TASK_TEMPLATE.md`, `METCO_REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md`) and any hand- or agent-authored prompt that followed their prose wording ("Phase boundary", "HITL pause rule", lowercase "Acceptance criteria") instead of compile-prompt.py's exact boilerplate. It now checks for the underlying concept via every phrasing actually used by a real source in this kit, and only requires labeled options/exact-resume-point/DECIDE format when a prompt is actually emitting a concrete HITL decision (signaled by the literal heading "HITL decision required"), not just stating the pause policy. Verified against both canonical templates (now pass), the valid/invalid gate-stub fixtures (unchanged pass/fail), and real `compile-prompt.py` output (still passes).
- Fixed an object-naming mismatch in `OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md`: section 3 registered `VerificationInstruction`, but all 6 templates that reference it plus `compile-prompt.py`'s own generator use `VerificationInstructionObject`. Updated the spec to match the name actually used everywhere else instead of changing 6 templates and the compiler. Also added a note telling authors to substitute the exact name from the spec's object table when filling in a template's `[DomainInstructionObject]` placeholder, instead of inventing a new name — the ambiguity in that placeholder is what caused the mismatch to begin with.

## 6.0.4 Duplication Cleanup - 2026-07-27

- Deleted `canonical/claude-skills/*/references/` (50 files across both packaged skills). These were static duplicates of files already living in `canonical/templates/`, `canonical/references/`, and `canonical/specifications/`, and every one of them was fully overwritten at build time by `skill_reference_mappings` regardless of content — confirmed programmatically that zero files would be lost before deleting. Each skill package's canonical source is now just its `SKILL.md`; `build-distributions.py` regenerates the full `references/` tree for both packages from the single canonical source on every build.
- Verified the change is purely a source-tree cleanup with no effect on the shipped output: rebuilt, ran `validate-kit.py` (0 warnings) and `test-all.py` (58/58), and confirmed `dist/claude/claude-skill/` still contains the complete 50-file reference tree for both packages.

## 6.0.3 Test Coverage Hardening - 2026-07-27

- Generalized the `DIST-006` canonical/distribution drift check in `validate-kit.py` from 3 hardcoded file pairs to every copy declared in `DISTRIBUTIONS` (~30 files across both distributions and both packaged skills). Verified it now catches drift that previously went undetected by intentionally corrupting a nested skill-reference file and confirming the check fails.
- Moved the skill-package reference copy map out of `metco_tools.py` (`cmd_build_distributions`) and into `metco_contracts.py` (`DISTRIBUTIONS['claude']['skill_reference_mappings']`), so the builder and the validator share one source of truth instead of the validator checking a hand-picked subset of what the builder actually copies.
- Added `tools/test-all.py`, a single entrypoint that runs the full existing fixture suite plus new coverage: every routing fixture (not just 1-2) through `route-request`, `compile-prompt`, `init-state`, `preflight`, and `check-capabilities`, with gate exit codes checked against the routing engine's own `blocked` decision; every HITL fixture through schema validation; a canonical-against-itself self-diff to sanity-check `diff-upgrade.py`; and a smoke test of the run-state helpers with automatic `runs/` cleanup. Currently 58/58 checks pass.

## 6.0.2 Claude Migration - 2026-07-27

- Replaced the ChatGPT distribution with a Claude distribution: `canonical/chatgpt-skills/` moved to `canonical/claude-skills/`, `canonical/GPT_PROJECT_INSTRUCTIONS.md` renamed to `canonical/CLAUDE_PROJECT_INSTRUCTIONS.md`, and `dist/chatgpt/` renamed to `dist/claude/`.
- Removed the ChatGPT-only `agents/openai.yaml` interface files and the `$skill-name` custom-GPT invocation syntax from both skill packages; skills are now invoked by frontmatter `name` through Claude's Skill tool.
- Updated `tools/metco_contracts.py` (`DISTRIBUTIONS`, `KIT_MANIFEST.generated_roots`) and `tools/metco_tools.py` (build-distributions, diff-upgrade, release-notes, validate-kit) so the engine builds and validates the Claude distribution instead of the ChatGPT one.
- Updated specifications, README, and legacy v6 README references from ChatGPT/GPT/OpenAI wording to Claude wording. The Replit distribution is unchanged.

## 6.0.1 Object-Oriented Instructions - 2026-07-27

- Converted canonical `references/ai/**` files into instruction objects with responsibility, activation, inputs, `Must Not`, workflow, and output evidence sections.
- Added `OBJECT_ORIENTED_INSTRUCTIONS_SPEC.md` and wired it into the specification index, architecture, scenario-skill, engine, and validation/distribution specs.
- Updated Replit, phased, audit, change, specification, backlog, and intake templates to record selected instruction objects, object inputs, authority boundaries, and output evidence.
- Updated the prompt compiler and packaged Claude skills to include object-aware routing and reporting.
- Added validation that canonical AI instruction files expose the required object contract sections.
- Moved METCO-owned JSON manifests, schemas, fixtures, examples, package metadata, run output, and release hashes into Python modules/files while preserving command behavior.

## 6.0.0 Engine Foundation - 2026-07-26

- Added one canonical source layout with generated ChatGPT (later migrated to Claude, see 6.0.2) and Replit distributions.
- Added machine-readable contracts for routing, capability gates, protected paths, HITL, request intake, templates, run state, reports, profiles, and distributions.
- Added validation, build, route, prompt compile, state initialization, report parsing, upgrade diff, request intake, next-phase prompt, Replit install, and release-note tools.
- Added routing, HITL, report, state, and gold-standard examples.
- Added `ENGINE_FOUNDATION_SPEC.md`.
- Preserved the v6 Markdown content while introducing engine contracts.
- Added hard gate enforcement.
- Added preflight, path, capability, prompt-lint, report-lint, run initialization, decision-log, and engine self-audit tools.
- Added mandatory HITL gate requirements to root Replit policy, compiled prompts, final-report contract, and all scenario skills.
