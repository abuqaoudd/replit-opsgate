# opsgate MCP server

Exposes this engine's own gate/routing/lint tools (`tools/opsgate.py`) as an
HTTP-based MCP server, so a remote agent (e.g. Replit's Connect via MCP) can call
them directly instead of an agent inside this repo shelling out to the CLI.

Every tool here calls the same pure core functions the CLI's own `cmd_*` wrappers call
(`check_paths_result`, `preflight_result`, etc., in `tools/opsgate.py`/`tools/opsgate_prompts.py`)
directly, in-process - no temp files, no subprocess, no stdout capture. The CLI wrappers still
exist unchanged for `python3 tools/opsgate.py <command>`, but this server calls straight past
them into the pure functions they themselves call, so `opsgate.py`/`opsgate_prompts.py`/
`opsgate_tenants.py` stay the single source of truth for both callers.

## Where this lives

`<engine-dir>/mcp-server/opsgate_mcp_server.py`, as a sibling of `tools/` and
`content/`. It imports `opsgate.py` directly from the real `tools/`
directory next to it, so paths and profile resolution behave exactly as they do
for the CLI.

## Install

Requires **Python 3.10+** (the `mcp` package's own minimum - check with `python3 --version`
first; on a machine whose default `python3` is older, install a newer interpreter and use
that instead, e.g. via a dedicated venv).

```
pip install -r mcp-server/requirements.txt
```

`requirements.txt` pins `mcp>=1.27.0,<2.0.0` - `mcp` 2.0.0 restructured its module layout
(`mcp.server.fastmcp.FastMCP`, which this file imports, no longer exists there), so an
unpinned `pip install mcp` would install a version this file cannot run against.

## Run

```
python3 <engine-dir>/mcp-server/opsgate_mcp_server.py --host 127.0.0.1 --port 8765
```

Flags default to `OPSGATE_MCP_HOST` / `OPSGATE_MCP_PORT` env vars, then
`127.0.0.1:8765`. One process, two separate MCP mount paths - see "Two tool
surfaces, one process" below for why:

- `http://<host>:<port>/mcp/replit/` - Replit's own implementation-time gate/profile/decision/sync tools.
- `http://<host>:<port>/mcp/claude/` - Claude's prompt-compiler chain (intake/route/compile/next-phase/parse/lint/init/export).

**The trailing slash matters.** Hitting the bare path (`/mcp/replit`, no
trailing slash) gets a `307 Temporary Redirect` to the same URL with a
trailing slash added - each mount's own route is registered at `/`, and
Starlette only treats the mount prefix's bare remainder as a redirect
candidate, not a direct match. A `307` on a `POST` is exactly the kind of
thing a real MCP client might not follow correctly (confirmed the redirect
happens; not confirmed every client handles it) - so configure the
trailing-slash URL directly in whichever client connects, rather than relying
on the redirect.

This only starts the server locally - it is not reachable from Replit's cloud
Agent until it's exposed through a tunnel (ngrok, Cloudflare Tunnel, Tailscale
Funnel, etc.) and that tunnel's public HTTPS URL is registered in Replit's
"Connect via MCP" settings (pointed at the `/mcp/replit/` path specifically).
That's a separate step from just running this file.

## Process supervision

Running the command above directly (or via `nohup ... & disown`) means nothing restarts it if
it ever crashes - it just stays down until someone notices. `mcp-server/com.opsgate.mcpserver.plist`
is a `launchd` LaunchAgent that keeps it running: starts it on login (`RunAtLoad`) and restarts
it on any exit (`KeepAlive`), with a 10-second `ThrottleInterval` so a crash loop doesn't spin
the CPU. Logs go to `~/Library/Logs/opsgate-mcp-server.log` (a stable location, unlike `/tmp`,
which can be cleared on reboot).

Install:

```bash
cp mcp-server/com.opsgate.mcpserver.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.opsgate.mcpserver.plist
```

Uninstall (stop and remove the supervised service - does not touch anything else, tenant data
included):

```bash
launchctl bootout gui/$(id -u)/com.opsgate.mcpserver
rm ~/Library/LaunchAgents/com.opsgate.mcpserver.plist
```

