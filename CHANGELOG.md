# Changelog

## 6.0.8 Deterministic Gates vs. Judgment HITL - 2026-08-10

- Fixed a conflation between deterministic gates and genuine HITL judgment calls, both in `preflight.py`'s output and in `replit.md`'s Mandatory HITL Gate table. `cmd_preflight` internally computes three separately-named, purely deterministic checks (`scope_gate`, `capability_gate`, `protected_path_gate` - each a fixed rule with one correct answer and no judgment involved), but was collapsing all three into a single `required_human_decision` boolean, and the eight-row prose table branded every failing row as a HITL case even though five of the eight rows are deterministic authorization/scope checks, not ambiguity. Only three rows are real HITL cases (owner/path unknown after inspection, two tied valid choices, self-made scope-expanding decision) - the same three cases `replit.md`'s own HITL section already defines.
- `preflight.py` no longer reports `required_human_decision`; it reports `blocked` (honest name for the same deterministic condition) and `blocked_gate_kind: "deterministic"`, since a static pre-execution check can never actually detect real ambiguity - that only surfaces during the work itself.
- `replit.md`'s Mandatory HITL Gate table now labels each row Deterministic or Judgment, and gives each kind its own resolution format: a Deterministic failure returns a new plain "Gate blocked" report naming the exact gate and missing grant (no `DECIDE` reply, nothing to choose between); a Judgment failure still returns the existing "HITL decision required" format with labeled options. `compile-prompt.py`'s MCP-mode gate text and prose-mode gate text were updated the same way, and the `metco_preflight` MCP tool description was corrected to stop calling its result a HITL decision.
- Motivation: every gate should be treated the same way - named, evidenced, and either passed or blocked - with HITL reserved for the narrow case it actually describes. Funneling deterministic authorization gaps through the HITL ceremony overstated how much of the gate surface is really about human judgment, and made every blocked task look like a decision when most blocks just need an explicit grant.
- Verified against the full fixture suite (`validate-kit.py`: 0 warnings after rebuilding distributions, `test-all.py`: 58/58) and against a live compiled MCP-mode prompt, confirming both the Deterministic and Judgment paths render correctly and `lint-prompt.py` still passes.

## 6.0.7 MCP-Aware Compilation and Compiled-Prompt Trimming - 2026-08-10

- Added three opt-in fields to `REQUEST_SCHEMA` and `compile-prompt.py`'s output, all no-ops when absent so every existing request still compiles a byte-identical prompt: `mcp.enabled` swaps the 8-row Mandatory HITL Gate reasoning table for direct tool calls (`metco_check_capability`, `metco_check_paths`, `metco_preflight`, `metco_record_decision`) against a project's own registered MCP server, falling back to the manual table only if a tool call errors or the connection is unreachable; `reference_scope: "minimal"` trims `required_references` down to only the reference docs whose topic keywords actually appear in the request's outcome/module/acceptance/scope text, always keeping `replit.md` and `ai/metco.md`; `known_context` (owners/callers/tests) replaces the open-ended "go discover the owner, callers, and tests" discovery steps with a targeted verify-what's-already-named instruction. Motivation: the compiler had no way to know a target project had exposed METCO's own gate logic as callable MCP tools, so every compiled Replit prompt kept asking the agent to re-derive gate answers in prose and read a fixed reference set regardless of task size — both pure overhead once the same checks are one deterministic tool call away.
- Verified against the full existing fixture suite (`validate-kit.py`: 0 warnings, `test-all.py`: 58/58) with no fixture touching the new fields, confirming default output is unchanged, then exercised all three fields together on a new ad hoc request and separately confirmed `reference_scope: "minimal"` actually drops references (a database-migration request went from 7 required references to 4) rather than being a no-op in practice.

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
