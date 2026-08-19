#!/usr/bin/env python3
"""Unit tests for opsgate_oauth.py's PKCE/credential logic - the parts that don't need a real
running server (see tests/test_opsgate_mcp_integration.py for the full HTTP round trip through
the actual server, including the /authorize -> /token -> Bearer-authenticated-tool-call chain).

Requires the mcp-server/.venv environment (opsgate_oauth.py imports starlette).
Run: mcp-server/.venv/bin/python3 tests/test_opsgate_oauth.py
"""
import base64
import hashlib
import os
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "mcp-server"))

import opsgate_oauth as oauth  # noqa: E402

RESULTS = []


def record(name, passed, detail=""):
    RESULTS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}" + (f" - {detail}" if detail and not passed else ""))


def pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


def main():
    os.environ["OPSGATE_OAUTH_CLIENT_ID"] = "test-client-id"
    os.environ["OPSGATE_OAUTH_CLIENT_SECRET"] = "test-client-secret"
    os.environ["OPSGATE_OAUTH_BACKING_TOKEN"] = "test-backing-token"
    os.environ.pop("OPSGATE_OAUTH_ALLOWED_REDIRECT_URI", None)
    os.environ.pop("OPSGATE_OAUTH_ISSUER_BASE_URL", None)
    os.environ.pop("OPSGATE_MCP_ALLOWED_HOSTS", None)
    os.environ["OPSGATE_MCP_PORT"] = "8765"

    # --- PKCE matching ---
    verifier, challenge = pkce_pair()
    record("a correct code_verifier matches its own code_challenge", oauth._pkce_matches(verifier, challenge))
    record("a wrong code_verifier does not match", not oauth._pkce_matches("wrong-verifier", challenge))
    record("an empty code_verifier never matches", not oauth._pkce_matches("", challenge))
    record("an empty code_challenge never matches", not oauth._pkce_matches(verifier, ""))

    # --- Client credential check ---
    record("correct client_id/secret authenticate", oauth._client_authenticated("test-client-id", "test-client-secret"))
    record("wrong client_secret is rejected", not oauth._client_authenticated("test-client-id", "wrong-secret"))
    record("wrong client_id is rejected", not oauth._client_authenticated("wrong-client-id", "test-client-secret"))
    record("empty client_id/secret are rejected even if OPSGATE_OAUTH_CLIENT_ID were empty", not oauth._client_authenticated("", ""))

    # --- issuer_base_url() derivation order: explicit override > OPSGATE_MCP_ALLOWED_HOSTS > localhost fallback ---
    record("falls back to a local http URL with no config", oauth.issuer_base_url() == "http://127.0.0.1:8765")
    os.environ["OPSGATE_MCP_ALLOWED_HOSTS"] = "example.tail1234.ts.net,other-host"
    record("derives https://<first-allowed-host> when OPSGATE_MCP_ALLOWED_HOSTS is set", oauth.issuer_base_url() == "https://example.tail1234.ts.net")
    os.environ["OPSGATE_OAUTH_ISSUER_BASE_URL"] = "https://explicit-override.example/"
    record("an explicit OPSGATE_OAUTH_ISSUER_BASE_URL always wins, trailing slash stripped", oauth.issuer_base_url() == "https://explicit-override.example")
    os.environ.pop("OPSGATE_OAUTH_ISSUER_BASE_URL", None)
    os.environ.pop("OPSGATE_MCP_ALLOWED_HOSTS", None)

    # --- Authorization-code store: issuance, single-use, expiry ---
    oauth._issued_codes.clear()
    code = "test-code-1"
    oauth._issued_codes[code] = {"code_challenge": challenge, "redirect_uri": "https://claude.example/callback", "expires_at": time.monotonic() + 60}
    record("a freshly issued code is present in the store", code in oauth._issued_codes)
    popped = oauth._issued_codes.pop(code, None)
    record("popping a code removes it (single-use semantics)", popped is not None and code not in oauth._issued_codes)

    expired_code = "test-code-expired"
    oauth._issued_codes[expired_code] = {"code_challenge": challenge, "redirect_uri": "https://claude.example/callback", "expires_at": time.monotonic() - 1}
    oauth._prune_expired_codes()
    record("_prune_expired_codes removes an already-expired code", expired_code not in oauth._issued_codes)

    live_code = "test-code-live"
    oauth._issued_codes[live_code] = {"code_challenge": challenge, "redirect_uri": "https://claude.example/callback", "expires_at": time.monotonic() + 60}
    oauth._prune_expired_codes()
    record("_prune_expired_codes leaves a still-valid code alone", live_code in oauth._issued_codes)
    oauth._issued_codes.pop(live_code, None)

    # --- _extract_client_credentials: both advertised auth methods ---
    class _FakeRequest:
        def __init__(self, headers):
            self.headers = headers

    basic_value = base64.b64encode(b"basic-id:basic-secret").decode("ascii")
    basic_request = _FakeRequest({"authorization": f"Basic {basic_value}"})
    client_id, client_secret = oauth._extract_client_credentials(basic_request, {})
    record("client_secret_basic auth method is parsed correctly", (client_id, client_secret) == ("basic-id", "basic-secret"))

    post_request = _FakeRequest({})
    client_id, client_secret = oauth._extract_client_credentials(post_request, {"client_id": "post-id", "client_secret": "post-secret"})
    record("client_secret_post auth method is parsed correctly", (client_id, client_secret) == ("post-id", "post-secret"))

    malformed_basic_request = _FakeRequest({"authorization": "Basic not-valid-base64!!!"})
    client_id, client_secret = oauth._extract_client_credentials(malformed_basic_request, {})
    record("malformed Basic auth header fails closed (no credentials extracted)", (client_id, client_secret) == (None, None))

    # --- Token response shape ---
    token_response = oauth._token_response()
    record(
        "token response hands back the configured backing token as both access_token and refresh_token",
        token_response == {"access_token": "test-backing-token", "token_type": "Bearer", "refresh_token": "test-backing-token"},
    )

    failed = [name for name, passed, _ in RESULTS if not passed]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed.")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        sys.exit(1)
    print("PASS test-opsgate-oauth: PKCE/credential logic holds.")


if __name__ == "__main__":
    main()
