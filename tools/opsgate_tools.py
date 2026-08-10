#!/usr/bin/env python3
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import copy
from pathlib import Path

import opsgate_contracts
import opsgate_fixtures
import opsgate_lexer


ROOT_DIR = Path(__file__).resolve().parent.parent


def read_json(relative_path):
    if relative_path in opsgate_contracts.CONTRACTS:
        return copy.deepcopy(opsgate_contracts.CONTRACTS[relative_path])
    with (ROOT_DIR / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_python_data(path, variable_name, value, header):
    import pprint

    body = f"{header}\n\n{variable_name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n"
    write_text(path, body)


def read_text(relative_path):
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def write_text(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def exists(relative_path):
    return (ROOT_DIR / relative_path).exists()


def copy_recursive(source, target):
    source = Path(source)
    target = Path(target)
    if source.is_dir():
        target.mkdir(parents=True, exist_ok=True)
        for entry in source.iterdir():
            copy_recursive(entry, target / entry.name)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def list_files(directory, predicate=lambda path: True):
    directory = Path(directory)
    if not directory.exists():
        return []
    files = [path for path in directory.rglob("*") if path.is_file() and predicate(path)]
    return sorted(files, key=lambda item: str(item))


def sha256(file_path):
    return hashlib.sha256(Path(file_path).read_bytes()).hexdigest()


def same_bytes(a, b):
    a = Path(a)
    b = Path(b)
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


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


def route_request(request):
    routing = read_json("manifests/routing.manifest.json")
    gates = read_json("manifests/capability-gates.json")
    profile = active_profile(request)
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

    profile_record = read_json("manifests/profiles.json").get("profiles", {}).get(profile, {})
    result = {
        "request_id": request.get("id"),
        "profile": profile,
        # frontend_root/backend_root are per-profile data, not universal facts - resolved here
        # so any caller (a compiled prompt, an MCP tool response, a human) can see this
        # request's actual write roots without hardcoding a specific project's paths.
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
        # The active profile's own business-facts doc (e.g. ai/metco.md for the metco profile) is
        # prepended here rather than hardcoded into every route in opsgate_contracts.py, so a new
        # profile with no business_file of its own (generic-replit) does not get told to read a
        # different project's business rules, and a future profile only needs to set one field.
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


def print_json(value):
    print(json.dumps(value, indent=2))


def fixture_data(path):
    normalized = str(path)
    for fixture in [*opsgate_fixtures.ROUTING_FIXTURES, *opsgate_fixtures.HITL_FIXTURES]:
        fixture_id = Path(fixture["path"]).stem
        group = Path(fixture["path"]).parent.name
        if normalized in [f"{group}:{fixture_id}", fixture_id] or normalized == fixture["path"] or normalized.endswith(fixture["path"]):
            return copy.deepcopy(fixture["data"])
    if normalized in ["state:ready-phased-state", "ready-phased-state"] or normalized.endswith("fixtures/state/ready-phased-state.json"):
        return copy.deepcopy(opsgate_fixtures.READY_PHASED_STATE)
    if normalized in ["reports:parsed-sample-report", "parsed-sample-report"] or normalized.endswith("fixtures/reports/parsed-sample-report.json"):
        return copy.deepcopy(opsgate_fixtures.PARSED_SAMPLE_REPORT)
    if normalized in ["gold:bounded-frontend-request", "bounded-frontend-request"] or normalized.endswith("canonical/examples/gold-standard/bounded-frontend-request.json"):
        return copy.deepcopy(opsgate_fixtures.GOLD_STANDARD_BOUNDED_FRONTEND_REQUEST)
    if normalized in ["gold:phased-migration-request", "phased-migration-request"] or normalized.endswith("canonical/examples/gold-standard/phased-migration-request.json"):
        return copy.deepcopy(opsgate_fixtures.GOLD_STANDARD_PHASED_MIGRATION_REQUEST)
    return None


def load_data(path):
    fixture = fixture_data(path)
    if fixture is not None:
        return fixture
    return json.loads(Path(path).resolve().read_text(encoding="utf-8"))


def load_request(path):
    data = load_data(path)
    return data.get("request") or data


def usage(message):
    print(message, file=sys.stderr)
    raise SystemExit(2)


def cmd_route_request(argv):
    if not argv:
        usage("Usage: python3 tools/route-request.py <request.json>")
    print_json(route_request(load_request(argv[0])))


def cmd_check_capabilities(argv):
    if not argv:
        usage("Usage: python3 tools/check-capabilities.py <request.json>")
    request = load_request(argv[0])
    route = route_request(request)
    gates = read_json("manifests/capability-gates.json")
    missing = []
    capabilities = set((request.get("authorizations") or {}).keys())
    if route.get("capability"):
        capabilities.add(route["capability"])
    for capability in capabilities:
        if capability not in gates:
            continue
        auth = (request.get("authorizations") or {}).get(capability) or {}
        if auth.get("authorized") is not True and gates[capability].get("default") == "blocked":
            missing.append({"capability": capability, "required": gates[capability].get("requires", [])})
    result = {"can_proceed": len(missing) == 0, "route_capability": route.get("capability"), "missing": missing}
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def active_profile(request=None):
    """Resolve which manifests/profiles.json entry governs this run, so the kit behaves
    correctly both in the project it was built for and in any new Replit project a submodule
    of it gets dropped into. Order: OPSGATE_PROFILE env var (set this when running against a
    different project) > legacy METCO_PROFILE env var (kept only so a deployment configured
    before the 6.0.13-generalization rename keeps working without touching its Repl Secret) >
    an explicit "profile" field on the request itself > the manifest's own default_profile.
    Falls back to "generic-replit" - never raises - if none of those resolve to a profile that
    actually exists, so a new project gets sane generic protections instead of a crash or a
    silent inheritance of another project's paths."""
    profiles = read_json("manifests/profiles.json")
    known = profiles.get("profiles", {})
    for candidate in [
        os.environ.get("OPSGATE_PROFILE"),
        os.environ.get("METCO_PROFILE"),  # legacy env var name, see docstring
        (request or {}).get("profile"),
        profiles.get("default_profile"),
    ]:
        if candidate and candidate in known:
            return candidate
    return "generic-replit" if "generic-replit" in known else profiles.get("default_profile")


def protected_paths_for(request=None):
    profile = active_profile(request)
    profiles_data = read_json("manifests/protected-paths.json")["profiles"]
    return profiles_data.get(profile) or profiles_data.get("generic-replit") or next(iter(profiles_data.values()), {})


def normalize_pattern(pattern):
    return re.sub(r"\*\*/?", "", str(pattern)).replace("*", "")


def matches_protected(candidate, protected_pattern):
    needle = normalize_pattern(protected_pattern).rstrip("/")
    return candidate == needle or candidate.startswith(f"{needle}/") or f"/{needle}/" in candidate or needle in candidate


def cmd_show_profile(argv):
    """Print the resolved active profile in full - name, roots, and protected paths - with no
    request file required. Exists so a human or an agent can answer "what project am I actually
    configured for right now" in one command instead of reading OPSGATE_PROFILE, profiles.json,
    and protected-paths.json by hand. Accepts an optional request.json argument only to honor an
    explicit "profile" field on it; every other request field is ignored."""
    request = load_request(argv[0]) if argv else {}
    profile = active_profile(request)
    profiles = read_json("manifests/profiles.json").get("profiles", {})
    print_json(
        {
            "resolved_profile": profile,
            "resolved_from": (
                "OPSGATE_PROFILE env var"
                if os.environ.get("OPSGATE_PROFILE") in profiles
                else "METCO_PROFILE env var (legacy name)"
                if os.environ.get("METCO_PROFILE") in profiles
                else "request.profile field"
                if request.get("profile") in profiles
                else "manifests/profiles.json default_profile"
            ),
            "profile_record": profiles.get(profile, {}),
            "protected_paths": protected_paths_for(request),
        }
    )


def cmd_check_paths(argv):
    if not argv:
        usage("Usage: python3 tools/check-paths.py <request.json>")
    request = load_request(argv[0])
    protected_paths = protected_paths_for(request)
    scope = request.get("scope") or {}
    all_paths = [*(scope.get("write_paths") or []), *(scope.get("read_paths") or [])]
    violations = []
    for candidate in all_paths:
        for protected_pattern in protected_paths.get("never_access", []):
            if matches_protected(candidate, protected_pattern):
                violations.append({"path": candidate, "protected_pattern": protected_pattern})
    result = {"can_proceed": len(violations) == 0, "checked_paths": all_paths, "violations": violations}
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def cmd_preflight(argv):
    if not argv:
        usage("Usage: python3 tools/preflight.py <request.json>")
    request = load_request(argv[0])
    route = route_request(request)
    gates = read_json("manifests/gates.json")
    failed_gates = []
    evidence = []
    scope = request.get("scope") or {}
    write_paths = scope.get("write_paths") or []
    read_paths = scope.get("read_paths") or []
    if request.get("deliverable") == "replit_prompt" and not write_paths:
        failed_gates.append("scope_gate: missing_write_scope")
    if request.get("deliverable") == "replit_prompt" and not read_paths:
        evidence.append("read_scope_default: direct owners, callers, and tests")
    if route.get("blocked"):
        failed_gates.append("capability_gate: missing_authority")
    protected_patterns = protected_paths_for(request).get("never_access", [])
    for candidate in [*write_paths, *read_paths]:
        for pattern in protected_patterns:
            token = normalize_pattern(pattern).rstrip("/")
            if token and (token in candidate or candidate.startswith(token)):
                failed_gates.append(f"protected_path_gate: {candidate}")
    # Every gate this function checks - scope, capability, protected-path - is deterministic:
    # a fixed rule evaluated against the request, with one correct answer and no judgment
    # involved. None of them is a HITL case. A failure here means "explicit authorization or
    # scope is missing," not "a human must choose between options." Treat every gate the same
    # way: name it, say what it needs, and stop - do not route any of them through the HITL
    # decision-required ceremony, which is reserved for the three genuine ambiguity cases
    # (unknown next step, tied valid options, self-made scope-expanding decision) that can only
    # be discovered during actual work, not from a request file before anything has been touched.
    result = {
        "request_id": request.get("id"),
        "route": route,
        "gates_version": gates.get("version"),
        "can_proceed": len(failed_gates) == 0,
        "failed_gates": unique(failed_gates),
        "blocked": len(failed_gates) > 0,
        "blocked_gate_kind": "deterministic" if failed_gates else None,
        "evidence": evidence,
    }
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def as_list(items, fallback="None specified"):
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


HITL_DECISION_BLOCK = """If blocked, return only:

# HITL decision required

ID: HITL-task-Pphase-Qnumber
Blocked check: name the failed gate row
Question: ask the smallest required decision
Evidence checked: list the evidence already inspected
Options:
A. option label - exact scope effect
B. option label - exact scope effect
Exact resume point: phase/step to resume after a valid DECIDE reply
Required reply: DECIDE HITL-id: answer and exact scope"""

DETERMINISTIC_BLOCK_DECISION = """If a Deterministic row fails, do not use the HITL decision format above - there is nothing to decide between, only something to grant. Return only:

# Gate blocked

Blocked gate: name the exact failed gate (scope_gate / capability_gate / protected_path_gate / verification_gate)
Missing: the exact authorization, evidence, or scope change needed to pass
Effect: task remains paused until that authorization is explicitly granted - this is not a HITL question and does not use the DECIDE reply format"""


def mandatory_hitl_gate(request=None):
    mcp = (request or {}).get("mcp") or {}
    if not mcp.get("enabled"):
        return f"""## Mandatory HITL Gate (per phase and final report)

Also run the lighter Per-Action Gate from replit.md before every individual step in the Execution section below - it checks the same three cases at finer grain and does not replace this table at the checkpoints where the table is required.

Every row below gets checked the same way, but two different kinds of failure resolve differently. A Deterministic row has one correct answer and no judgment involved - failing it means an authorization or scope grant is missing, not that a decision needs making. A Judgment row is one of the three real HITL cases (unknown next step, two tied valid options, or a self-made choice that would expand scope) - only these use the HITL decision format.

Before editing, before each phase, and before final report, answer this gate explicitly:

| Check | Kind | Answer | Evidence |
|---|---|---|---|
| Is the exact owner/path known? | Judgment | YES/NO | |
| Is the write scope explicitly authorized? | Deterministic | YES/NO | |
| Are protected paths excluded? | Deterministic | YES/NO | |
| Are package/config/schema/seed/destructive changes needed? | Deterministic | YES/NO | |
| If risky changes are needed, are they explicitly authorized? | Deterministic | YES/NO/NA | |
| Are there two materially valid implementation choices? | Judgment | YES/NO | |
| Would proceeding require inventing a business rule, permission rule, data rule, or API contract? | Judgment | YES/NO | |
| Is verification possible in a safe environment? | Deterministic | YES/NO | |

Stop immediately on any failing row. If every failing row is Deterministic, name each one and the exact grant it needs using the block below - do not invent options or a DECIDE-style question for a row with nothing to choose between. If any failing row is Judgment, use the HITL decision format instead; it takes priority when both kinds fail together.

{DETERMINISTIC_BLOCK_DECISION}

{HITL_DECISION_BLOCK}"""

    prefix = mcp.get("tool_prefix", "opsgate_")
    return f"""## Mandatory HITL Gate (per phase and final report) - MCP mode

MCP tools are registered for this project. Before editing, before each phase, and before final report, call these tools directly instead of re-deriving the gate table by hand each time. Treat every gate the same way - name it, state what's missing, stop - and reserve the HITL decision format for genuine judgment ambiguity only, never for a named gate that just needs authorization:

1. Call `{prefix}check_capability` with this request's authorizations. `can_proceed: false` is a Deterministic `capability_gate` failure - report the missing capability/evidence as blocked and stop using the Gate Blocked format below. This is not a HITL decision; there is nothing to choose between.
2. Call `{prefix}check_paths` with this request's scope. A reported protected-path violation is a Deterministic `protected_path_gate` failure - name the exact path, stop, use the same Gate Blocked format. Do not touch those paths.
3. Call `{prefix}preflight` with the full request before the first edit, before each phase, and again immediately before the final report. Every gate it can name in `failed_gates` is Deterministic by construction - `preflight` only inspects the request file, so it cannot detect real ambiguity. If `can_proceed` is false, name each failed gate from the response using the Gate Blocked format, not the HITL format.
4. Reserve the HITL decision format for ambiguity none of the tools above can see: an owner/path that stays unknown after bounded inspection, two implementation choices with no governing rule between them, or a step that would require inventing a business/data/security/API rule. These only surface during the work itself, never from the request file alone.
5. If a human answers a HITL question, call `{prefix}record_decision` with the HITL id and the answer before resuming, so the decision is persisted outside this conversation.

{DETERMINISTIC_BLOCK_DECISION}

{HITL_DECISION_BLOCK}

Only fall back to the manual eight-row reasoning table if a tool call errors or the MCP connection is unreachable - state that explicitly in the Final Report if it happens, since it means the gate ran on inference instead of a computed result."""


def per_action_gate_line(request=None):
    mcp = (request or {}).get("mcp") or {}
    if not mcp.get("enabled"):
        return "Before each step below, run the Per-Action Gate from replit.md and state its result (`Gate: OK` or `Gate: BLOCKED`) before acting on that step. A `BLOCKED` result stops the entire task immediately; do not continue to the next step or defer it to the final report."
    prefix = mcp.get("tool_prefix", "opsgate_")
    return f"Before each step below, call `{prefix}check_paths` (and `{prefix}preflight` for any step touching a risky/package/config surface) and state its result (`Gate: OK` or `Gate: BLOCKED`) before acting on that step. A `BLOCKED` result stops the entire task immediately; do not continue to the next step or defer it to the final report."


def discovery_steps(request=None):
    known = (request or {}).get("known_context") or {}
    owners, callers, tests = known.get("owners"), known.get("callers"), known.get("tests")
    if not (owners or callers or tests):
        return """1. Capture scoped status and diff for approved paths.
2. Inspect named owners, direct callers/imports, contracts, and related tests.
3. Stop discovery once ownership, direct consumers, pre-existing changes, and relevant checks are known.
4. Complete reuse/creation decisions before adding any new unit.
5. Implement only within approved scope and preserve protected paths.
6. Run the smallest risk-based checks available in the project."""
    known_lines = []
    if owners:
        known_lines.append(f"Owner(s): {', '.join(owners)}")
    if callers:
        known_lines.append(f"Direct caller(s)/import site(s): {', '.join(callers)}")
    if tests:
        known_lines.append(f"Relevant test(s): {', '.join(tests)}")
    known_block = "; ".join(known_lines)
    return f"""1. Capture scoped status and diff for approved paths.
2. Owner, callers, and tests are already known from the request - {known_block}. Do a quick targeted check that this is still current (git status/diff on those exact paths) instead of open-ended discovery; only widen the search if one of these is stale or missing.
3. Complete reuse/creation decisions before adding any new unit.
4. Implement only within approved scope and preserve protected paths.
5. Run the smallest risk-based checks available in the project."""


def context_block(request):
    return f"""## Context

- Module: {request.get("module") or "Not specified"}
- Outcome: {request.get("outcome")}
- Write paths: {", ".join((request.get("scope") or {}).get("write_paths") or []) or "None specified"}
- Read paths: {", ".join((request.get("scope") or {}).get("read_paths") or []) or "None specified"}

## Acceptance Evidence

{as_list(request.get("acceptance"))}

## Must Remain Unchanged

{as_list(request.get("must_not_change"))}"""


def compile_replit_prompt(request, route):
    phase_line = (
        "Use phased execution. Produce a phase plan and execute only the earliest authorized incomplete phase."
        if route.get("execution_shape") == "phased"
        else "Use one bounded implementation batch."
    )
    blocked = ""
    if route.get("blocked"):
        blocked = f"\n## Blocked Capability Gate\n\nDo not implement yet. Missing required authority/evidence:\n\n{as_list(route.get('missing_authority'))}\n"
    scope = request.get("scope") or {}
    return f"""# {request.get("module") or "Replit Task"}

Deliver: **{request.get("outcome")}**

Automatically route this task through the installed instructions. Selected routing evidence:

| Field | Value |
|---|---|
| Execution shape | {route.get("execution_shape")} |
| Internal mode | {route.get("replit_mode")} |
| Skill | {route.get("skill")} |
| Capability gate | {route.get("capability")} |

## Load First

Read these files before acting:

{as_list(route.get("required_references"))}

## Instruction Objects

Record the loaded instruction object set before editing:

| Object | Why loaded | Inputs used | Authority boundary |
|---|---|---|---|
| TaskControlInstruction | every task | outcome, acceptance, scope, selected mode/skill | does not override replit.md |
| DomainInstructionObject | selected from routed references and current scope | owner, contract, consumers, risks | no unauthorized surfaces |
| VerificationInstructionObject | required evidence and result labeling | acceptance, changed paths, risks | no broader tests or writes by itself |

Use each object's Responsibility, Inputs, Must Not, Workflow, and Output Evidence sections as the operating contract. A loaded object guides behavior only inside approved scope.

## Scope

| Access | Paths |
|---|---|
| Write | {", ".join(scope.get("write_paths") or []) or "No write paths authorized"} |
| Minimum read-only | {", ".join(scope.get("read_paths") or []) or "Only direct owners, callers, and tests needed for the task"} |
| Never access | {", ".join(protected_paths_for(request).get("never_access", [])) or "No never_access paths configured for the active profile"}, resolved aliases, protected generated or production systems |

Must remain unchanged:

{as_list(request.get("must_not_change"))}

{blocked}
{mandatory_hitl_gate(request)}

## Execution

{phase_line}

{per_action_gate_line(request)}

{discovery_steps(request)}

## Acceptance Criteria

{as_list(request.get("acceptance"), "- Observable outcome is delivered without changing locked behavior.")}

## Final Report

Include:

1. Outcome and acceptance status.
2. HITL Gate Result table.
3. Confirmation that the Per-Action Gate ran before every step above, not only reconstructed afterward; name any step where it was skipped.
4. Selected instruction objects, object inputs used, and authority boundaries honored.
5. Files changed and purpose.
6. Ownership/reuse decisions.
7. Checks as PASSED/FAILED/NOT RUN.
8. Protected Path Compliance.
9. Residual Risk.
10. Blockers or manual next steps."""


def compile_artifact_prompt(request, route):
    title = f"# {route.get('deliverable', '').replace('_', ' ')}"
    routing = f"""Routing:

| Field | Value |
|---|---|
| Deliverable | {route.get("deliverable")} |
| Internal mode | {route.get("artifact_mode")} |
| Template | {route.get("template")} |"""
    common_close = "Keep facts, assumptions, decisions, recommendations, and open questions separate. Use stable IDs where the template requires them. Return only the polished artifact unless commentary is explicitly requested."
    deliverable = route.get("deliverable")
    if deliverable == "audit":
        body = f"""Perform a read-only audit for: **{request.get("outcome")}**

{routing}

{context_block(request)}

## Required Output

1. Objective, baseline, scope, exclusions, method, and evidence inventory.
2. Requirement coverage table with PASSED, FAILED, or NOT RUN.
3. Findings ordered by severity and confidence.
4. Positive controls and compliant behavior worth preserving.
5. Coverage gaps and unverified claims.
6. Prioritized remediation backlog with acceptance evidence and recovery note.
7. Open decisions, residual risk, and recommended next artifact or Replit process.

Do not change files, broaden scope, or infer an unobserved pass. {common_close}"""
    elif deliverable == "task_backlog":
        body = f"""Create a dependency-aware task backlog for: **{request.get("outcome")}**

{routing}

{context_block(request)}

## Required Output

1. Ordered tasks with stable TASK IDs.
2. Source traceability to business, spec, audit, and change IDs.
3. Observable outcome, scope, dependencies, acceptance, verification, recovery, and handoff for each task.
4. Bounded versus phased execution shape with rationale.
5. Blockers and HITL-eligible decisions tied to the exact blocked task.
6. Dependency summary, phase groupings, and recommended next task or phase.

Do not hide missing decisions inside implementation tasks. {common_close}"""
    elif deliverable == "change_record":
        body = f"""Create a controlled change record for: **{request.get("outcome")}**

{routing}

{context_block(request)}

## Required Output

1. Change summary, business value, urgency, decision owner, and affected baselines.
2. Current versus target behavior.
3. In-scope, out-of-scope, and must-remain-unchanged boundaries.
4. Requirement additions, modifications, deprecations, removals, and unaffected IDs.
5. Impact analysis for business, UX, API, data, security, operations, tests, and documentation.
6. Options considered, recommendation, rollout, rollback, monitoring, risks, and approvals.
7. Recommended bounded or phased delivery shape.

Do not silently rewrite the original baseline. {common_close}"""
    elif deliverable == "specification":
        body = f"""Create or update an implementation-ready specification for: **{request.get("outcome")}**

{routing}

{context_block(request)}

## Required Output

1. Document control and governing business/change IDs.
2. System context, scope, exclusions, glossary, assumptions, and explicit decisions.
3. Requirement traceability to REQ, NFR, SEC, DATA, and UX IDs.
4. Actors, permissions, tenant/object scope, and authorization matrix.
5. Functional flows, state transitions, edge cases, and failure behavior.
6. Interface/API/form/event contracts, validation, errors, idempotency, compatibility, and versioning.
7. Data ownership, lifecycle, migration/backfill implications, and auditability.
8. UI, accessibility, performance, security, reliability, observability, rollout, and rollback expectations.
9. Verification matrix and unresolved decisions eligible for HITL.

{common_close}"""
    else:
        body = f"""Create or update a business file for: **{request.get("outcome")}**

{routing}

{context_block(request)}

## Required Output

1. Document control and source authority.
2. Executive summary, business outcome, and decision requested.
3. Current problem, affected users, frequency, severity, and cost/risk of inaction.
4. In-scope capabilities, out-of-scope boundaries, and unchanged behavior.
5. Stakeholders, responsibilities, decision owners, and approval owners.
6. Atomic business capabilities, requirements, and business rules with stable IDs.
7. Current-state and target-state journeys, including exceptions and recovery.
8. Success measures and acceptance outcomes.
9. Decisions, assumptions, risks, open questions, and traceability.

{common_close}"""
    return f"{title}\n\n{body}"


def cmd_compile_prompt(argv):
    if not argv:
        usage("Usage: python3 tools/compile-prompt.py <request.json>")
    request = load_request(argv[0])
    route = route_request(request)
    prompt = compile_replit_prompt(request, route) if route.get("deliverable") == "replit_prompt" else compile_artifact_prompt(request, route)
    print(prompt.strip())


def cmd_init_state(argv):
    if not argv:
        usage("Usage: python3 tools/init-state.py <request.json>")
    request = load_request(argv[0])
    route = route_request(request)
    state = {
        "request_id": request.get("id"),
        "status": "blocked" if route.get("blocked") else "ready",
        "deliverable": route.get("deliverable"),
        "artifact_mode": route.get("artifact_mode"),
        "replit_mode": route.get("replit_mode"),
        "skill": route.get("skill"),
        "execution_shape": route.get("execution_shape"),
        "capability": route.get("capability"),
        "missing_authority": route.get("missing_authority") or [],
        "scope": request.get("scope") or {},
        "decisions": [],
        "checks": [],
        "phases": [],
    }
    if route.get("execution_shape") == "phased":
        state["phases"] = [
            {
                "id": "PHASE-0",
                "status": "blocked" if route.get("blocked") else "planned",
                "outcome": "Discovery, prerequisite proof, and phase authorization check",
                "write_paths": [],
                "verification_gate": ["Prerequisites and capability gates are evidenced"],
                "rollback_boundary": "No write operations",
            },
            {
                "id": "PHASE-1",
                "status": "planned",
                "outcome": request.get("outcome"),
                "write_paths": (request.get("scope") or {}).get("write_paths") or [],
                "verification_gate": request.get("acceptance") or [],
                "rollback_boundary": "Current phase changed files only",
            },
        ]
    print_json(state)


def cmd_parse_report(argv):
    if not argv:
        usage("Usage: python3 tools/parse-report.py <report.md>")
    text = Path(argv[0]).resolve().read_text(encoding="utf-8")
    lines = re.split(r"\r?\n", text)

    def collect_section(patterns):
        start = next((i for i, line in enumerate(lines) if any(re.search(pattern, line, re.I) for pattern in patterns)), -1)
        if start < 0:
            return []
        out = []
        for line in lines[start + 1:]:
            if re.match(r"^#{1,6}\s+", line):
                break
            if line.strip():
                out.append(line.strip())
        return out

    checks = []
    for line in lines:
        match = re.search(r"\b(PASSED|FAILED|NOT RUN)\b[:\s-]*(.*)$", line, re.I)
        if match:
            checks.append({"status": match.group(1).upper(), "text": match.group(2).strip() or line.strip()})
    files = []
    for line in lines:
        match = re.search(r"(?:changed|file|path)[:\s-]+(`?[^`\s][^`]*`?)", line, re.I)
        if match and re.search(r"[./]", match.group(1)):
            files.append(match.group(1).replace("`", "").strip())
    hitl = [line.strip() for line in lines if re.search(r"HITL-[A-Za-z0-9-]+", line)]
    risk = collect_section([r"^#+\s*residual risk", r"^#+\s*remaining risk"])
    parsed = {
        "outcome": (collect_section([r"^#+\s*outcome", r"^#+\s*summary"]) or ["Not detected"])[0],
        "acceptance_status": (collect_section([r"^#+\s*acceptance"]) or ["Not detected"])[0],
        "files_changed": unique(files),
        "checks": checks,
        "hitl_decisions": hitl,
        "blockers": collect_section([r"^#+\s*blockers?", r"^#+\s*limitations?"]),
        "residual_risk": risk or ["Not detected"],
    }
    print_json(parsed)


def extract_section(source, heading):
    pattern = re.compile(rf"(^|\n)#+\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n#+\s+|$)", re.I)
    match = pattern.search(source)
    return match.group(2).strip() if match else ""


def parse_markdown_table(section):
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|") and not re.match(r"^\|\s*-+", line):
            rows.append([cell.strip() for cell in line[1:-1].split("|")])
    return rows


def is_placeholder(value):
    return (not value) or value == "-" or value == "NA" or re.search(r"\[[^\]]+\]", value) or re.search(r"evidence\s*(here|checked|needed|tbd|todo)?", value, re.I)


REQUIRED_GATE_ROWS = [
    "Is the exact owner/path known?",
    "Is the write scope explicitly authorized?",
    "Are protected paths excluded?",
    "Are package/config/schema/seed/destructive changes needed?",
    "If risky changes are needed, are they explicitly authorized?",
    "Are there two materially valid implementation choices?",
    "Would proceeding require inventing a business rule, permission rule, data rule, or API contract?",
    "Is verification possible in a safe environment?",
]


def cmd_lint_report(argv):
    if not argv:
        usage("Usage: python3 tools/lint-report.py <report.md>")
    text = Path(argv[0]).resolve().read_text(encoding="utf-8")
    required = ["HITL Gate Result", "Files Changed", "Checks", "Protected Path Compliance", "Residual Risk"]
    missing = [item for item in required if item not in text]
    has_check_label = re.search(r"\b(PASSED|FAILED|NOT RUN)\b", text) is not None
    rows = parse_markdown_table(extract_section(text, "HITL Gate Result"))
    header = rows[0] if rows else []
    data_rows = rows[1:]
    has_gate_header = any(re.match(r"^(check|gate)$", cell, re.I) for cell in header) and any(re.match(r"^(answer|result)$", cell, re.I) for cell in header) and any(re.match(r"^evidence$", cell, re.I) for cell in header)
    normalized = {}
    for row in data_rows:
        if len(row) >= 3:
            normalized[row[0]] = {"answer": (row[1] or "").upper(), "evidence": " | ".join(row[2:]).strip()}
    missing_gate_rows = [row for row in REQUIRED_GATE_ROWS if row not in normalized]
    invalid_answers = [row for row, value in normalized.items() if value["answer"] not in ["YES", "NO", "NA", "N/A"]]
    weak_evidence = [row for row, value in normalized.items() if is_placeholder(value["evidence"])]
    blockers = []

    def answer_for(row):
        return (normalized.get(row) or {}).get("answer")

    for row in [
        "Is the exact owner/path known?",
        "Is the write scope explicitly authorized?",
        "Are protected paths excluded?",
        "Is verification possible in a safe environment?",
    ]:
        if answer_for(row) == "NO":
            blockers.append(f"{row}: NO")
    if answer_for("Are package/config/schema/seed/destructive changes needed?") == "YES" and answer_for("If risky changes are needed, are they explicitly authorized?") != "YES":
        blockers.append("risky change requested without explicit authorization")
    if answer_for("Are there two materially valid implementation choices?") == "YES" and not re.search(r"\bHITL-[A-Za-z0-9-]+(-P[0-9]+)?-Q[0-9]+\b", text):
        blockers.append("two valid choices require recorded HITL decision ID")
    if answer_for("Would proceeding require inventing a business rule, permission rule, data rule, or API contract?") == "YES" and not re.search(r"\bHITL-[A-Za-z0-9-]+(-P[0-9]+)?-Q[0-9]+\b", text):
        blockers.append("invented rule/contract requires recorded HITL decision ID")
    result = {
        "pass": not missing and has_check_label and has_gate_header and not missing_gate_rows and not invalid_answers and not weak_evidence and not blockers,
        "missing": missing,
        "has_check_label": has_check_label,
        "has_gate_header": has_gate_header,
        "missing_gate_rows": missing_gate_rows,
        "invalid_gate_answers": invalid_answers,
        "weak_gate_evidence": weak_evidence,
        "blockers": blockers,
    }
    print_json(result)
    if not result["pass"]:
        raise SystemExit(1)


def cmd_lint_prompt(argv):
    if not argv:
        usage("Usage: python3 tools/lint-prompt.py <prompt.md>")
    text = Path(argv[0]).resolve().read_text(encoding="utf-8")

    # Every real Replit prompt in this kit must state these six concepts, but the exact
    # wording differs by source: compile-prompt.py's own output and the compact "gate stub"
    # fixture use literal headings ("## Scope", "## Mandatory HITL Gate", "## Final Report"),
    # while the canonical prose templates (REPLIT_TASK_TEMPLATE.md,
    # REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md) and hand/agent-authored prompts that
    # follow them use different section names ("Phase boundary", "HITL pause rule",
    # "Verify and report"). Each entry below accepts every phrasing actually used by a real
    # source in this kit, so a prompt is not marked broken just for following the templates.
    concept_patterns = {
        "write/read scope or phase boundary": r"\bscope\b|\bphase boundary\b",
        "never-access boundary": r"\bnever access\b",
        "HITL pause policy": r"\bmandatory hitl gate\b|\bhitl pause rule\b",
        "acceptance criteria": r"\bacceptance criteria\b",
        "PASSED/FAILED/NOT RUN result labeling": r"passed/failed/not run|passed.{0,40}failed.{0,40}not run",
        "final report or verify-and-report section": r"\bfinal report\b|##\s*report\b|###\s*verify and report\b|\breport(?:\s+the outcome|:)",
    }
    missing = [name for name, pattern in concept_patterns.items() if not re.search(pattern, text, re.I)]

    # A prompt that is only stating the HITL policy (the normal case for a task/phase prompt)
    # does not need labeled options or a resume point yet - those only apply once a prompt
    # actually emits a concrete HITL decision request (signaled by the literal heading
    # "HITL decision required", which both replit.md and compile-prompt.py use for that).
    emits_hitl_decision = re.search(r"hitl decision required", text, re.I) is not None
    has_labeled_options = re.search(r"(^|\n)A\.\s+.+\nB\.\s+.+", text, re.M) is not None
    has_resume_point = re.search(r"\bresume point\b", text, re.I) is not None
    has_decide_reply = re.search(r"\bDECIDE\b", text) is not None
    if emits_hitl_decision:
        if not has_labeled_options:
            missing.append("labeled HITL decision options (A./B.)")
        if not has_resume_point:
            missing.append("exact resume point for the HITL decision")
        if not has_decide_reply:
            missing.append("DECIDE reply format for the HITL decision")

    has_resume_language = re.search(r"\b(paused|resume)\b", text, re.I) is not None
    result = {
        "pass": not missing and has_resume_language,
        "missing": missing,
        "emits_hitl_decision": emits_hitl_decision,
        "has_labeled_options": has_labeled_options,
        "has_resume_language": has_resume_language,
    }
    print_json(result)
    if not result["pass"]:
        raise SystemExit(1)


# Deliverable signal lists for intake-request.py, matched word-aware via opsgate_lexer instead of
# the regex chain this replaced. The old regex (e.g. r"\baudit|review|findings?\b") only anchored
# \b to the first and last alternative, so "review" and "seeding" etc. matched as bare substrings
# - "review" inside "preview" was a real false-positive risk. First-match-wins order is also
# replaced with scoring plus explicit tie detection, so an outcome that genuinely reads two ways
# ("review and improve the login form") is reported as ambiguous instead of silently picking
# whichever deliverable happened to be checked first.
_INTAKE_DELIVERABLE_SIGNALS = [
    ("audit", ["audit", "review", "finding", "findings"]),
    ("specification", ["spec", "specification", "delta spec"]),
    ("business_file", ["business", "scope", "requirement", "requirements"]),
    ("task_backlog", ["backlog", "task", "tasks"]),
    ("change_record", ["change", "improvement", "amendment"]),
]


def cmd_intake_request(argv):
    text = " ".join(argv)
    if not text:
        usage('Usage: python3 tools/intake-request.py "<plain language request>"')
    scored = [(deliverable, opsgate_lexer.lexical_score(text, signals)[0]) for deliverable, signals in _INTAKE_DELIVERABLE_SIGNALS]
    best_score, tied = opsgate_lexer.top_candidates(scored)
    if best_score <= 0:
        deliverable, tied = "replit_prompt", []
    else:
        deliverable = tied[0]
    module_match = re.search(r"\b(?:module|for|in)\s+([A-Z][A-Za-z0-9 -]{2,40})", text)
    request = {
        "id": f"REQ-{_dt.datetime.now(_dt.timezone.utc).date().isoformat().replace('-', '')}-INTAKE",
        "deliverable": deliverable,
        "outcome": text,
        "module": module_match.group(1).strip() if module_match else None,
        "scope": {"write_paths": [], "read_paths": []},
        "authorizations": {},
        "acceptance": [],
        "must_not_change": [],
    }
    if len(tied) > 1:
        request["intake_notes"] = [
            f"Deliverable is ambiguous between {' and '.join(tied)} - no signal-based winner. "
            f"Defaulted to '{deliverable}'; confirm before treating this as authoritative."
        ]
    if opsgate_lexer.lexical_contains(text, "schema") or opsgate_lexer.lexical_contains(text, "migration") or opsgate_lexer.lexical_contains(text, "backfill"):
        request["authorizations"]["schema_migration_backfill"] = {"authorized": False, "evidence": []}
    if opsgate_lexer.lexical_contains(text, "seed") or opsgate_lexer.lexical_contains(text, "demo data") or opsgate_lexer.lexical_contains(text, "test data"):
        request["authorizations"]["data_seeding"] = {"authorized": False, "evidence": []}
    if any(opsgate_lexer.lexical_contains(text, word) for word in ["package", "config", "environment", "deployment"]):
        request["authorizations"]["package_config_environment_deployment"] = {"authorized": False, "evidence": []}
    if any(opsgate_lexer.lexical_contains(text, word) for word in ["delete", "destructive", "cleanup", "remove"]):
        request["authorizations"]["contract_change_or_destructive_cleanup"] = {"authorized": False, "evidence": []}
    print_json(request)


def cmd_next_phase_prompt(argv):
    if len(argv) < 2:
        usage("Usage: python3 tools/next-phase-prompt.py <run-state.json> <parsed-report.json>")
    state = load_data(argv[0])
    report = load_data(argv[1])
    next_phase = next((phase for phase in state.get("phases", []) if phase.get("status") in ["planned", "ready"]), None)
    if not next_phase:
        print("# No Next Phase\n\nNo planned or ready phase was found in the supplied run state.")
        return
    failed = [check for check in report.get("checks", []) if check.get("status") == "FAILED"]
    blockers = report.get("blockers") or []
    if failed or blockers:
        lines = [*(f"- FAILED: {check.get('text')}" for check in failed), *[f"- {item}" for item in blockers]]
        print(f"# Phase Blocked\n\nDo not generate the next implementation prompt yet.\n\n## Blocking Evidence\n\n{chr(10).join(lines)}")
        return
    not_run = [check for check in report.get("checks", []) if check.get("status") == "NOT RUN"]
    passed_count = len([check for check in report.get("checks", []) if check.get("status") == "PASSED"])
    verification = "\n".join(f"- {item}" for item in next_phase.get("verification_gate", [])) or "- Verify the phase outcome with risk-based checks."
    print(f"""# Prompt for {next_phase.get("id")}

Deliver only: **{next_phase.get("outcome")}**

Use the previous phase report as evidence, not authority.

## Previous Phase Evidence

- Outcome: {report.get("outcome")}
- Files changed: {", ".join(report.get("files_changed") or []) or "none detected"}
- Checks passed: {passed_count}
- Checks not run: {len(not_run)}

## Scope

- Write paths: {", ".join(next_phase.get("write_paths") or []) or "none"}
- Rollback boundary: {next_phase.get("rollback_boundary") or "current phase only"}

## Verification Gate

{verification}

Resume from the next incomplete phase. Do not repeat completed discovery unless scoped drift is detected. Label checks PASSED, FAILED, or NOT RUN.""")


def cmd_init_run(argv):
    if not argv:
        usage("Usage: python3 tools/init-run.py <request.json>")
    request = load_request(argv[0])
    route = route_request(request)
    run_id = request.get("id") or f"REQ-{int(_dt.datetime.now().timestamp() * 1000)}"
    run_dir = ROOT_DIR / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_python_data(run_dir / "request.py", "REQUEST", request, "# Engine run request")
    write_python_data(run_dir / "route.py", "ROUTE", route, "# Engine run route")
    write_python_data(run_dir / "gate_result.py", "GATE_RESULT", {"request_id": run_id, "status": "blocked" if route.get("blocked") else "pending_preflight", "failed_gates": ["capability_gate"] if route.get("blocked") else [], "missing_authority": route.get("missing_authority") or []}, "# Engine run gate result")
    write_python_data(run_dir / "handoff.py", "HANDOFF", {"request_id": run_id, "completed": False, "next_phase_ready": False, "blockers": route.get("missing_authority") or [] if route.get("blocked") else []}, "# Engine run handoff")
    print_json({"run_id": run_id, "run_dir": str(run_dir.relative_to(ROOT_DIR))})


def cmd_record_decision(argv):
    if len(argv) < 2:
        usage("Usage: python3 tools/record-decision.py <HITL-ID> <answer and exact scope>")
    entry = {"recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"), "id": argv[0], "answer": " ".join(argv[1:])}
    decisions = ROOT_DIR / "runs" / "decisions.pylog"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    with decisions.open("a", encoding="utf-8") as handle:
        handle.write(repr(entry) + "\n")
    print_json(entry)


def relative_map(base):
    base = Path(base).resolve()
    out = {}
    for file_path in list_files(base):
        rel = str(file_path.relative_to(base))
        if ".zip" in rel or "dist/" in rel:
            continue
        out[rel] = {"file": file_path, "hash": sha256(file_path)}
    return out


def cmd_diff_upgrade(argv):
    if not argv:
        usage("Usage: python3 tools/diff-upgrade.py <old-kit-root> [new-kit-root]")
    old_root = Path(argv[0]).resolve()
    new_root = Path(argv[1]).resolve() if len(argv) > 1 else ROOT_DIR / "canonical"
    old_map = relative_map(old_root)
    new_map = relative_map(new_root)
    added = [rel for rel in new_map if rel not in old_map]
    changed = [rel for rel in new_map if rel in old_map and old_map[rel]["hash"] != new_map[rel]["hash"]]
    removed = [rel for rel in old_map if rel not in new_map]
    all_changed = [*added, *changed, *removed]
    result = {
        "compared_at": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "old_root": str(old_root),
        "new_root": str(new_root),
        "added": added,
        "changed": changed,
        "removed": removed,
        "reinstall_replit_when_changed": ["references/replit.md", "references/ai/**", "references/replit-skills/**"],
        "reinstall_claude_when_changed": ["CLAUDE_PROJECT_INSTRUCTIONS.md", "templates/**", "references/**", "specifications/**", "claude-skills/**"],
        "classification": {
            "claude_reinstall": any(re.search(r"^(CLAUDE_PROJECT_INSTRUCTIONS|templates|references|specifications|claude-skills)\b", item) for item in all_changed),
            "replit_reinstall": any(re.search(r"^references/(replit\.md|ai/|replit-skills/)", item) for item in all_changed),
            "manual_review": any(re.search(r"(protected|capability|HITL|replit\.md|SKILL\.md|ENGINE_FOUNDATION_SPEC)", item, re.I) for item in all_changed),
        },
    }
    print_json(result)


def cmd_release_notes(argv):
    old_root = argv[0] if argv else "../audit_unpack/old-kit-root"
    diff = json.loads(capture_python("diff-upgrade", [old_root, "canonical"]))
    changed = "\n".join(f"- {item}" for item in diff["changed"]) or "- None"
    added_engine = "\n".join(f"- {item}" for item in [item for item in diff["added"] if "ENGINE" in item or "gold-standard" in item or "claude-skills" in item][:40]) or "- None detected"
    print(f"""# Kit Release Notes

Generated from upgrade diff.

## Summary

- Added files: {len(diff["added"])}
- Changed files: {len(diff["changed"])}
- Removed or relocated files: {len(diff["removed"])}

## Reinstall Guidance

- Rebuild Claude distribution when project instructions, templates, references, specifications, or Claude skill sources changed.
- Reinstall Replit distribution when `references/replit.md`, `references/ai/**`, or `references/replit-skills/**` changed.
- Run `python3 tools/validate-kit.py` before release.

## Changed Files

{changed}

## Added Engine Files

{added_engine}""")


def reset_dir(relative_path):
    target = ROOT_DIR / relative_path
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)


def make_zip(zip_path, source_dir):
    zip_path = Path(zip_path)
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in list_files(source_dir):
            archive.write(file_path, file_path.relative_to(source_dir))


def cmd_build_distributions(argv):
    distributions = read_json("manifests/distributions.json")
    reset_dir("dist/claude")
    reset_dir("dist/replit")
    for source, target in distributions["claude"]["copies"]:
        copy_recursive(ROOT_DIR / source, ROOT_DIR / target)
    for source, target in distributions["replit"]["copies"]:
        copy_recursive(ROOT_DIR / source, ROOT_DIR / target)
    claude_root = ROOT_DIR / "dist/claude/claude-skill"
    copy_recursive(ROOT_DIR / "canonical/claude-skills", claude_root)
    for source, target in distributions["claude"]["skill_reference_mappings"]:
        copy_recursive(ROOT_DIR / source, claude_root / target)
    for package_name in distributions["claude"]["skill_packages"]:
        make_zip(claude_root / f"{package_name}.zip", claude_root / package_name)
    shutil.copy2(claude_root / "replit-task-builder.zip", claude_root / "skill.zip")
    dist_files = list_files(ROOT_DIR / "dist", lambda path: not str(path).endswith(".DS_Store"))
    manifest = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "files": [{"path": str(path.relative_to(ROOT_DIR)), "sha256": sha256(path)} for path in dist_files],
    }
    write_python_data(ROOT_DIR / "dist/release_hashes.py", "RELEASE_HASHES", manifest, "# Generated engine release hashes")
    print("Built Claude and Replit distributions.")


