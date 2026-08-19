#!/usr/bin/env python3
"""CLI command implementations and dispatcher.

Focused sibling modules (opsgate_tenants, opsgate_profiles, opsgate_io, opsgate_routing,
opsgate_prompts, opsgate_validation, opsgate_selftest) own routing, prompt compilation, tenant
resolution, and self-testing; this file is the cmd_* command handlers (each one thin,
orchestrating calls into the modules above) plus the COMMANDS dispatch table this file's own
CLI entrypoint (`python3 tools/opsgate.py <command> [args...]`) and
mcp-server/opsgate_mcp_server.py both rely on.
"""
import datetime as _dt
import json
import re
import sys
from pathlib import Path

import opsgate_contracts
import opsgate_lexer
import opsgate_tenants
from opsgate_io import ROOT_DIR, load_data, load_request, print_json, usage, write_python_data
from opsgate_prompts import compile_artifact_prompt, compile_replit_prompt
from opsgate_profiles import matches_protected, read_json
from opsgate_routing import route_request, unique
from opsgate_validation import REQUIRED_GATE_ROWS, extract_section, is_placeholder, parse_markdown_table, validate_value
from opsgate_selftest import cmd_test_all, cmd_validate_engine


def _extract_tenant_flag(argv):
    """Pulls a leading/trailing `--tenant <id>` flag out of argv - e.g. `python3
    tools/opsgate.py show-profile --tenant acme`. Defaults to opsgate_tenants.LOCAL_DEV_TENANT_ID
    when omitted, so the bare CLI has a safe, always-available identity with no setup required.
    Returns (tenant_id, remaining_positional_argv)."""
    if "--tenant" not in argv:
        return opsgate_tenants.LOCAL_DEV_TENANT_ID, argv
    index = argv.index("--tenant")
    if index + 1 >= len(argv):
        usage("--tenant requires a value, e.g. --tenant acme")
    tenant_id = argv[index + 1]
    remaining = argv[:index] + argv[index + 2:]
    return tenant_id, remaining