After editing `opsgate_mcp_server.py`, `opsgate_oauth.py`, any file under `tools/`, or
`mcp-server/.env`, the running process still needs a restart to pick up the change (Python
doesn't hot-reload, and `.env` is only read once at startup) - with the LaunchAgent installed,
that's `launchctl kickstart -k gui/$(id -u)/com.opsgate.mcpserver` instead of manually killing
and re-launching the process; `KeepAlive` brings it straight back up. The plist file itself
(`mcp-server/com.opsgate.mcpserver.plist`) is only read at `bootstrap`/`load` time - editing it
requires `bootout` then `bootstrap` again, not `kickstart`, for the change to take effect.

## Docker

`Dockerfile`, `docker-compose.yml`, and `.dockerignore` at the repository root package this
server as a container. This exists because the current hosting - a launchd-supervised process on
one personal machine, reached through a personal Tailscale Funnel - is a single point of failure
for every connected project and has to be replaced with real server infrastructure; the image is
the deployment unit for that move (the technical documentation's Section 12 sets out why and how).

The build context is the repository root, not `mcp-server/`, because the
server imports the engine from the sibling `tools/` folder, reads `content/**` live, and
persists state under `tenants/` and `runs/` at the repository root - the repo layout *is* the
runtime layout, mirrored one-to-one under `/app` in the image.

What the image does and does not contain:

- **Baked in**: `mcp-server/`, `tools/`, `content/`, `fixtures/`, `package.py`. A change to any
  of these is a rebuild (`docker compose up -d --build`).
- **Never baked in** (`.dockerignore`): `mcp-server/.env` (real secrets), `tenants/` and `runs/`
  (live state), `.git/`, `.venv/`, `tests/`, `docs/`. The image contains no credentials and no
  tenant data - it is safe to push to a registry.
- **Runs as an unprivileged user** (`opsgate`, uid 10001). `tenants/registry.json` is chmod'ed to
  `0600` on every save, so the state directories must be writable by that uid - the named
  volumes below inherit the right ownership automatically on first mount. If you use bind
  mounts instead, `chown -R 10001:10001` them first.
- **Binds `0.0.0.0` inside the container** (`OPSGATE_MCP_HOST`), because a published port cannot
  reach a loopback-only process. This does not widen what the server answers to: the mcp SDK's
  DNS-rebinding protection still rejects any `Host` header other than `127.0.0.1`/`localhost`
  and whatever `OPSGATE_MCP_ALLOWED_HOSTS` lists. Compose publishes the port on
  `127.0.0.1:8765` only, so the container is reachable from the host but not from the network
  - put a TLS-terminating reverse proxy in front of it, exactly as the Tailscale Funnel sits in
  front of the current process.

### Run with compose

```bash
cp mcp-server/.env.example mcp-server/.env   # fill in OPSGATE_MCP_TOKEN, OPSGATE_MCP_ALLOWED_HOSTS, OAuth values
docker compose up -d --build
curl -s http://127.0.0.1:8765/health          # {"status":"ok"}
```

`docker-compose.yml` reads `mcp-server/.env` through `env_file` - the same file, same keys,
as the non-container deployment (`.env.example` documents every one). State lives in two named
volumes, `opsgate-tenants` and `opsgate-runs`. They are plain files, not a database: losing
them loses every tenant, token hash, run, decision, and audit entry, so back them up like any
other stateful volume.

### First run: provision a tenant

A fresh volume has no tenants. Use the engine CLI *inside the container*, so it writes to the
mounted volume rather than to the host checkout:

```bash
# 1. Register the tenant (a JSON file with tenant_id, frontend_root, backend_root, optional
#    extra_never_access / business_file / description - see tools/opsgate.py admin-create-tenant).
#    The CLI resolves its argument to a real path, so /dev/stdin does not work - write the JSON
#    to a file inside the container first. `-T` disables the pseudo-TTY so stdin pipes through.
docker compose exec -T opsgate-mcp sh -c 'cat > /tmp/tenant.json && python tools/opsgate.py admin-create-tenant /tmp/tenant.json' <<'EOF'
{"tenant_id": "my-project", "frontend_root": "client/src", "backend_root": "server"}
EOF

# 2. Mint one token per consumer. The plaintext is printed exactly once - only its hash is stored.
docker compose exec opsgate-mcp python tools/opsgate.py admin-issue-token my-project --label claude
docker compose exec opsgate-mcp python tools/opsgate.py admin-issue-token my-project --label replit
```

Then verify the token resolves to the right tenant before handing it to a client:

```bash
curl -s -H "X-Opsgate-Token: <token>" -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" http://127.0.0.1:8765/mcp/replit/ \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```

A `200` with a `serverInfo` payload confirms authentication and the mount; a `401` means the
token did not resolve; a `421` means the `Host` header you used is not in
`OPSGATE_MCP_ALLOWED_HOSTS`.

### Operations

- **Logs**: `docker compose logs -f opsgate-mcp` (uvicorn access log + the server's own stderr).
  The structured per-tool-call audit log is `runs/audit.jsonl` *inside the `opsgate-runs`
  volume*, not in the container log.
- **Restart after a code change**: `docker compose up -d --build`. A change under `content/**`
  also needs a rebuild here, because content is baked into the image (unlike the bare-process
  deployment, where it is read live from the checkout). To keep content hot-editable, bind-mount
  it read-only instead: add `- ./content:/app/content:ro` under `volumes`.
- **Health**: the container's `HEALTHCHECK` hits `GET /health`, which also confirms
  `tenants/registry.json` parses - a corrupted registry shows as `unhealthy`, not just as a
  process that answers HTTP.
- **Migrating existing state in**: copy the current `tenants/registry.json` and `runs/**` into
  the volumes (`docker compose cp tenants/registry.json opsgate-mcp:/app/tenants/` and the same
  for `runs/`), then `docker compose exec opsgate-mcp chmod 600 tenants/registry.json`. This is
  the one true state migration described in the technical documentation's hosting section;
  everything else is a fresh code deploy.

## Authentication

Every request must carry an `X-Opsgate-Token: <token>` header, checked by a
small ASGI middleware in front of the MCP app - there is no unauthenticated
path, regardless of `--host`. This matters because the server has real side
effects (`opsgate_init_run` writes to disk, `opsgate_record_decision` appends
to a log) and is designed to end up reachable through a public tunnel.

It's a custom header, not the standard `Authorization` header, because
Cloudflare's free, account-less "quick tunnels" (`cloudflared tunnel --url
...`, no login required) reject any request carrying an `Authorization`
header at the edge with `421 Invalid Host header` - confirmed empirically,
never even reaching this server. A custom header carries the same secret with
the same protection and passes through untouched.

Set a stable token with `--token` or `OPSGATE_MCP_TOKEN` (recommended, so it
survives restarts and you can put the same value into Replit's "Connect via
MCP" custom-header config). If neither is set, the server generates a random
token at startup and prints it once to stderr - fine for a quick local test,
but it changes every restart, so a saved MCP client config would need updating
each time.

A request without a valid token gets `401 {"error": "unauthorized - missing or invalid x-opsgate-token header"}`.

### OAuth (for Claude's org-level "custom connector" flow)

Claude's own org-level Connectors feature (`claude.ai/customize/connectors`, distinct from a
Claude Code plugin's `.mcp.json`) is OAuth-only - there is no field for a static header there.
`opsgate_oauth.py` adds a minimal OAuth 2.1 + PKCE authorization server, just enough to satisfy
that flow, alongside the `X-Opsgate-Token` model above - not a replacement for it. Its
`/token` endpoint doesn't mint a new kind of credential: a successful, PKCE-verified code
exchange hands back one of this server's own existing `X-Opsgate-Token` values
(`OPSGATE_OAUTH_BACKING_TOKEN`) as the OAuth `access_token`, and `TokenAuthMiddleware` accepts
that value via `Authorization: Bearer <token>` exactly as it would via the custom header - so
tenant resolution above is completely unaffected by which path a caller used to get the token.

Setup: generate a client id/secret (`python3 -c "import secrets; print(secrets.token_urlsafe(16))"`
for the id, `secrets.token_urlsafe(32)` for the secret), issue a **dedicated** tenant token for
`OPSGATE_OAUTH_BACKING_TOKEN` (`opsgate_tenants.issue_token(tenant_id, label="oauth-backing")`
- never reuse a token some other consumer already has, since revoking one revokes both with no
warning; `opsgate_tenants.list_tokens(tenant_id)` shows every token's label so this is checkable
later), set `OPSGATE_OAUTH_CLIENT_ID`/`OPSGATE_OAUTH_CLIENT_SECRET`/`OPSGATE_OAUTH_BACKING_TOKEN`
in `.env`, then paste the name/URL/client id/secret into Claude's "Add connector" form - no
Dynamic Client Registration (RFC 7591) is implemented or required; Claude's form registers a
static client ahead of time. Endpoints exposed at the server root (not under either `/mcp/*`
mount, since a caller has no credential yet when reaching them): `/.well-known/oauth-
authorization-server`, `/.well-known/oauth-protected-resource`, `/authorize`, `/token`.

Set `OPSGATE_OAUTH_ALLOWED_REDIRECT_URI` to pin `/authorize` to one known `redirect_uri`,
closing an open-redirect surface that otherwise exists (consistency between `/authorize` and
`/token` is still enforced either way - a code can only be redeemed with the exact
`redirect_uri` it was issued for). For Claude's own org-level connector flow, the confirmed
real value - from a live connector setup, not documentation - is
`https://claude.ai/api/mcp/auth_callback`.

**Verified live against a real Claude org-level connector** (2026-08-19): added it through
Claude's actual "Add connector" UI with the credentials above, watched the real request
sequence land in this server's log (`GET /.well-known/oauth-protected-resource` → `GET
/.well-known/oauth-authorization-server` → `GET /authorize?...redirect_uri=https%3A%2F%2Fclaude.ai%2Fapi%2Fmcp%2Fauth_callback...`
→ `POST /token`), and confirmed a real tool call (`opsgate_show_profile`) through the connector
returned real `metco` tenant data - not a simulated/curl-only test.

## Which project's profile it answers for

Every request resolves to exactly one tenant, by identity, not by cwd or environment variable:

- If the `X-Opsgate-Token` header value matches a real tenant's issued token
  (`tools/opsgate_tenants.py`'s `tenants/registry.json`), that tenant's own profile and
  protected paths govern the call.
- Otherwise (the shared-secret auth path, or a revoked/unknown tenant token that still matches
  the shared secret) the call resolves to `opsgate_tenants.LOCAL_DEV_TENANT_ID` (`"local-dev"`)
  - a small built-in default with no frontend/backend roots assumed, always available even on a
  fresh checkout with an empty tenant registry.

`opsgate_show_profile` reports which tenant resolved the call either way. A deployment that
wants `local-dev` to have real roots can register it like any other tenant
(`opsgate_tenants.create_profile("local-dev", ...)`) - a real registry entry always takes
precedence over the built-in default.

## Two tool surfaces, one process

Names match the convention `replit.md` Section 9 ("MCP tool availability")
already documents - `opsgate_` prefix. Replit and Claude call this server for
different reasons - Replit runs gate checks on its own implementation work;
Claude compiles governed prompts *for* Replit, upstream of any implementation,
then parses Replit's reports back (see `ADOPTION_GUIDE.md` for the full
chain). So each gets its own mount with only the tools its role needs, rather
than one tool list serving neither role cleanly. **This is a discoverability
split, not a security boundary** - both mounts sit behind the same
`TokenAuthMiddleware`/tenant resolution (a valid token authenticates
identically against either path), and the gates inside each tool call are
what actually enforce authorization either way.

### `/mcp/replit/` - 16 tools

| Tool | Calls | Input | Output |
|---|---|---|---|
| `opsgate_check_capability` | `opsgate.check_capabilities_result` | `request` (object) | JSON |
| `opsgate_check_paths` | `opsgate.check_paths_result` | `request` (object) | JSON |
| `opsgate_preflight` | `opsgate.preflight_result` | `request` (object) | JSON |
| `opsgate_show_profile` | `opsgate.show_profile_result` | `request` (object, optional) | JSON |
| `opsgate_record_decision` | `opsgate.record_decision_result` | `hitl_id` + `answer` (strings) | JSON - **appends to `runs/<tenant-id>/decisions.pylog` on this server's machine** |
| `opsgate_sync_instructions` | `opsgate_knowledge.project_files_manifest` | none | JSON - `{path, size}` for every file in the instruction system, no content (see below for why) |
| `opsgate_sync_file` | `opsgate_knowledge.project_file_text` | `path` (string, from the manifest above) | JSON - `{path, content}` for that one file; the caller must write it itself, this server cannot |
| `opsgate_list_own_tokens` | `opsgate.list_own_tokens_result` | none | JSON - label/admin flag for every token issued to the caller's own tenant, never the token values |
| `opsgate_issue_own_token` | `opsgate.issue_own_token_result` | `label` (string, optional) | JSON - **mints and returns a new non-admin token for the caller's own tenant, shown once** |
| `opsgate_revoke_own_token` | `opsgate.revoke_own_token_result` | `token` (string) | JSON - revokes `token` only if it belongs to the caller's own tenant, otherwise errors |
| `opsgate_list_audit_log` | `opsgate.list_audit_log_result` | `limit` (int, optional) | JSON - the caller's own tenant's recent tool-call audit entries, most recent first |
| `opsgate_quota_usage` | `opsgate.quota_usage_result` | none | JSON - the caller's own tenant's call volume over last hour/24h/7d plus a per-tool breakdown; **visibility only, no rate limit is enforced** |
| `opsgate_admin_create_tenant` | `opsgate.admin_create_tenant_result` | `tenant_id` + optional profile fields | JSON - **ADMIN ONLY** (rejects a non-admin-flagged token); registers a brand-new tenant |
| `opsgate_admin_list_tenants` | `opsgate.admin_list_tenants_result` | none | JSON - **ADMIN ONLY**; every tenant's own public profile, not just the caller's |
| `opsgate_admin_issue_token` | `opsgate.admin_issue_token_result` | `tenant_id` + `admin`/`label` (optional) | JSON - **ADMIN ONLY**; mints a token for any tenant, optionally admin-flagged, shown once |
| `opsgate_admin_revoke_token` | `opsgate.admin_revoke_token_result` | `token` (string) | JSON - **ADMIN ONLY**; revokes any token regardless of owning tenant, no ownership check |

`opsgate_sync_instructions` returns a manifest, not file content, because the combined content (~90KB JSON-encoded as of this writing) has been observed to exceed at least one real MCP client's per-tool-result size cap (~32KB) - it truncated mid-response into invalid JSON rather than erroring cleanly. Every individual file fits comfortably under that limit, so `opsgate_sync_file` fetches one at a time instead.

The four `opsgate_admin_*` tools and `opsgate_quota_usage` are gated inside their own function body by `_require_admin()`/scoped to `_active_tenant_id()` respectively - a token's admin flag (`opsgate_tenants.issue_token(..., admin=True)`) is threaded through `TokenAuthMiddleware` into a `_current_is_admin` contextvar the same way `_current_tenant_id` already was, not a new authentication mechanism. A non-admin token calling an `opsgate_admin_*` tool gets a normal tool-call error (`PermissionError`), the same as any other rejected precondition in this server - never a silent no-op or a different HTTP status.

### `/mcp/claude/` - 25 tools (14 shared with `/mcp/replit/` above, minus its 2 Replit-only sync tools, plus 11 compiler-chain/run-recovery tools exclusive to this mount)

| Tool | Calls | Input | Output |
|---|---|---|---|
| `opsgate_check_capability` / `opsgate_check_paths` / `opsgate_preflight` / `opsgate_show_profile` | (shared - see left) | | |
| `opsgate_intake_request` | `opsgate.intake_request_result` | `text` (plain sentence) | JSON |
| `opsgate_route_request` | `opsgate.route_request` | `request` (object) | JSON |
| `opsgate_init_run` | `opsgate.init_run_result` | `request` (object) | JSON - **writes `runs/<id>/` to disk on this server's machine** |
| `opsgate_list_runs` | `opsgate.list_runs_result` | `limit` (int, optional) | JSON - the caller's own tenant's tracked runs, most recently updated first |
| `opsgate_get_run` | `opsgate.get_run_result` | `run_id` (string) | JSON - the caller's own tenant's persisted request/route/gate_result/handoff for one run |
| `opsgate_compile_prompt` | `opsgate.compile_prompt_text` | `request` (object) | prose text |
| `opsgate_next_phase_prompt` | `opsgate.next_phase_prompt_text` | `run_state` + `parsed_report` (objects) | prose text |
| `opsgate_parse_report` | `opsgate.parse_report_result` | `report_markdown` (text) | JSON |
| `opsgate_lint_report` | `opsgate.lint_report_result` | `report_markdown` (text) | JSON |
| `opsgate_lint_prompt` | `opsgate.lint_prompt_result` | `prompt_markdown` (text) | JSON |
| `opsgate_export_ruleset` | `opsgate_knowledge.export_ruleset` | none | JSON - snapshot of every resource below, for offline/CI use |
| `opsgate_record_decision` / `opsgate_list_own_tokens` / `opsgate_issue_own_token` / `opsgate_revoke_own_token` / `opsgate_list_audit_log` / `opsgate_quota_usage` / `opsgate_admin_create_tenant` / `opsgate_admin_list_tenants` / `opsgate_admin_issue_token` / `opsgate_admin_revoke_token` | (shared - see left) | | |

Every request-shaped tool above (all but `opsgate_export_ruleset`/`opsgate_sync_instructions`/`opsgate_sync_file`) resolves its profile/protected
paths from whichever tenant resolved in Authentication above - a real tenant's own profile, or
`LOCAL_DEV_TENANT_ID`'s default - via that tool's underlying `opsgate.*` function's `tenant_id`
parameter.

Deliberately **not** exposed: `validate-json`, `validate-engine`, `test-all` -
engine-authoring operations run by hand inside this repo, not gate/routing
calls a live Replit task needs.

A deterministic gate tool failing (`can_proceed: false` / `pass: false`) is a
normal, valid result - not a protocol-level error. The caller (the Agent
following `replit.md`) is expected to read that field and report the gate as
blocked, exactly as it would from the CLI's exit code.

## Resources exposed

Read-only governance content, backed by `tools/opsgate_knowledge.py`, which reads its canonical
source files live at call time - never a copied string, so it can't drift from source. Registered
on **both** `/mcp/replit/` and `/mcp/claude/` - unlike the tools above, nothing here is mount-specific.

| Resource | Always-on? | Backed by |
|---|---|---|
| `opsgate://knowledge/hitl-protocol` | yes, unconditionally | `HITL_SPEC.md`, unabridged |
| `opsgate://knowledge/security-rules` | yes, unconditionally | `ai/security.md`'s durable rules |
| `opsgate://knowledge/skill-workflow/{skill}` | no - fetch per matched route's `skill` | one `replit-skills/<skill>/SKILL.md`'s durable workflow |
| `opsgate://knowledge/instruction-object/{name}` | no - fetch per matched route's `references` | one `ai/<name>.md`'s durable rules |

The HITL protocol and security rules are always-on because they apply regardless of which route
a request resolves to; skill workflows and instruction objects are route-conditional, matching
`ROUTING_MANIFEST`'s per-route `skill`/`references` fields - fetch the one(s) the current route
actually names, not all of them unconditionally.

## Verified

- Tested end-to-end against a real request/report round-trip (route → preflight →
  check_paths violation case → compile_prompt → intake_request → record_decision →
  lint_report → parse_report → init_run) via the official `mcp` Python
  SDK's streamable-HTTP client - every tool's output matched what the equivalent
  CLI command (`python3 tools/opsgate.py <command> ...`) produces, and `init_run` /
  `record_decision`'s disk side effects (`runs/<id>/`, `runs/decisions.pylog`) were
  confirmed to land in the right place.
- `tests/test_opsgate_mcp_integration.py` re-runs this against the real running server on
  every change: the legacy shared-secret path, two real tenants' isolation (including a
  revoked token failing closed immediately), every resource/the export tool above, the
  two-mount split itself (each mount lists exactly its own tools, the 5 shared ones appear on
  both, the same tenant token resolves identically regardless of which mount it's used
  against), and the full OAuth round trip (metadata discovery, `/authorize` → `/token` with a
  real PKCE challenge/verifier, the issued `access_token` authenticating a real tool call via
  `Authorization: Bearer`, plus the adversarial cases: wrong client credentials, a mismatched
  PKCE verifier, and replaying an already-redeemed code) - all over genuine MCP protocol calls
  rather than direct Python calls. Requires this directory's `.venv`; run with
  `mcp-server/.venv/bin/python3 tests/test_opsgate_mcp_integration.py`.
- `tests/test_opsgate_oauth.py` unit-tests `opsgate_oauth.py`'s PKCE/credential-matching logic
  directly (no running server needed, but still requires this directory's `.venv` for
  `starlette`): run with `mcp-server/.venv/bin/python3 tests/test_opsgate_oauth.py`.
