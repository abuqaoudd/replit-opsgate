"""Request routing and word-aware signal scoring.

Split out of opsgate.py (relocation, not a rewrite). This is the "which deliverable,
mode, skill, and references does this request route to" engine - a self-contained concern
separate from prompt compilation, reports, or command dispatch.
"""
import re

import opsgate_lexer
import opsgate_tenants
from opsgate_profiles import read_json


def score_signals(text, signals):
    """Word-aware signal scoring - see opsgate_lexer.py. Kept as a thin wrapper so every existing
    call site (and anything importing this function by name) keeps working unchanged; only the
    matching behavior underneath improved (no more substring leakage across word boundaries)."""
    score, _matched = opsgate_lexer.lexical_score(text, signals)
    return score


def parse_skill_frontmatter(text):
    match = re.match(r"^---\n([\s\S]*?)\n---\n", text)
    if not match:
        return None
    fields = {}
    for line in re.split(r"\r?\n", match.group(1)):
        item = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if item:
            fields[item.group(1)] = re.sub(r'^"|"$', "", item.group(2))
    return fields


def unique(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def route_request(request, tenant_id=None):
    routing = read_json("manifests/routing.manifest.json")
    gates = read_json("manifests/capability-gates.json")
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    text = " ".join(
        str(item or "")
        for item in [
            request.get("deliverable"),
            request.get("outcome"),
            request.get("module"),
            *(request.get("acceptance") or []),
            *list((request.get("authorizations") or {}).keys()),
        ]
    )
    risk_text = " ".join([text, *(request.get("must_not_change") or [])])

    def best_route(routes, label_key="mode"):
        best = None
        scored_by_label = []
        for route in routes:
            scored = dict(route)
            scored["score"] = score_signals(text, route.get("signals"))
            scored_by_label.append((route.get(label_key) or route.get("deliverable"), scored["score"]))
            if best is None or scored["score"] > best["score"]:
                best = scored
        _best_score, tied_labels = opsgate_lexer.top_candidates(scored_by_label)
        # Only a genuine tie for the top score across two or more routes counts as ambiguous -
        # one route scoring highest on its own, even by a margin of one, is not ambiguity.
        best_tied_with = [label for label in tied_labels if label != ((best or {}).get(label_key) or (best or {}).get("deliverable"))]
        return best, best_tied_with

    artifact, artifact_tied_with = (
        (next((route for route in routing.get("artifact_routes", []) if route.get("deliverable") == request.get("deliverable")), None), [])
        if any(route.get("deliverable") == request.get("deliverable") for route in routing.get("artifact_routes", []))
        else best_route(routing.get("artifact_routes", []), label_key="deliverable")
    )
    replit, replit_tied_with = best_route(routing.get("replit_routes", [])) if request.get("deliverable") == "replit_prompt" else (None, [])
    phased_by_signal = any(opsgate_lexer.lexical_contains(risk_text, signal) for signal in routing.get("phased_triggers", []))
    execution_shape = "phased" if request.get("deliverable") == "replit_prompt" and ((replit or {}).get("force_phased") or phased_by_signal) else "bounded"

    missing_authority = []
    authorizations = request.get("authorizations") or {}
    if replit and replit.get("capability") and replit["capability"] in gates:
        auth = authorizations.get(replit["capability"]) or {}
        if not auth.get("authorized"):
            missing_authority.extend(gates[replit["capability"]].get("requires", []))
    for capability, auth in authorizations.items():
        if capability != (replit or {}).get("capability") and capability in gates and auth.get("authorized") is False:
            missing_authority.extend(gates[capability].get("requires", []))

    profile_record = opsgate_tenants.get_profile(tenant_id) or {}
    result = {
        "request_id": request.get("id"),
        "profile": tenant_id,
        # frontend_root/backend_root are per-tenant data, not universal facts - resolved here
        # so any caller (a compiled prompt, an MCP tool response, a human) can see this
        # request's actual write roots without hardcoding a specific tenant's paths.
        "profile_roots": {"frontend_root": profile_record.get("frontend_root"), "backend_root": profile_record.get("backend_root")},
        "deliverable": artifact.get("deliverable"),
        "artifact_mode": artifact.get("mode"),
        "template": artifact.get("template"),
        "execution_shape": execution_shape,
        # Word-aware tie detection (opsgate_lexer.top_candidates): true only when two or more
        # artifact-deliverable routes scored exactly equal on their top score - not when one
        # route simply won by a margin. This is the genuine HITL case-2 shape (two materially
        # correct answers, no governing signal between them) surfaced automatically instead of
        # silently taking whichever route happened to be scored first.
        "artifact_mode_ambiguous": bool(artifact_tied_with),
        "artifact_mode_ambiguous_with": artifact_tied_with,
    }
    if replit:
        capability = replit.get("capability") or next(iter(authorizations.keys()), None) or "ordinary_application_change"
        # The active tenant's own business-facts doc is prepended here rather than hardcoded into
        # every route in opsgate_contracts.py, so a tenant with no business_file of its own does
        # not get told to read a different tenant's business rules, and a new tenant only needs
        # to set one field.
        business_file = profile_record.get("business_file")
        full_references = ["replit.md", *([business_file] if business_file else []), *(replit.get("references") or [])]
        result.update(
            {
                "replit_mode": replit.get("mode"),
                "skill": replit.get("skill"),
                "required_references": trim_references(full_references, request, text, business_file),
                "capability": capability,
                "missing_authority": unique(missing_authority),
                "blocked": len(missing_authority) > 0,
                # Same tie detection, applied to skill/mode selection - the routing decision most
                # likely to actually change what gets built. A tie here does not block the task;
                # it is evidence for the Mandatory HITL Gate's "two materially valid choices" row.
                "routing_ambiguous": bool(replit_tied_with),
                "routing_ambiguous_with": replit_tied_with,
            }
        )
    return result


# Reference file -> keywords that justify keeping it when reference_scope=="minimal".
# These are intentionally about the *topic* of the reference doc, not the routing signals -
# a task can be routed to a mode (e.g. by "endpoint") while still not needing every reference
# that mode's route normally bundles (e.g. ai/security.md if nothing security-shaped is in scope).
REFERENCE_TOPIC_KEYWORDS = {
    "ai/backend.md": ["backend", "api", "endpoint", "service", "repository", "server"],
    "ai/frontend.md": ["frontend", "react", "component", "page", "hook", "client"],
    "ai/database.md": ["database", "schema", "migration", "backfill", "mapping", "index", "query"],
    "ai/security.md": ["security", "auth", "permission", "role", "tenant", "sensitive"],
    "ai/testing.md": ["test", "testing", "coverage", "regression"],
    "ai/ui-ux.md": ["ui", "ux", "accessibility", "responsive", "visual"],
    "ai/agents.md": ["agent"],
    "ai/refactoring.md": ["refactor", "consolidate", "decompose", "duplicate"],
}
def trim_references(references, request, scored_text, business_file=None):
    """Return the reference list unchanged unless the request opts into trimming.

    Default behavior (no "reference_scope" field, or reference_scope != "minimal") is
    unchanged from before this function existed, so existing fixtures/requests keep
    producing byte-identical prompts. Only requests that explicitly set
    request["reference_scope"] = "minimal" get a filtered list, based on whether that
    reference's topic keywords actually appear in the request's own text (module,
    outcome, acceptance, authorizations) plus its scope paths.
    """
    # Core routing/gate doc plus the active profile's own business file (if it has one) are
    # always kept regardless of scope trimming - resolved per-call rather than as a fixed module
    # constant, since which business file (if any) applies depends on the active profile.
    always_keep = {"replit.md", *([business_file] if business_file else [])}
    if (request.get("reference_scope") or "full") != "minimal":
        return unique(references)
    path_text = " ".join([*(request.get("scope") or {}).get("write_paths", []), *(request.get("scope") or {}).get("read_paths", [])])
    haystack = f"{scored_text} {path_text}".lower()
    kept = []
    for reference in unique(references):
        if reference in always_keep:
            kept.append(reference)
            continue
        keywords = REFERENCE_TOPIC_KEYWORDS.get(reference)
        if keywords is None or any(keyword in haystack for keyword in keywords):
            kept.append(reference)
    # Never trim down to nothing but the always-keep set for a replit_prompt - if trimming
    # would strip every topic reference, that's a sign the request text is too sparse to
    # trust, so fall back to the full list rather than under-informing the agent.
    if len(kept) <= len(always_keep) and len(references) > len(always_keep):
        return unique(references)
    return kept