def cmd_build_replit_install(argv):
    target = ROOT_DIR / "dist/replit-install"
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    copy_recursive(ROOT_DIR / "dist/replit/replit.md", target / "replit.md")
    copy_recursive(ROOT_DIR / "dist/replit/ai", target / "ai")
    copy_recursive(ROOT_DIR / "dist/replit/.agents", target / ".agents")
    write_text(target / "INSTALL.md", """# Replit Install

Copy these generated files into the root of the target Replit project:

- `replit.md`
- `ai/**`
- `.agents/skills/**`

Do not copy Claude-only templates, specifications, or packaged skills into Replit.
""")
    print("Built dist/replit-install")


def cmd_audit_engine(argv):
    project_root = Path(argv[0]).resolve() if argv else ROOT_DIR.parent.resolve()
    checks = []

    def check(name, passed, evidence):
        checks.append({"name": name, "status": "PASSED" if passed else "FAILED", "evidence": evidence})

    check("root replit aligns with generated install", same_bytes(project_root / "replit.md", ROOT_DIR / "dist/replit-install/replit.md"), "replit.md compared to <engine-dir>/dist/replit-install/replit.md")
    for file_path in list_files(ROOT_DIR / "dist/replit-install/ai", lambda item: str(item).endswith(".md")):
        rel = file_path.relative_to(ROOT_DIR / "dist/replit-install")
        check(f"root {rel} aligns", same_bytes(project_root / rel, file_path), str(rel))
    for file_path in list_files(ROOT_DIR / "dist/replit-install/.agents/skills", lambda item: str(item).endswith("SKILL.md")):
        rel = file_path.relative_to(ROOT_DIR / "dist/replit-install")
        check(f"root {rel} aligns", same_bytes(project_root / rel, file_path), str(rel))
    check("Python contracts exist", (ROOT_DIR / "tools/opsgate_contracts.py").exists(), "<engine-dir>/tools/opsgate_contracts.py")
    check("tools exist", (ROOT_DIR / "tools/preflight.py").exists(), "<engine-dir>/tools/preflight.py")
    result = {"project_root": str(project_root), "checks": checks, "pass": not any(item["status"] == "FAILED" for item in checks)}
    print_json(result)
    if not result["pass"]:
        raise SystemExit(1)