def cmd_route_request(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py route-request <request.json> [--tenant <id>]")
    print_json(route_request(load_request(argv[0]), tenant_id=tenant_id))


def check_capabilities_result(request, tenant_id=None):
    route = route_request(request, tenant_id=tenant_id)
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
    return {"can_proceed": len(missing) == 0, "route_capability": route.get("capability"), "missing": missing}


def cmd_check_capabilities(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py check-capabilities <request.json> [--tenant <id>]")
    result = check_capabilities_result(load_request(argv[0]), tenant_id=tenant_id)
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def show_profile_result(request, tenant_id=None):
    """Resolve the caller's tenant profile in full - name, roots, and protected paths. `request`
    is accepted for call-site symmetry with the other *_result functions but is otherwise
    unused - every field that used to come from it (an explicit "profile" field) is now resolved
    by tenant identity instead. `tenant_id` defaults to opsgate_tenants.LOCAL_DEV_TENANT_ID."""
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    profile_record = opsgate_tenants.get_profile(tenant_id)
    return {
        "resolved_profile": tenant_id,
        "profile_record": profile_record or {},
        "protected_paths": opsgate_tenants.protected_paths_for_tenant(tenant_id) or {},
    }


def cmd_show_profile(argv):
    """Print the resolved tenant profile - see show_profile_result() for the real logic.
    Defaults to opsgate_tenants.LOCAL_DEV_TENANT_ID; pass --tenant <id> for any other tenant."""
    tenant_id, argv = _extract_tenant_flag(argv)
    request = load_request(argv[0]) if argv else {}
    print_json(show_profile_result(request, tenant_id=tenant_id))


def check_paths_result(request, tenant_id=None):
    protected_paths = opsgate_tenants.protected_paths_for_tenant(tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID)
    scope = request.get("scope") or {}
    all_paths = [*(scope.get("write_paths") or []), *(scope.get("read_paths") or [])]
    violations = []
    for candidate in all_paths:
        for protected_pattern in (protected_paths or {}).get("never_access", []):
            if matches_protected(candidate, protected_pattern):
                violations.append({"path": candidate, "protected_pattern": protected_pattern})
    return {"can_proceed": len(violations) == 0, "checked_paths": all_paths, "violations": violations}


def cmd_check_paths(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py check-paths <request.json> [--tenant <id>]")
    result = check_paths_result(load_request(argv[0]), tenant_id=tenant_id)
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def preflight_result(request, tenant_id=None):
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    route = route_request(request, tenant_id=tenant_id)
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
    # Reuse matches_protected() (the exact same check cmd_check_paths/check_paths_result uses)
    # rather than a second, independently-drifting inline implementation - preflight and
    # check-paths must agree on every path, not just usually agree.
    protected_paths = opsgate_tenants.protected_paths_for_tenant(tenant_id)
    protected_patterns = (protected_paths or {}).get("never_access", [])
    for candidate in [*write_paths, *read_paths]:
        for pattern in protected_patterns:
            if matches_protected(candidate, pattern):
                failed_gates.append(f"protected_path_gate: {candidate}")
    # Every gate this function checks - scope, capability, protected-path - is deterministic:
    # a fixed rule evaluated against the request, with one correct answer and no judgment
    # involved. None of them is a HITL case. A failure here means "explicit authorization or
    # scope is missing," not "a human must choose between options." Treat every gate the same
    # way: name it, say what it needs, and stop - do not route any of them through the HITL
    # decision-required ceremony, which is reserved for the three genuine ambiguity cases
    # (unknown next step, tied valid options, self-made scope-expanding decision) that can only
    # be discovered during actual work, not from a request file before anything has been touched.
    return {
        "request_id": request.get("id"),
        "route": route,
        "gates_version": gates.get("version"),
        "can_proceed": len(failed_gates) == 0,
        "failed_gates": unique(failed_gates),
        "blocked": len(failed_gates) > 0,
        "blocked_gate_kind": "deterministic" if failed_gates else None,
        "evidence": evidence,
    }


def cmd_preflight(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py preflight <request.json> [--tenant <id>]")
    result = preflight_result(load_request(argv[0]), tenant_id=tenant_id)
    print_json(result)
    if not result["can_proceed"]:
        raise SystemExit(1)


def compile_prompt_text(request, tenant_id=None):
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    route = route_request(request, tenant_id=tenant_id)
    # A caller-supplied request["mcp"] always wins (including an explicit {"enabled": False} to
    # force the manual prose gate even for an mcp_enabled tenant) - this only fills in a default
    # when the caller didn't say anything, from the resolved tenant's own profile. Without this,
    # every single compile call for a tenant whose Replit project genuinely has these MCP tools
    # registered would need to remember to pass mcp.enabled itself, every time, forever - a
    # property of the tenant's real setup, not something to re-specify per request.
    if "mcp" not in request and (opsgate_tenants.get_profile(tenant_id) or {}).get("mcp_enabled"):
        request = {**request, "mcp": {"enabled": True}}
    if route.get("deliverable") == "replit_prompt":
        protected_paths = opsgate_tenants.protected_paths_for_tenant(tenant_id)
        prompt = compile_replit_prompt(request, route, protected_paths=protected_paths)
    else:
        prompt = compile_artifact_prompt(request, route)
    return prompt.strip()


def cmd_compile_prompt(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py compile-prompt <request.json> [--tenant <id>]")
    print(compile_prompt_text(load_request(argv[0]), tenant_id=tenant_id))


def init_state_result(request, tenant_id=None):
    route = route_request(request, tenant_id=tenant_id)
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
                "status": "blocked" if route.get("blocked") else "planned",
                "outcome": request.get("outcome"),
                "write_paths": (request.get("scope") or {}).get("write_paths") or [],
                "verification_gate": request.get("acceptance") or [],
                "rollback_boundary": "Current phase changed files only",
            },
        ]
    return state


def cmd_init_state(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py init-state <request.json> [--tenant <id>]")
    print_json(init_state_result(load_request(argv[0]), tenant_id=tenant_id))


def parse_report_result(text):
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
    outcome_section = collect_section([r"^#+\s*outcome", r"^#+\s*summary"])
    acceptance_section = collect_section([r"^#+\s*acceptance"])
    blockers = collect_section([r"^#+\s*blockers?", r"^#+\s*limitations?"])
    risk = collect_section([r"^#+\s*residual risk", r"^#+\s*remaining risk"])
    # True only if at least one recognizable section/marker was actually found in the text.
    # Distinguishes "the report says nothing failed" from "this input didn't look like a report
    # at all" - callers (next_phase_prompt_text) must not treat the latter as a clean pass.
    has_signal = bool(outcome_section or acceptance_section or checks or files or hitl or blockers or risk)
    return {
        "outcome": (outcome_section or ["Not detected"])[0],
        "acceptance_status": (acceptance_section or ["Not detected"])[0],
        "files_changed": unique(files),
        "checks": checks,
        "hitl_decisions": hitl,
        "blockers": blockers,
        "residual_risk": risk or ["Not detected"],
        "has_signal": has_signal,
    }


def cmd_parse_report(argv):
    if not argv:
        usage("Usage: python3 tools/opsgate.py parse-report <report.md>")
    print_json(parse_report_result(Path(argv[0]).resolve().read_text(encoding="utf-8")))


def lint_report_result(text):
    # Sourced from GATES['gates']['final_report_gate']['required_sections'] rather than a
    # second hardcoded copy - the two lists were already identical, just independently
    # maintained, which is exactly the kind of declared-vs-enforced drift risk this fixes.
    required = read_json("manifests/gates.json")["gates"]["final_report_gate"]["required_sections"]
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
    return {
        "pass": not missing and has_check_label and has_gate_header and not missing_gate_rows and not invalid_answers and not weak_evidence and not blockers,
        "missing": missing,
        "has_check_label": has_check_label,
        "has_gate_header": has_gate_header,
        "missing_gate_rows": missing_gate_rows,
        "invalid_gate_answers": invalid_answers,
        "weak_gate_evidence": weak_evidence,
        "blockers": blockers,
    }


def cmd_lint_report(argv):
    if not argv:
        usage("Usage: python3 tools/opsgate.py lint-report <report.md>")
    result = lint_report_result(Path(argv[0]).resolve().read_text(encoding="utf-8"))
    print_json(result)
    if not result["pass"]:
        raise SystemExit(1)


def lint_prompt_result(text):
    # Every real Replit prompt in this engine must state these six concepts, but the exact
    # wording differs by source: compile-prompt.py's own output and the compact "gate stub"
    # fixture use literal headings ("## Scope", "## Mandatory HITL Gate", "## Final Report"),
    # while the canonical prose templates (REPLIT_TASK_TEMPLATE.md,
    # REPLIT_PHASED_IMPLEMENTATION_TEMPLATE.md) and hand/agent-authored prompts that
    # follow them use different section names ("Phase boundary", "HITL pause rule",
    # "Verify and report"). Each entry below accepts every phrasing actually used by a real
    # source in this engine, so a prompt is not marked broken just for following the templates.
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
    return {
        "pass": not missing and has_resume_language,
        "missing": missing,
        "emits_hitl_decision": emits_hitl_decision,
        "has_labeled_options": has_labeled_options,
        "has_resume_language": has_resume_language,
    }


def cmd_lint_prompt(argv):
    if not argv:
        usage("Usage: python3 tools/opsgate.py lint-prompt <prompt.md>")
    result = lint_prompt_result(Path(argv[0]).resolve().read_text(encoding="utf-8"))
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


def intake_request_result(text):
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
    return request


def cmd_intake_request(argv):
    text = " ".join(argv)
    if not text:
        usage('Usage: python3 tools/opsgate.py intake-request "<plain language request>"')
    print_json(intake_request_result(text))


def cmd_next_phase_prompt(argv):
    if len(argv) < 2:
        usage("Usage: python3 tools/opsgate.py next-phase-prompt <run-state.json> <parsed-report.json>")
    print(next_phase_prompt_text(load_data(argv[0]), load_data(argv[1])))


def next_phase_prompt_text(state, report):
    # Checked before looking at individual phase statuses or the report at all: a run's
    # top-level `blocked` status is the actual capability-gate outcome, and must not be
    # bypassable by a phase whose own status was (or could again be) mis-set to look runnable.
    if state.get("status") == "blocked":
        missing = state.get("missing_authority") or []
        lines = "\n".join(f"- {item}" for item in missing) or "- See the run state's missing_authority for detail."
        return f"# Phase Blocked\n\nDo not generate the next implementation prompt. This run's overall status is `blocked` - a capability gate has not been cleared, regardless of any individual phase or report status.\n\n## Missing Authority\n\n{lines}"
    next_phase = next((phase for phase in state.get("phases", []) if phase.get("status") in ["planned", "ready"]), None)
    if not next_phase:
        return "# No Next Phase\n\nNo planned or ready phase was found in the supplied run state."
    if not report.get("has_signal", True):
        return "# Report Not Recognized\n\nThe supplied report contained no recognizable outcome, check, blocker, or risk section. Do not generate the next implementation prompt from an unparseable report - request a report in the expected format before advancing."
    failed = [check for check in report.get("checks", []) if check.get("status") == "FAILED"]
    blockers = report.get("blockers") or []
    if failed or blockers:
        lines = [*(f"- FAILED: {check.get('text')}" for check in failed), *[f"- {item}" for item in blockers]]
        return f"# Phase Blocked\n\nDo not generate the next implementation prompt yet.\n\n## Blocking Evidence\n\n{chr(10).join(lines)}"
    not_run = [check for check in report.get("checks", []) if check.get("status") == "NOT RUN"]
    passed_count = len([check for check in report.get("checks", []) if check.get("status") == "PASSED"])
    verification = "\n".join(f"- {item}" for item in next_phase.get("verification_gate", [])) or "- Verify the phase outcome with risk-based checks."
    return f"""# Prompt for {next_phase.get("id")}

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

Resume from the next incomplete phase. Do not repeat completed discovery unless scoped drift is detected. Label checks PASSED, FAILED, or NOT RUN."""


_UNSAFE_RUN_ID_CHARS = re.compile(r"[^A-Za-z0-9_-]")

MAX_INIT_RUN_REQUEST_LENGTH = 50000  # generous for a real request's outcome/acceptance/scope
# fields, while bounding how much disk one opsgate_init_run call can write - unlike
# decisions.pylog (an intentionally unbounded append-only log), each run gets its own new
# directory with several files, so nothing here should be allowed to be arbitrarily large.


def init_run_result(request, tenant_id=None):
    """`tenant_id` scopes the run under `runs/<tenant_id>/` - without this, every tenant wrote
    into the same flat `runs/` namespace, so two tenants choosing (or colliding on) the same
    `request["id"]` would silently overwrite each other's run. Defaults to
    opsgate_tenants.LOCAL_DEV_TENANT_ID, matching every other tenant-aware *_result function."""
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    request_length = len(json.dumps(request))
    if request_length > MAX_INIT_RUN_REQUEST_LENGTH:
        raise ValueError(f"request must be at most {MAX_INIT_RUN_REQUEST_LENGTH} JSON-encoded characters, got {request_length}")
    route = route_request(request, tenant_id=tenant_id)
    run_id = request.get("id") or f"REQ-{int(_dt.datetime.now().timestamp() * 1000)}"
    # request["id"] is caller-controlled (including over the MCP server) and used as a runs/
    # directory name below - strip anything but a single safe path segment's worth of
    # characters so a value like "../../etc" can never resolve outside runs/. tenant_id is
    # already validated (a real registry key or the LOCAL_DEV_TENANT_ID constant) but gets the
    # same treatment here rather than trusting that invariant to hold at every call site.
    safe_run_id = _UNSAFE_RUN_ID_CHARS.sub("_", str(run_id))
    safe_tenant_id = _UNSAFE_RUN_ID_CHARS.sub("_", str(tenant_id))
    run_dir = ROOT_DIR / "runs" / safe_tenant_id / safe_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_python_data(run_dir / "request.py", "REQUEST", request, "# Engine run request")
    write_python_data(run_dir / "route.py", "ROUTE", route, "# Engine run route")
    write_python_data(run_dir / "gate_result.py", "GATE_RESULT", {"request_id": run_id, "status": "blocked" if route.get("blocked") else "pending_preflight", "failed_gates": ["capability_gate"] if route.get("blocked") else [], "missing_authority": route.get("missing_authority") or []}, "# Engine run gate result")
    write_python_data(run_dir / "handoff.py", "HANDOFF", {"request_id": run_id, "completed": False, "next_phase_ready": False, "blockers": route.get("missing_authority") or [] if route.get("blocked") else []}, "# Engine run handoff")
    result = {"run_id": run_id, "tenant_id": tenant_id, "run_dir": str(run_dir.relative_to(ROOT_DIR))}
    if safe_run_id != str(run_id):
        result["run_dir_id_sanitized"] = True
    return result


def cmd_init_run(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if not argv:
        usage("Usage: python3 tools/opsgate.py init-run <request.json> [--tenant <id>]")
    print_json(init_run_result(load_request(argv[0]), tenant_id=tenant_id))


MAX_DECISION_FIELD_LENGTH = 5000  # generous for "the smallest decision needed... exact scope"
# (replit.md's own phrasing for what a HITL answer should be) while bounding how much a single
# call can grow one tenant's decisions.pylog - there is no other size limit on this file, since
# it is an append-only audit log a tenant is expected to keep growing over real usage.

# Reuses the exact pattern HITL_SCHEMA already requires of a HITL id, rather than a second,
# independently-drifting regex - a decision log entry should require at least the same shape a
# real HITL decision object is validated against, not accept an arbitrary string as if it were
# a valid, attributable decision.
HITL_ID_PATTERN = re.compile(opsgate_contracts.HITL_SCHEMA["properties"]["id"]["pattern"])


def record_decision_result(hitl_id, answer, tenant_id=None):
    """`tenant_id` scopes which tenant's own `decisions.pylog` this gets appended to - without
    this, every tenant shared one global log with no attribution, so any caller could append a
    decision for a HITL-ID that looked like it belonged to a different tenant's task, with no
    record of who actually wrote it. Defaults to opsgate_tenants.LOCAL_DEV_TENANT_ID."""
    tenant_id = tenant_id or opsgate_tenants.LOCAL_DEV_TENANT_ID
    if len(str(hitl_id)) > MAX_DECISION_FIELD_LENGTH or len(str(answer)) > MAX_DECISION_FIELD_LENGTH:
        raise ValueError(f"hitl_id/answer must each be at most {MAX_DECISION_FIELD_LENGTH} characters")
    if not HITL_ID_PATTERN.match(str(hitl_id)):
        raise ValueError(f"hitl_id {hitl_id!r} does not match the required HITL id shape {HITL_ID_PATTERN.pattern!r}")
    safe_tenant_id = _UNSAFE_RUN_ID_CHARS.sub("_", str(tenant_id))
    entry = {"recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"), "id": hitl_id, "answer": answer, "tenant_id": tenant_id}
    decisions = ROOT_DIR / "runs" / safe_tenant_id / "decisions.pylog"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    with decisions.open("a", encoding="utf-8") as handle:
        handle.write(repr(entry) + "\n")
    return entry


def cmd_record_decision(argv):
    tenant_id, argv = _extract_tenant_flag(argv)
    if len(argv) < 2:
        usage("Usage: python3 tools/opsgate.py record-decision <HITL-ID> <answer and exact scope> [--tenant <id>]")
    print_json(record_decision_result(argv[0], " ".join(argv[1:]), tenant_id=tenant_id))


def cmd_validate_json(argv):
    if len(argv) < 2:
        usage("Usage: python3 tools/opsgate.py validate-json <schema-contract> <data-file>")
    schema = read_json(argv[0])
    data = load_data(argv[1])
    failures = validate_value(data.get("request") or data, schema, schema)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS {Path(argv[1]).relative_to(ROOT_DIR) if str(Path(argv[1])).startswith(str(ROOT_DIR)) else argv[1]} matches {argv[0]}")


COMMANDS = {
    "check-capabilities": cmd_check_capabilities,
    "check-paths": cmd_check_paths,
    "compile-prompt": cmd_compile_prompt,
    "init-run": cmd_init_run,
    "init-state": cmd_init_state,
    "intake-request": cmd_intake_request,
    "lint-prompt": cmd_lint_prompt,
    "lint-report": cmd_lint_report,
    "next-phase-prompt": cmd_next_phase_prompt,
    "parse-report": cmd_parse_report,
    "preflight": cmd_preflight,
    "record-decision": cmd_record_decision,
    "route-request": cmd_route_request,
    "show-profile": cmd_show_profile,
    "test-all": cmd_test_all,
    "validate-json": cmd_validate_json,
    "validate-engine": cmd_validate_engine,
}


def main():
    if len(sys.argv) < 2:
        usage(f"Usage: python3 tools/opsgate.py <{'|'.join(sorted(COMMANDS))}> [args...]")
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in COMMANDS:
        usage(f"Unknown command: {command}")
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
