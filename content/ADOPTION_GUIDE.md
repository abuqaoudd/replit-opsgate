# OpsGate Adoption Guide

This engine turns project requests into detailed business files, implementation specifications, audits, task backlogs, controlled change records, and governed Replit Agent prompts. It preserves automatic internal process-mode routing and the strict three-case HITL pause/resume flow, with first-class module business-file audit updates plus delta spec generation from business MD versus existing spec files.

## Contents

- `templates/`: business, specification, audit, backlog, change/improvement, bounded Replit, phased Replit, three-case HITL decision, and intake templates.
- `references/replit.md`: authoritative Replit scope, modes, and safety policy.
- `references/ai/`: progressively loaded domain instruction objects.
- `references/replit-skills/`: Replit Agent workflows for focused scenarios.
- `specifications/`: detailed normative architecture, mode, routing, artifact, execution, and HITL specifications.

This engine is used as a hosted MCP service (`mcp-server/opsgate_mcp_server.py`, see "Exposing this engine remotely" below) - there is no separate Claude-side package to paste or install.

Replit workflows cover bounded frontend/API work, architecture refactors, full-stack features, auth/permissions, forms, tables/reporting, UI/UX, schema migrations, seeding, bug diagnosis, performance optimization, verification, and instruction maintenance.

## Replit installation

Copy:

- `references/replit.md` to project-root `replit.md`
- `references/ai/**` to project-root `ai/**`
- `references/replit-skills/**` to project-root `.agents/skills/**`

For an upgrade from version 5.5 to 6, replace `replit.md`, all `ai/**` files, and all `.agents/skills/**` folders because automatic mode selection is distributed across the root, domain references, and scenario skills. Do not copy `templates/` or `specifications/` into Replit; those are this engine's own authoring/validation material, not runtime content for the target project.

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

## Adopting this engine for a different Replit project

Each project's own business facts (roles, permissions, ID formats, billing rules) are that project's own data, not this engine's - they live in the tenant store (`tools/opsgate_tenants.py`, backed by `tenants/registry.json`, gitignored), never baked into this engine's own repo or git history. Nothing about adopting a new project ever needs to touch a canonical file inside this engine.

### Setup: create a tenant

From a Python session with `tools/` on the path (or via a small script the team running this server maintains):

```python
import opsgate_tenants as tenants

tenants.create_profile(
    "acme",
    frontend_root="client/src",
    backend_root="server/src",
    extra_never_access=["legacy-service/**"],  # optional, on top of the universal baseline
)
token = tenants.issue_token("acme", label="replit-connector")  # returned once, in plaintext - deliver it to the tenant
```

That's the whole setup. Give the tenant its token; they set it as the `X-Opsgate-Token` header value when connecting to this engine's MCP server (Replit's "Connect via MCP" custom-header config, or any MCP client that supports custom headers). Every gate/routing tool call they make resolves against `"acme"`'s own profile and protected paths automatically - no local file, no copy step, no rebuild.

`label` is optional but worth setting on every token you issue: a short, non-secret note on what that specific token is *for* (e.g. `"replit-connector"`, `"oauth-backing"`, `"ci-pipeline"`). Never used for authorization - purely so `tenants.list_tokens("acme")` can answer "what is this token actually used for" later, instead of a guess. Mint a separate, distinctly-labeled token per consumer rather than handing the same one to two different callers - a token is a single on/off switch, and revoking one revokes every consumer relying on that exact string, with no warning that anything else was riding along.

Add a second tenant the same way, any time, without touching the first. `update_profile()` changes an existing tenant's roots/protected paths; `issue_token()`/`revoke_token()` manage credentials independently of profile data.

Once a tenant's Replit project actually has this server's MCP tools registered (not just a token issued - the tools genuinely reachable from that project), set `mcp_enabled=True` on its profile (`tenants.update_profile("acme", mcp_enabled=True)`). `opsgate_compile_prompt` then defaults every compiled Replit prompt for that tenant to the "call these tools directly" HITL gate (`opsgate_check_capability`/`opsgate_check_paths`/`opsgate_preflight`/`opsgate_record_decision`) instead of the manual prose reasoning table - without every caller needing to remember to pass `request["mcp"]["enabled"]` itself on every single compile call. An explicit `request["mcp"]` field, if the caller supplies one, always overrides this default in either direction. Defaults to unset/off for a new tenant, since a token being issued doesn't by itself mean the target project's MCP connection actually exists yet.

### Why `ai/*.md` files mention "protected paths" without listing any

Files under `ai/` (`backend.md`, `database.md`, `maintenance.md`, and the rest, including a tenant's own business file if it has one) use "protected", "locked", and "restricted" only as behavioral vocabulary - instructions like "do not touch protected paths without authorization." None of them declare or duplicate an actual glob list. The one and only source of truth for what counts as protected for a given tenant is `opsgate_tenants.protected_paths_for_tenant(tenant_id)` (universal baseline from `tools/opsgate_contracts.py`, merged with that tenant's own `extra_never_access`); every `ai/*.md` reference to "protected" defers to whatever that resolves, so there is nothing to keep in sync by hand when a tenant's protected paths change.

### Exposing this engine remotely: `mcp-server/opsgate_mcp_server.py`

An HTTP ("streamable-http" transport) MCP server, built on the official `mcp` Python SDK, exposing this engine's routing/gate/lint tools and knowledge resources directly - see `mcp-server/README.md` for the full tool/resource table, run instructions, and tenant resolution.

Running this file only starts the server on whatever machine runs it (e.g. a developer's own laptop, or a hosted always-on process) - it is not reachable by a remote agent like Replit's cloud Agent until it's exposed through a tunnel (ngrok, Cloudflare Tunnel, Tailscale Funnel, etc.) and that tunnel's public HTTPS URL is registered in Replit's "Connect via MCP" settings, or it is deployed behind a stable hostname directly. Setting that up is a separate step from running the server itself.

Once exposed, the server is on the open internet, so every request must carry an `X-Opsgate-Token: <token>` header - a custom header rather than the standard `Authorization` header because free quick-tunnel providers reject requests carrying `Authorization` at the edge. A tenant's own issued token (see "Setup" above) authenticates and resolves their tenant in one step; `--token`/`OPSGATE_MCP_TOKEN` (or `mcp-server/.env`, gitignored) is the separate shared secret for admin/shared access with no tenant token. See `mcp-server/README.md` for the full auth details.

## Maintenance

Edit canonical files under `references/`, `templates/`, and `specifications/` directly - they are read live by `tools/opsgate_knowledge.py` and the MCP server, not copied or rebuilt. Run `python3 tools/opsgate.py validate-engine` and `python3 tools/opsgate.py test-all` before release.