def validate_value(value, spec, schema, pointer="$", failures=None):
    failures = failures if failures is not None else []
    if not spec:
        return failures
    if "$ref" in spec:
        ref = spec["$ref"]
        if ref.startswith("#/$defs/"):
            spec = schema.get("$defs", {}).get(ref[len("#/$defs/"):], {})
    expected_type = spec.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            failures.append(f"{pointer} must be object")
            return failures
        for required in spec.get("required", []):
            if required not in value:
                failures.append(f"{pointer}.{required} is required")
        for key, child in spec.get("properties", {}).items():
            if key in value:
                validate_value(value[key], child, schema, f"{pointer}.{key}", failures)
    elif expected_type == "array":
        if not isinstance(value, list):
            failures.append(f"{pointer} must be array")
            return failures
        if "minItems" in spec and len(value) < spec["minItems"]:
            failures.append(f"{pointer} must have at least {spec['minItems']} items")
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            failures.append(f"{pointer} must have at most {spec['maxItems']} items")
        for index, item in enumerate(value):
            validate_value(item, spec.get("items", {}), schema, f"{pointer}[{index}]", failures)
    elif expected_type == "string":
        if not isinstance(value, str):
            failures.append(f"{pointer} must be string")
        else:
            if "minLength" in spec and len(value) < spec["minLength"]:
                failures.append(f"{pointer} is too short")
            if "pattern" in spec and not re.search(spec["pattern"], value):
                failures.append(f"{pointer} does not match {spec['pattern']}")
            if "enum" in spec and value not in spec["enum"]:
                failures.append(f"{pointer} must be one of {', '.join(spec['enum'])}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            failures.append(f"{pointer} must be integer")
        elif "enum" in spec and value not in spec["enum"]:
            failures.append(f"{pointer} must be one of {', '.join(map(str, spec['enum']))}")
    elif expected_type == "boolean" and not isinstance(value, bool):
        failures.append(f"{pointer} must be boolean")
    return failures


def cmd_validate_json(argv):
    if len(argv) < 2:
        usage("Usage: python3 tools/validate-json.py <schema-contract> <data-file>")
    schema = read_json(argv[0])
    data = load_data(argv[1])
    failures = validate_value(data.get("request") or data, schema, schema)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS {Path(argv[1]).relative_to(ROOT_DIR) if str(Path(argv[1])).startswith(str(ROOT_DIR)) else argv[1]} matches {argv[0]}")


def capture_python(command, args):
    return subprocess.check_output([sys.executable, str(ROOT_DIR / "tools" / f"{command}.py"), *args], cwd=ROOT_DIR, text=True)


def run_python(command, args, expect=None):
    completed = subprocess.run([sys.executable, str(ROOT_DIR / "tools" / f"{command}.py"), *args], cwd=ROOT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if expect is not None and completed.returncode != expect:
        raise RuntimeError(completed.stderr or completed.stdout)
    if expect is None and completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return completed


def cmd_validate_kit(argv):
    failures = []
    warnings = []

    def fail(message):
        failures.append(message)

    def warn(message):
        warnings.append(message)

    def assert_exists(relative_path):
        if not exists(relative_path):
            fail(f"Missing required path: {relative_path}")

    assert_exists("tools/opsgate_contracts.py")
    for contract_name, contract_value in opsgate_contracts.CONTRACTS.items():
        if not isinstance(contract_value, dict):
            fail(f"Invalid Python contract shape: {contract_name}")
    protected_paths = read_json("manifests/protected-paths.json")
    never_access = protected_paths.get("profiles", {}).get("metco", {}).get("never_access", [])
    for required in ["metco-api/**", "pipeline/**"]:
        if required not in never_access:
            fail(f"Protected path rule missing: {required}")
    if "Risk, complexity, security, destructiveness" not in read_text("canonical/specifications/HITL_SPEC.md"):
        fail("HITL spec no longer clearly separates risk/complexity from HITL triggers.")
    replit_text = read_text("canonical/references/replit.md")
    for required in ["Mandatory HITL Gate", "HITL Gate Result", "HITL decision required", "Per-Action Gate"]:
        if required not in replit_text:
            fail(f"Root replit policy missing {required}")
    skill_root = ROOT_DIR / "canonical/references/replit-skills"
    for skill_file in list_files(skill_root, lambda path: str(path).endswith("SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        frontmatter = parse_skill_frontmatter(text)
        relative = skill_file.relative_to(ROOT_DIR)
        if not frontmatter:
            fail(f"Skill missing frontmatter: {relative}")
            continue
        if ",".join(sorted(frontmatter.keys())) != "description,name":
            fail(f"Skill frontmatter must contain only name and description: {relative}")
        if frontmatter.get("name") != skill_file.parent.name:
            fail(f"Skill folder/name mismatch: {relative}")
        if "Mandatory HITL Gate" not in text:
            fail(f"Skill missing Mandatory HITL Gate reminder: {relative}")
        if "Per-Action Gate" not in text:
            fail(f"Skill missing Per-Action Gate reminder: {relative}")
    routing = read_json("manifests/routing.manifest.json")
    for route in routing.get("replit_routes", []):
        assert_exists(f"canonical/references/replit-skills/{route['skill']}/SKILL.md")
        for reference in route.get("references", []):
            assert_exists(f"canonical/references/{reference}")
    for route in routing.get("artifact_routes", []):
        assert_exists(f"canonical/{route['template']}")
    # DIST-006: every canonical->distribution copy declared in DISTRIBUTIONS must be byte-identical,
    # not just a hand-picked sample. Covers top-level Claude/Replit copies plus every per-skill
    # reference mapping (~25 files across both packaged skills).
    distributions = read_json("manifests/distributions.json")
    drift_pairs = [
        *distributions["claude"]["copies"],
        *[[source, f"dist/claude/claude-skill/{target}"] for source, target in distributions["claude"]["skill_reference_mappings"]],
        *distributions["replit"]["copies"],
    ]
    for source, target in drift_pairs:
        source_path = ROOT_DIR / source
        target_path = ROOT_DIR / target
        if not target_path.exists():
            warn(f"Generated path not found yet: {target}. Run build-distributions.")
            continue
        if source_path.is_dir():
            for file_path in list_files(source_path):
                relative_file = file_path.relative_to(source_path)
                target_file = target_path / relative_file
                if not target_file.exists():
                    fail(f"Generated file missing: {target}/{relative_file}")
                elif not same_bytes(file_path, target_file):
                    fail(f"Generated file drifted from canonical source: {target}/{relative_file}")
        elif not same_bytes(source_path, target_path):
            fail(f"Generated file drifted from canonical source: {target}")
    ooi_sections = ["Responsibility", "Activation", "Inputs", "Must Not", "Workflow", "Output Evidence"]
    for file_path in list_files(ROOT_DIR / "canonical/references/ai", lambda path: str(path).endswith(".md")):
        text = file_path.read_text(encoding="utf-8")
        missing_sections = [section for section in ooi_sections if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.M)]
        if missing_sections:
            fail(f"Instruction object missing sections in {file_path.relative_to(ROOT_DIR)}: {', '.join(missing_sections)}")
    for file_path in list_files(ROOT_DIR / "canonical/templates", lambda path: str(path).endswith(".md")):
        text = file_path.read_text(encoding="utf-8")
        for forbidden in ["Mode:", "Primary skill:", "Complexity:", "Execution profile:"]:
            if forbidden in text:
                fail(f'Forbidden user-facing routing field "{forbidden}" in {file_path.relative_to(ROOT_DIR)}')
    for zip_path in list_files(ROOT_DIR / "dist/claude", lambda path: str(path).endswith(".zip")):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                bad = archive.testzip()
                if bad:
                    raise RuntimeError(bad)
        except Exception:
            fail(f"Invalid zip archive: {zip_path.relative_to(ROOT_DIR)}")
    for fixture in opsgate_fixtures.ROUTING_FIXTURES:
        expected = fixture["data"].get("expected", {})
        actual = route_request(fixture["data"].get("request") or fixture["data"])
        for key, expected_value in expected.items():
            if key == "missing_authority_contains":
                for item in expected_value:
                    if item not in (actual.get("missing_authority") or []):
                        fail(f"Routing fixture {fixture['path']} missing authority item {item}")
            elif actual.get(key) != expected_value:
                fail(f"Routing fixture {fixture['path']} expected {key}={expected_value}, got {actual.get(key)}")
    for fixture in opsgate_fixtures.HITL_FIXTURES:
        data = fixture["data"]
        relative = fixture["path"]
        if data.get("case") not in [1, 2, 3]:
            fail(f"Invalid HITL case in {relative}")
        if not isinstance(data.get("options"), list) or not (2 <= len(data["options"]) <= 4):
            fail(f"HITL fixture must provide 2-4 decision options in {relative}")
        if not str(data.get("exact_resume_point") or "").strip():
            fail(f"HITL fixture missing exact resume point in {relative}")
        if not str(data.get("resume_reply") or "").startswith(f"DECIDE {data.get('id')}: "):
            fail(f"Invalid HITL resume reply in {relative}")
    compiled = capture_python("compile-prompt", ["fixtures/routing/frontend-task.json"])
    for required in ["Vendor approvals", "frontend-development", "Acceptance Criteria", "PASSED/FAILED/NOT RUN", "Mandatory HITL Gate", "HITL decision required", "HITL Gate Result", "Per-Action Gate"]:
        if required not in compiled:
            fail(f"Compiled prompt missing expected text: {required}")
    if re.search(r"\[[^\]]+\]", compiled):
        fail("Compiled prompt still contains bracket-style unresolved placeholders.")
    state = json.loads(capture_python("init-state", ["fixtures/routing/migration-task-missing-auth.json"]))
    if state.get("status") != "blocked" or state.get("execution_shape") != "phased":
        fail("Init state fixture did not produce blocked phased state for migration missing auth.")
    parsed_report = json.loads(capture_python("parse-report", ["fixtures/reports/sample-replit-final-report.md"]))
    if not any(check.get("status") == "PASSED" for check in parsed_report.get("checks", [])):
        fail("Report parser did not detect PASSED check.")
    if not any(check.get("status") == "NOT RUN" for check in parsed_report.get("checks", [])):
        fail("Report parser did not detect NOT RUN check.")
    try:
        run_python("check-paths", ["fixtures/routing/frontend-task.json"])
        run_python("preflight", ["fixtures/routing/frontend-task.json"])
        run_python("lint-prompt", ["fixtures/prompts/frontend-compiled-with-gate.md"])
        run_python("lint-report", ["fixtures/reports/sample-replit-final-report.md"])
        run_python("audit-engine", ["dist/replit-install"])
    except Exception:
        fail("Gate/path/prompt/report/engine audit command failed.")
    try:
        run_python("check-capabilities", ["fixtures/routing/migration-task-missing-auth.json"], expect=1)
        run_python("validate-json", ["manifests/request.schema.json", "fixtures/routing/frontend-task.json"])
        run_python("validate-json", ["manifests/report.schema.json", "fixtures/reports/parsed-sample-report.json"])
        for fixture in opsgate_fixtures.HITL_FIXTURES:
            run_python("validate-json", ["manifests/hitl.schema.json", fixture["path"]])
        run_python("lint-prompt", ["fixtures/prompts/invalid-missing-hitl-options.md"], expect=1)
        run_python("lint-report", ["fixtures/reports/invalid-weak-hitl-report.md"], expect=1)
    except Exception:
        fail("Negative or Python contract validation fixture failed unexpectedly.")
    intake = json.loads(capture_python("intake-request", ["Audit the Roles module without changing code"]))
    if intake.get("deliverable") != "audit":
        fail("Intake helper did not infer audit deliverable.")
    if "Prompt for PHASE-1" not in capture_python("next-phase-prompt", ["fixtures/state/ready-phased-state.json", "fixtures/reports/parsed-sample-report.json"]):
        fail("Next phase prompt command did not generate PHASE-1 prompt.")
    try:
        run_python("build-replit-install", [])
    except Exception:
        fail("Replit install helper failed.")
    if not (ROOT_DIR / "dist/replit-install/INSTALL.md").exists():
        fail("Replit install helper did not create INSTALL.md.")
    diff = json.loads(capture_python("diff-upgrade", ["../audit_unpack/old-kit-root", "canonical"]))
    if "classification" not in diff:
        fail("Upgrade diff did not include classification.")
    for warning in warnings:
        print(f"WARN {warning}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS validation complete ({len(warnings)} warnings).")


def cmd_test_all(argv):
    """Single entrypoint that exercises every tool in the kit against every fixture.

    Broader than validate-kit: validate-kit spot-checks one or two fixtures per command as
    part of its own contract checks. This command runs every routing fixture through
    route-request, compile-prompt, init-state, preflight, and check-capabilities; runs every
    HITL fixture through schema validation; runs both positive and negative prompt/report
    fixtures through their linters; self-diffs canonical against itself; and smoke-tests the
    run-state helpers, cleaning up any runs/ output it creates.
    """
    results = []

    def record(name, ok, detail=""):
        results.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f" -- {detail}" if detail and not ok else ""))

    def try_run(name, command, args, expect_exit=0):
        try:
            completed = subprocess.run(
                [sys.executable, str(ROOT_DIR / "tools" / f"{command}.py"), *args],
                cwd=ROOT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            ok = completed.returncode == expect_exit
            detail = "" if ok else f"expected exit {expect_exit}, got {completed.returncode}: {(completed.stderr or completed.stdout).strip()[:200]}"
            record(name, ok, detail)
            return completed.stdout
        except Exception as exc:
            record(name, False, str(exc))
            return ""

    # 1. Build the kit, then run the existing validator. validate-kit already covers Python
    #    contract shape, protected-path presence, HITL wording, skill frontmatter, the full
    #    canonical<->distribution drift check, forbidden template fields, zip integrity, the
    #    routing/HITL fixtures, one compiled-prompt spot check, and the negative lint fixtures.
    try_run("build-distributions", "build-distributions", [])
    validate_out = try_run("validate-kit", "validate-kit", [])
    if validate_out and not validate_out.strip().startswith("PASS"):
        record("validate-kit reported failures", False, validate_out.strip()[:300])
    try_run("build-replit-install", "build-replit-install", [])

    # 2. Exercise every routing fixture end to end, not just the one or two validate-kit
    #    spot-checks. Compare preflight/check-capabilities exit codes against what the routing
    #    engine itself decided, so the gate commands are checked for internal consistency
    #    instead of against a hand-authored "expected blocked" value that not every fixture sets.
    for fixture in opsgate_fixtures.ROUTING_FIXTURES:
        path = fixture["path"]
        route = route_request(fixture["data"].get("request") or fixture["data"])
        expect_blocked = 1 if route.get("blocked") else 0
        try_run(f"route-request {path}", "route-request", [path])
        try_run(f"compile-prompt {path}", "compile-prompt", [path])
        try_run(f"init-state {path}", "init-state", [path])
        try_run(f"preflight {path}", "preflight", [path], expect_exit=expect_blocked)
        try_run(f"check-capabilities {path}", "check-capabilities", [path], expect_exit=expect_blocked)

    # 3. Every HITL fixture must validate against the HITL schema.
    for fixture in opsgate_fixtures.HITL_FIXTURES:
        try_run(f"validate-json (hitl) {fixture['path']}", "validate-json", ["manifests/hitl.schema.json", fixture["path"]])

    # 4. Positive and negative report/prompt lint fixtures.
    try_run("parse-report sample", "parse-report", ["fixtures/reports/sample-replit-final-report.md"])
    try_run("lint-report valid fixture", "lint-report", ["fixtures/reports/sample-replit-final-report.md"])
    try_run("lint-report invalid fixture (expect fail)", "lint-report", ["fixtures/reports/invalid-weak-hitl-report.md"], expect_exit=1)
    try_run("lint-prompt valid fixture", "lint-prompt", ["fixtures/prompts/frontend-compiled-with-gate.md"])
    try_run("lint-prompt invalid fixture (expect fail)", "lint-prompt", ["fixtures/prompts/invalid-missing-hitl-options.md"], expect_exit=1)

    # 5. Self-diff: canonical compared against itself must report zero drift, proving the
    #    upgrade-diff tool itself is trustworthy before it's ever pointed at a real old kit.
    diff_out = try_run("diff-upgrade self-diff", "diff-upgrade", [str(ROOT_DIR / "canonical"), str(ROOT_DIR / "canonical")])
    if diff_out:
        try:
            diff = json.loads(diff_out)
            empty = not diff["added"] and not diff["changed"] and not diff["removed"]
            record("diff-upgrade self-diff is empty", empty, "self-diff reported unexpected changes" if not empty else "")
        except Exception as exc:
            record("diff-upgrade self-diff is empty", False, str(exc))
    try_run("release-notes", "release-notes", [str(ROOT_DIR / "canonical")])

    # 6. Light smoke test of the run-state helpers; clean up the runs/ directory afterward so
    #    repeat runs don't leave residue behind.
    try_run("intake-request", "intake-request", ["Audit the Roles module without changing code"])
    try_run("show-profile (default)", "show-profile", [])
    default_profile_out = json.loads(capture_python("show-profile", []))
    if default_profile_out.get("resolved_profile") != opsgate_contracts.PROFILES.get("default_profile"):
        record("show-profile matches default_profile", False, f"expected {opsgate_contracts.PROFILES.get('default_profile')}, got {default_profile_out.get('resolved_profile')}")
    else:
        record("show-profile matches default_profile", True)
    os.environ["OPSGATE_PROFILE"] = "generic-replit"
    try:
        generic_out = json.loads(capture_python("show-profile", []))
        record("show-profile honors OPSGATE_PROFILE override", generic_out.get("resolved_profile") == "generic-replit", str(generic_out.get("resolved_profile")))
    finally:
        del os.environ["OPSGATE_PROFILE"]
    # Legacy env var name from before the 6.0.13 generalization rename - a deployment that
    # still sets METCO_PROFILE as its Repl Secret must keep resolving correctly without any
    # action on its part.
    os.environ["METCO_PROFILE"] = "metco"
    try:
        legacy_out = json.loads(capture_python("show-profile", []))
        record(
            "show-profile honors legacy METCO_PROFILE override",
            legacy_out.get("resolved_profile") == "metco" and legacy_out.get("resolved_from") == "METCO_PROFILE env var (legacy name)",
            str(legacy_out.get("resolved_profile")),
        )
    finally:
        del os.environ["METCO_PROFILE"]
    try_run("init-run", "init-run", ["fixtures/routing/frontend-task.json"])
    try_run("next-phase-prompt", "next-phase-prompt", ["state:ready-phased-state", "reports:parsed-sample-report"])
    try_run("record-decision", "record-decision", ["HITL-example-P1-Q1", "Use the approved feature owner only"])
    shutil.rmtree(ROOT_DIR / "runs", ignore_errors=True)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = [r for r in results if r["status"] == "FAIL"]
    print(f"\n{passed}/{len(results)} checks passed.")
    if failed:
        for r in failed:
            print(f"FAIL: {r['name']} -- {r['detail']}", file=sys.stderr)
        raise SystemExit(1)
    print("PASS test-all: full kit exercised cleanly.")


COMMANDS = {
    "audit-engine": cmd_audit_engine,
    "build-distributions": cmd_build_distributions,
    "build-replit-install": cmd_build_replit_install,
    "check-capabilities": cmd_check_capabilities,
    "check-paths": cmd_check_paths,
    "compile-prompt": cmd_compile_prompt,
    "diff-upgrade": cmd_diff_upgrade,
    "init-run": cmd_init_run,
    "init-state": cmd_init_state,
    "intake-request": cmd_intake_request,
    "lint-prompt": cmd_lint_prompt,
    "lint-report": cmd_lint_report,
    "next-phase-prompt": cmd_next_phase_prompt,
    "parse-report": cmd_parse_report,
    "preflight": cmd_preflight,
    "record-decision": cmd_record_decision,
    "release-notes": cmd_release_notes,
    "route-request": cmd_route_request,
    "show-profile": cmd_show_profile,
    "test-all": cmd_test_all,
    "validate-json": cmd_validate_json,
    "validate-kit": cmd_validate_kit,
}


def main():
    command = Path(sys.argv[0]).stem
    if command == "opsgate_tools":
        if len(sys.argv) < 2:
            usage(f"Usage: python3 tools/opsgate_tools.py <{'|'.join(sorted(COMMANDS))}> [args...]")
        command = sys.argv[1]
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    if command not in COMMANDS:
        usage(f"Unknown command: {command}")
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
