# Replit OpsGate Claude Project Prompt Engine

This engine turns project requests into detailed business files, implementation specifications, audits, task backlogs, controlled change records, and governed Replit Agent prompts. Version 6 preserves automatic internal process-mode routing and the strict three-case HITL pause/resume flow, and adds first-class module business-file audit updates plus delta spec generation from business MD versus existing spec files.

## Contents

- `CLAUDE_PROJECT_INSTRUCTIONS.md`: Claude project instructions.
- `templates/`: business, specification, audit, backlog, change/improvement, bounded Replit, phased Replit, three-case HITL decision, and intake templates.
- `references/replit.md`: authoritative Replit scope, modes, and safety policy.
- `references/ai/`: progressively loaded domain instruction objects.
- `references/replit-skills/`: Replit Agent workflows for focused scenarios.
- `specifications/`: detailed normative architecture, mode, routing, artifact, execution, HITL, and distribution specifications.
- `examples/`: compact example output.
- `claude-skill/project-prompt-router/`: selects the correct artifact template.
- `claude-skill/replit-task-builder/`: builds bounded or phased Replit prompts.
- `claude-skill/*.zip`: packaged skills.

## Setup

1. Paste `CLAUDE_PROJECT_INSTRUCTIONS.md` into the Claude project instructions.
2. Upload `references/`, `templates/`, `specifications/`, and optionally `examples/`.
3. Keep one current version of each file.
4. Install the packaged router and Replit task-builder skills when reusable Claude Skills are preferred.

Replit workflows cover bounded frontend/API work, architecture refactors, full-stack features, auth/permissions, forms, tables/reporting, UI/UX, schema migrations, seeding, bug diagnosis, performance optimization, verification, and instruction maintenance.

## Replit installation

Copy:

- `references/replit.md` to project-root `replit.md`
- `references/ai/**` to project-root `ai/**`
- `references/replit-skills/**` to project-root `.agents/skills/**`

For an upgrade from version 5.5 to 6, replace `replit.md`, all `ai/**` files, and all `.agents/skills/**` folders because automatic mode selection is distributed across the root, domain references, and scenario skills. Do not copy `templates/`, `specifications/`, `CLAUDE_PROJECT_INSTRUCTIONS.md`, or `claude-skill/` into Replit; those generate and validate prompts on the Claude side.

## Design

- Root files define authority once.
- Domain files load only when relevant and expose responsibility, activation, inputs, `Must Not`, workflow, and output evidence.
- The generator selects one internal mode and one primary scenario skill automatically; users never need to choose them.
- Internal modes cover business definition, specifications, audits, backlogs, change control, prompt generation, frontend, API, full-stack, auth, forms, tables, refactors, schema evolution, seeding, diagnosis, performance, UI/UX, verification, and instruction maintenance.
- Modes and skills select procedure but never grant authority; root capability gates and explicit scope remain controlling.
- Loaded instruction objects guide behavior inside approved scope; they never expand access or replace Python contracts.
- The router selects templates by immediate deliverable, not keywords alone.
- Work that cannot be safely delivered as one batch produces separate gated phase prompts sequentially.
- Only the next authorized phase receives a full prompt; later prompts use verified handoffs.
- Bounded work starts from named paths and stops discovery once ownership, consumers, and checks are proven.
- HITL pauses only for an unknown answer/next step, two materially correct answers, or a self-invented decision that would change scope.
- A HITL request stops the entire Replit task. Replit waits for the matching human answer, validates it and scoped drift, then resumes the exact blocked step without restarting completed work.
- HITL has no modes or risk levels and never replaces authorization, stop conditions, or protected-path rules.
- Generated prompts include only applicable requirements and checks.
- Detailed specification files define requirement records, interface contracts, traceability, state coverage, verification, and distribution parity.
- `PASSED`, `FAILED`, and `NOT RUN` keep verification honest.

## Adopting this engine in a different Replit project

This engine is meant to be dropped into other projects as a submodule (or a vendored copy) - which means its own git history ships to every project that reuses it. A profile that describes one specific project's own write roots and protected paths is fine as generic infrastructure, but that project's actual business facts (roles, permissions, ID formats, billing rules - whatever `ai/metco.md` holds for METCO) are that project's own data, not this engine's. Baking a project's profile and business file into `opsgate_contracts.py`/`canonical/references/ai/` the way the original `metco` profile still does means every other adopting project's submodule checkout carries METCO's business facts around for no reason.

So a new profile's config and business file are written entirely **outside this engine's own repo**, in the consuming project's own root - the same place `replit.md` and `ai/**` already end up after the "Replit installation" copy step above. Nothing about adopting a new project ever needs to touch a file inside this engine.

### Setup process: `tools/apply-setup.py` (the primary path)

