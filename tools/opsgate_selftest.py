"""The two release-gate self-test commands: validate-engine and test-all.

Split out of opsgate_tools.py (relocation, not a rewrite). Kept together, separate from the
ordinary command implementations, because both exist purely to exercise every other command
against every fixture - they are meta relative to everything else in this engine, not command
implementations themselves.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import opsgate_contracts
import opsgate_fixtures
from opsgate_io import ROOT_DIR, capture_python, exists, list_files, read_text, run_python, same_bytes
from opsgate_profiles import read_json
from opsgate_routing import parse_skill_frontmatter, route_request


def cmd_validate_engine(argv):
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
        # The Mandatory HITL Gate and Per-Action Gate are defined once, authoritatively, in
        # replit.md (see canonical/README-v6.md) - skills are not required to restate that
        # reminder in their own words; every skill's step 1 pointing back to replit.md is
        # what actually keeps them honoring it.
        if "replit.md" not in text:
            fail(f"Skill does not reference replit.md as authority: {relative}")
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
        run_python("validate-json", ["manifests/run-state.schema.json", "state:ready-phased-state"])
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
    # Self-diff (canonical against itself) rather than a personal-machine sibling directory
    # that will never exist on a fresh checkout - relative_map() fails soft on a missing
    # directory, so the old default silently produced a meaningless "everything added" diff
    # that still passed this check regardless. Self-diffing makes the assertion meaningful:
    # a real self-diff must report zero drift, same pattern test-all.py already uses.
    diff = json.loads(capture_python("diff-upgrade", ["canonical", "canonical"]))
    if "classification" not in diff:
        fail("Upgrade diff did not include classification.")
    if diff["added"] or diff["changed"] or diff["removed"]:
        fail("diff-upgrade self-diff (canonical against itself) reported unexpected changes.")
    for warning in warnings:
        print(f"WARN {warning}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS validation complete ({len(warnings)} warnings).")


def cmd_test_all(argv):
    """Single entrypoint that exercises every tool in the engine against every fixture.

    Broader than validate-engine: validate-engine spot-checks one or two fixtures per command as
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

    # 1. Build the engine, then run the existing validator. validate-engine already covers Python
    #    contract shape, protected-path presence, HITL wording, skill frontmatter, the full
    #    canonical<->distribution drift check, forbidden template fields, zip integrity, the
    #    routing/HITL fixtures, one compiled-prompt spot check, and the negative lint fixtures.
    try_run("build-distributions", "build-distributions", [])
    validate_out = try_run("validate-engine", "validate-engine", [])
    if validate_out and not validate_out.strip().startswith("PASS"):
        record("validate-engine reported failures", False, validate_out.strip()[:300])
    try_run("build-replit-install", "build-replit-install", [])

    # 2. Exercise every routing fixture end to end, not just the one or two validate-engine
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

    # 3. Every HITL fixture must validate against the HITL schema, and the ready-phased-state
    #    fixture must validate against the run-state schema (previously declared, never checked).
    for fixture in opsgate_fixtures.HITL_FIXTURES:
        try_run(f"validate-json (hitl) {fixture['path']}", "validate-json", ["manifests/hitl.schema.json", fixture["path"]])
    try_run("validate-json (run-state) state:ready-phased-state", "validate-json", ["manifests/run-state.schema.json", "state:ready-phased-state"])

    # 4. Positive and negative report/prompt lint fixtures.
    try_run("parse-report sample", "parse-report", ["fixtures/reports/sample-replit-final-report.md"])
    try_run("lint-report valid fixture", "lint-report", ["fixtures/reports/sample-replit-final-report.md"])
    try_run("lint-report invalid fixture (expect fail)", "lint-report", ["fixtures/reports/invalid-weak-hitl-report.md"], expect_exit=1)
    try_run("lint-prompt valid fixture", "lint-prompt", ["fixtures/prompts/frontend-compiled-with-gate.md"])
    try_run("lint-prompt invalid fixture (expect fail)", "lint-prompt", ["fixtures/prompts/invalid-missing-hitl-options.md"], expect_exit=1)

    # 5. Self-diff: canonical compared against itself must report zero drift, proving the
    #    upgrade-diff tool itself is trustworthy before it's ever pointed at a real old engine checkout.
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
    print("PASS test-all: full engine exercised cleanly.")
