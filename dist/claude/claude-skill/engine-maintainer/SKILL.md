---
name: engine-maintainer
description: Review, audit, extend, or fix this engine (Replit OpsGate) itself - tools/*.py, canonical/**, manifests, replit-skills, ai instruction references, packaged Claude skills, or the mcp-server/ MCP server - rather than use the engine to generate a business file, spec, audit, backlog, change record, or Replit prompt. Use when the user wants to add or change routing/gate/lexical behavior, edit a replit-skill or ai reference file, add a new Claude skill package, modify the MCP server, or otherwise modify the engine's own source and distributions. Route ordinary artifact-generation requests to project-prompt-router instead.
---

# Engine Maintainer

This is instruction-system maintenance on the engine's own source, not on a target project's installed copy. Follow the same explicit-request discipline `replit.md`'s `instruction_maintenance` capability requires: only touch `canonical/**`, `tools/**`, and `mcp-server/**` the user actually asked about, and never edit `dist/**` directly - it is generated output, not source.

`mcp-server/**` is real source, not a generated copy, but it is deliberately not wired into `build-distributions.py`/`DISTRIBUTIONS` (see `canonical/ENGINE_ADOPTION_GUIDE.md` "Exposing this project's tools remotely") - a change there needs the same `validate-engine.py`/`test-all.py`/version-bump/changelog discipline as `canonical/**`/`tools/**`, but never a distribution rebuild, and should be exercised with a real server boot and client round-trip when the change affects request handling, auth, or tool behavior, not just the static checks.

## Before changing anything

1. Read the exact file(s) in scope plus anything that depends on their current behavior: fixtures in `tools/opsgate_fixtures.py`, the `expected` values inside routing/HITL fixtures, and any other tool that imports or calls the function being changed.
2. State whether the change is additive/opt-in (a new optional request field, a new function, a new tool - existing callers keep their exact current output) or a behavior fix (something was wrong or contradictory and the corrected behavior differs from before). Prefer additive changes; reserve behavior fixes for genuine bugs, contradictions, or the user's explicit request to change default behavior.
3. If a fixture's recorded `expected` values would need to change as a result, treat that as a signal to double-check the change is actually correct - not as routine fixture maintenance to wave through.

## Making the change

1. Edit `canonical/**`, `tools/**`, and/or `mcp-server/**` only - never `dist/**`.
2. If anything under `canonical/**` changed, run `python3 tools/opsgate_tools.py build-distributions` before validating, so the generated `dist/claude` and `dist/replit` copies aren't flagged as drifted.
3. Run `python3 tools/opsgate_tools.py validate-engine` - it must report 0 warnings. Run `python3 tools/opsgate_tools.py test-all` - it must report every check passing. Both must pass before the change is considered done; fix regressions, don't rationalize them.
4. Bump both `package.py`'s `PACKAGE.version` and `tools/opsgate_contracts.py`'s `ENGINE_MANIFEST.version` together (they must always match), and add a `CHANGELOG.md` entry above the previous top entry, in the engine's established style: what changed, the concrete motivation/root cause, and what was verified. A version bump with no changelog entry, or a changelog entry with no version bump, is incomplete.
5. Re-run `validate-engine.py` and `test-all.py` once more after the version/changelog edit, since `opsgate_contracts.py` changed too.

## Reporting

State: files changed and why; whether each change was additive or a behavior fix, with evidence; the before/after version; `validate-engine.py` and `test-all.py` results; any fixture whose `expected` values changed and why that's correct rather than a regression being papered over; and whether the change needs pushing to a remote the engine is vendored or submoduled from elsewhere.

## Never

- Never edit `dist/**` by hand - it is overwritten by `build-distributions.py` and drift checks will flag hand edits as inconsistent with canonical source.
- Never report a change as done without both `validate-engine.py` (0 warnings) and `test-all.py` (full pass) evidence.
- Never bump the version without a changelog entry, or add a changelog entry without bumping the version.
- Never change fixture `expected` values to make a regression pass without stating explicitly that the new value is the correct one and why.