This only applies when the engine itself is vendored into the project (as a submodule or a full copy) - the trimmed copy-only install described above (just `replit.md`, `ai/**`, `.agents/skills/**`, no `tools/`, no `canonical/`) has nothing to run it with, and `replit.md`'s own first-run check knows to skip straight past setup and fall back to `generic-replit` in that case rather than getting stuck looking for tooling that was never copied in.

When the engine is vendored, this is meant to be run by the Replit Agent itself, not typed by hand - `replit.md`'s own "First-run setup check" (its very first section) tells the Agent exactly this, automatically, the first time it works on a project that hasn't been set up yet:

1. Copy `canonical/templates/PROJECT_SETUP_TEMPLATE.md` to the project root as `PROJECT_SETUP.md` - one plain-language fill-in form covering the profile key, project name, frontend/backend roots, extra protected paths, and the same Business Facts questions `ai/metco.md` answers (roles, lifecycle, ID formats, key business rules, design system, known drift).
2. This engine exists for people with no technical background, so the user should do as little as possible: detect the technical fields yourself first (frontend/backend roots from the project's actual folder structure, the profile key derived from the project's name) and only ask the user, in plain everyday language, for what truly needs their own knowledge - the project's name and the Business Facts. Write every answer into the file yourself; the user never opens or edits it.
3. Run `python3 <engine-dir>/tools/apply-setup.py --template PROJECT_SETUP.md --target-root .`

That one command writes, all at the project's own root:

- `opsgate.profile.json` and `ai/<profile>.md` - same shape and same shared logic (`tools/opsgate_setup_lib.py`) as `tools/init-profile.py` below, except the Business Facts section is filled in directly from the template's answers instead of left as placeholders, since a human already answered them.
- `ai/*.md` - the engine's generic domain files (`backend.md`, `frontend.md`, `database.md`, and the rest), copied over if not already present. These apply to any project unchanged and need no project-specific filling in.
- `replit.md` - a copy of the engine's canonical `replit.md` with the "This project's configuration" section filled in with a literal, human-readable summary of every profile currently configured (roots, protected paths, business file) - not just a note to go look it up dynamically. Re-running setup for a second profile updates this summary to list all configured profiles, not just the newest one.

`apply-setup.py` never overwrites an existing profile key (edit `opsgate.profile.json` by hand instead) and never overwrites an existing `ai/*.md` file without `--force`, so running it again to add a second profile is safe and additive.

### `tools/init-profile.py` (flags-only, for scripted/CI use)

The lower-level primitive `apply-setup.py` itself calls into (see `tools/opsgate_setup_lib.py`) - useful directly when scripting setup without a human filling in a template, e.g. from CI:

```
python3 tools/init-profile.py --profile acme --target-root /path/to/outer-project --frontend-root client/src --backend-root server/src
```

`--target-root` is the *outer* project's own root - not this engine's directory. Run from inside the engine (as it would be when embedded as a submodule), this writes two files at the outer project's root and touches nothing inside the engine (it does not materialize `replit.md`/`ai/*.md` the way `apply-setup.py` does - only the profile config and a placeholder business file):

1. `<target-root>/opsgate.profile.json` - a small JSON file holding the new profile's `frontend_root`/`backend_root`, `description`, `business_file` name, and any `--extra-never-access <glob>` (repeatable) on top of the universal baseline (`.git/**`, `.env`, `node_modules/**`, `.github/workflows/**`, `.claude/**`, `.agents/memory/**`). `tools/opsgate_profiles.py`'s `read_json()` merges this on top of the built-in `metco`/`generic-replit` profiles at runtime, for every tool, automatically - `active_profile()`, `protected_paths_for()`, `show-profile`, `compile-prompt` all see it with no other change needed.
2. `<target-root>/ai/<profile>.md` - a starter business file structured like `ai/metco.md` (Responsibility, Activation, Inputs, a `## Business Facts` section left as fill-in placeholders, `Must Not`, `Start record`, `Workflow`, `Output Evidence`), written directly to where the Replit installation step already expects a project's `ai/**` files to live - no copy step needed for this file specifically.

It never edits an existing profile (re-running with a profile key already in `opsgate.profile.json` refuses and tells you to edit that file by hand) and never overwrites an existing business file without `--force`.

After the first run for a given outer project, `--target-root` can be omitted on later calls (adding a second, third, etc. profile to the same project) - the tool walks up from the current directory looking for an existing `opsgate.profile.json`, the same way the runtime resolver does.

**How the engine finds that file at runtime**, since it has no inherent idea where the outer project's root is when running from inside a submodule: the `OPSGATE_PROFILE_CONFIG` environment variable, if set, points at it explicitly. Otherwise every tool walks up from the current working directory looking for a file named exactly `opsgate.profile.json`, skipping the .git-based stop at the *starting* directory specifically (the engine's own submodule root almost always has its own `.git`, and that must not stop the walk before it ever climbs out into the outer project), stopping once it reaches a directory with its own `.git` and no config file there, or after 12 levels. Once found, `OPSGATE_PROFILE=<profile>` (or `"profile": "<profile>"` on a request) selects it exactly like a built-in profile.

