"""Minimal OAuth 2.1 + PKCE authorization server - just enough to satisfy Claude's "add
custom connector" flow (see modelcontextprotocol.io's Authorization spec), for this single-
operator, single-client deployment. Not a general-purpose OAuth server: there is exactly one
registered client (this deployment's own Claude connector), a static pre-shared client_id/
client_secret handed to Claude by hand via its connector-setup form (which asks for exactly
those two values plus a name/URL - it never registers a client dynamically), and Dynamic Client
Registration (RFC 7591) is explicitly not required by the MCP spec, so it is not implemented
here.

The /token endpoint does not mint a new kind of credential: a successful, PKCE-verified
authorization-code exchange just hands back this deployment's own existing X-Opsgate-Token
value (OPSGATE_OAUTH_BACKING_TOKEN) as the OAuth access_token. opsgate_mcp_server.py's
TokenAuthMiddleware accepts that same value via either header (X-Opsgate-Token or
Authorization: Bearer), so nothing about tenant resolution changes - this is a thin
authorization-flow wrapper in front of the existing token model, not a replacement for it.

OPSGATE_OAUTH_BACKING_TOKEN must be a token dedicated to this one purpose - mint it with
opsgate_tenants.issue_token(tenant_id, label="oauth-backing") rather than reusing a token
already handed to some other consumer (a plugin, a CLI header config, a launchctl-set env var).
A token is a single on/off switch: revoking it revokes every consumer relying on that exact
string, with no warning that anything else was riding along. This was not a hypothetical -
this exact deployment's backing token was originally the same token a since-retired plugin
used directly, discovered only when revoking the plugin's token was about to also cut off the
live OAuth connector (see CHANGELOG.md, 2026-08-19).

OPSGATE_OAUTH_ALLOWED_REDIRECT_URI pins /authorize to one known redirect_uri, closing an
open-redirect surface that would otherwise exist (accepting any caller-supplied redirect_uri on
/authorize, relying only on /token's requirement that it match exactly what /authorize was
originally called with). Left unset, that fallback still holds - a code can only ever be
redeemed with the exact redirect_uri it was issued for - but pin this once the real value is
known, which for Claude's own connector flow is `https://claude.ai/api/mcp/auth_callback`
(confirmed from a real connector setup's request log, not assumed from documentation).
"""
import base64
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

AUTH_CODE_TTL_SECONDS = 300  # generous for a real browser redirect round trip, short enough
# that a leaked/logged code is useless soon after - it is also single-use (popped on redemption).

_issued_codes = {}  # code -> {"code_challenge": str, "redirect_uri": str, "expires_at": float}


def _client_id():
    return os.environ.get("OPSGATE_OAUTH_CLIENT_ID", "")


def _client_secret():
    return os.environ.get("OPSGATE_OAUTH_CLIENT_SECRET", "")


def _backing_token():
    return os.environ.get("OPSGATE_OAUTH_BACKING_TOKEN", "")


def _allowed_redirect_uri():
    """None means accept any redirect_uri on /authorize (see module docstring) - set
    OPSGATE_OAUTH_ALLOWED_REDIRECT_URI once the real value Claude sends is known."""
    return os.environ.get("OPSGATE_OAUTH_ALLOWED_REDIRECT_URI") or None