After running it: fill in the generated business file's `## Business Facts` section, set `OPSGATE_PROFILE=acme` (a Repl Secret is the usual place), and that's the whole setup - nothing in this engine's own repo changes or needs rebuilding.

### Doing it by hand instead

If you'd rather not run the script: write `<target-root>/opsgate.profile.json` yourself (see `tools/opsgate_profiles.py`'s `load_external_profile_config()` for the exact shape expected under its `"profiles"` key) and `<target-root>/ai/<profile>.md` following `ai/metco.md`'s structure.

Everything else in the engine - routing, capability gates, the HITL protocol, the lexical scoring/tie detection, MCP tool wiring - is already project-agnostic and needs no change to adopt elsewhere.

### Known migration debt: `metco` itself is still a built-in, not an external profile

The `metco` profile and `ai/metco.md` still live inside this engine's own `PROFILES`/`PROTECTED_PATHS` and `canonical/references/ai/`, for backward compatibility with the live deployment that depends on them resolving without any external file present. That is exactly the coupling this section exists to avoid for every *other* project - `metco` just hasn't been migrated to its own `opsgate.profile.json` in METCO's own project root yet. Once that migration happens (write METCO's real profile + business file into METCO's own repo as an external profile, confirm it resolves identically, then delete the built-in `metco` entries and `ai/metco.md` from this engine), the engine carries no project-specific data of its own at all. Until then, treat the built-in `metco` profile as legacy, not as the pattern to copy for a new project.

### Why `ai/*.md` files mention "protected paths" without listing any

Files under `ai/` (`backend.md`, `database.md`, `maintenance.md`, and the rest, including a project's own business file whether built-in like `ai/metco.md` or external like a generated `ai/acme.md`) use "protected", "locked", and "restricted" only as behavioral vocabulary - instructions like "do not touch protected paths without authorization." None of them declare or duplicate an actual glob list. The one and only source of truth for what counts as protected on a given profile is `PROTECTED_PATHS`/`protected_paths_for(request)` in `tools/opsgate_contracts.py` (merged with any external `opsgate.profile.json` at runtime); every `ai/*.md` reference to "protected" defers to whatever that resolves for the active profile, so there is nothing to keep in sync by hand when a profile's protected paths change.

### Exposing this project's tools remotely: `mcp-server/opsgate_mcp_server.py`

`replit.md` Section 10 ("MCP tool availability") has always described an `opsgate_`-prefixed MCP tool surface as *something a project could register* - it never shipped an actual server. `mcp-server/opsgate_mcp_server.py` is that server: an HTTP ("streamable-http" transport) MCP server, built on the official `mcp` Python SDK, that exposes the same 14 runtime `cmd_*` functions from `tools/opsgate.py` the CLI scripts call (`opsgate_route_request`, `opsgate_check_capability`, `opsgate_check_paths`, `opsgate_preflight`, `opsgate_show_profile`, `opsgate_init_state`, `opsgate_init_run`, `opsgate_compile_prompt`, `opsgate_next_phase_prompt`, `opsgate_intake_request`, `opsgate_parse_report`, `opsgate_lint_report`, `opsgate_lint_prompt`, `opsgate_record_decision`) as MCP tools with matching names. It is a thin adapter, not a reimplementation - each tool writes its input to a temp file, calls the real `cmd_*` function, captures what it printed, and returns that; if `opsgate.py` changes, this file does not need to. See `mcp-server/README.md` for the full tool table, run instructions, and how it resolves which project's profile/protected-paths apply.

Running this file only starts the server on whatever machine runs it (e.g. a developer's own laptop) - it is not reachable by a remote agent like Replit's cloud Agent until it's exposed through a tunnel (ngrok, Cloudflare Tunnel, Tailscale Funnel, etc.) and that tunnel's public HTTPS URL is registered in Replit's "Connect via MCP" settings. Setting up that tunnel is a separate step from running the server itself.

Once exposed, the server is on the open internet, so every request must carry an `X-Opsgate-Token: <token>` header - a custom header rather than the standard `Authorization` header because free quick-tunnel providers reject requests carrying `Authorization` at the edge. Set a stable token with `--token` or `OPSGATE_MCP_TOKEN` (or `mcp-server/.env`, gitignored) before exposing the server; see `mcp-server/README.md` for the full auth details.

Deliberately not wired into `build-distributions.py`/`DISTRIBUTIONS` - `mcp-server/` ships only with a full checkout or submodule of this engine, not inside the trimmed `dist/replit-install`/`dist/claude` packages. A project using only the copy-only install has no `tools/` for it to import from anyway.

## Maintenance

Edit canonical files under `references/`, `templates/`, and `specifications/`, rebuild generated distributions, validate all skill folders, and keep packaged/source copies identical. See root `README.md`'s "Distribution model" section for the full `canonical/` → `dist/` architecture and the commands that enforce it.