def issuer_base_url():
    """The externally-reachable origin this server is advertised under - not derived from the
    incoming request, since this process sits behind a tunnel that terminates TLS upstream (a
    request here would otherwise report scheme "http" and host "127.0.0.1:<port>", which is
    right for this process but wrong for anything Claude's client needs to reach). Falls back to
    the first OPSGATE_MCP_ALLOWED_HOSTS entry - already the real tunnel hostname whenever one is
    configured - rather than hardcoding any single deployment's hostname into this module."""
    override = os.environ.get("OPSGATE_OAUTH_ISSUER_BASE_URL")
    if override:
        return override.rstrip("/")
    allowed_hosts = [h.strip() for h in os.environ.get("OPSGATE_MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
    if allowed_hosts:
        return f"https://{allowed_hosts[0]}"
    return f"http://127.0.0.1:{os.environ.get('OPSGATE_MCP_PORT', '8765')}"


def _prune_expired_codes():
    now = time.monotonic()
    for code in [c for c, entry in _issued_codes.items() if entry["expires_at"] < now]:
        _issued_codes.pop(code, None)


def _pkce_matches(code_verifier, code_challenge):
    if not code_verifier or not code_challenge:
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(computed, code_challenge)


def _extract_client_credentials(request, form):
    """Supports both token_endpoint_auth_methods this server advertises: client_secret_post
    (client_id/client_secret in the form body) and client_secret_basic (HTTP Basic auth)."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        except Exception:
            return None, None
        client_id, _, client_secret = decoded.partition(":")
        return client_id, client_secret
    return form.get("client_id"), form.get("client_secret")


def _client_authenticated(client_id, client_secret):
    return bool(_client_id()) and hmac.compare_digest(client_id or "", _client_id()) and hmac.compare_digest(client_secret or "", _client_secret())


async def oauth_authorization_server_metadata(request: Request):
    base = issuer_base_url()
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
    })


async def oauth_protected_resource_metadata(request: Request):
    base = issuer_base_url()
    return JSONResponse({
        "resource": base,
        "authorization_servers": [base],
    })


async def oauth_authorize(request: Request):
    params = request.query_params
    response_type = params.get("response_type")
    client_id = params.get("client_id")
    redirect_uri = params.get("redirect_uri")
    state = params.get("state", "")
    code_challenge = params.get("code_challenge")
    code_challenge_method = params.get("code_challenge_method")

    if response_type != "code":
        return JSONResponse({"error": "unsupported_response_type"}, status_code=400)
    if not _client_id() or not hmac.compare_digest(client_id or "", _client_id()):
        return JSONResponse({"error": "unauthorized_client"}, status_code=401)
    if not redirect_uri:
        return JSONResponse({"error": "invalid_request", "error_description": "redirect_uri is required"}, status_code=400)
    allowed_redirect_uri = _allowed_redirect_uri()
    if allowed_redirect_uri and redirect_uri != allowed_redirect_uri:
        return JSONResponse({"error": "invalid_request", "error_description": "redirect_uri not recognized"}, status_code=400)
    if code_challenge_method != "S256" or not code_challenge:
        return JSONResponse({"error": "invalid_request", "error_description": "PKCE (S256) is required"}, status_code=400)

    # No login/consent screen is rendered - there is exactly one legitimate holder of this
    # deployment's client_secret (this deployment's own operator), so a request that already
    # authenticated as that client is auto-approved. The MCP Authorization spec requires the
    # authorization-code + PKCE *flow*, not an interactive consent UI.
    _prune_expired_codes()
    code = os.urandom(32).hex()
    _issued_codes[code] = {
        "code_challenge": code_challenge,
        "redirect_uri": redirect_uri,
        "expires_at": time.monotonic() + AUTH_CODE_TTL_SECONDS,
    }
    query = {"code": code}
    if state:
        query["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(query)}", status_code=302)


def _token_response():
    token = _backing_token()
    return {"access_token": token, "token_type": "Bearer", "refresh_token": token}


async def oauth_token(request: Request):
    form = await request.form()
    grant_type = form.get("grant_type")
    client_id, client_secret = _extract_client_credentials(request, form)
    if not _client_authenticated(client_id, client_secret):
        return JSONResponse({"error": "invalid_client"}, status_code=401)

    if grant_type == "authorization_code":
        code = form.get("code")
        redirect_uri = form.get("redirect_uri")
        code_verifier = form.get("code_verifier")
        _prune_expired_codes()
        entry = _issued_codes.pop(code, None) if code else None
        if entry is None:
            return JSONResponse({"error": "invalid_grant", "error_description": "unknown or expired code"}, status_code=400)
        if not hmac.compare_digest(entry["redirect_uri"], redirect_uri or ""):
            return JSONResponse({"error": "invalid_grant", "error_description": "redirect_uri mismatch"}, status_code=400)
        if not _pkce_matches(code_verifier or "", entry["code_challenge"]):
            return JSONResponse({"error": "invalid_grant", "error_description": "code_verifier does not match code_challenge"}, status_code=400)
        return JSONResponse(_token_response())

    if grant_type == "refresh_token":
        refresh_token = form.get("refresh_token")
        if not _backing_token() or not hmac.compare_digest(refresh_token or "", _backing_token()):
            return JSONResponse({"error": "invalid_grant"}, status_code=400)
        return JSONResponse(_token_response())

    return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)


PUBLIC_PATHS = {
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/authorize",
    "/token",
}
