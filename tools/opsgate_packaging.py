"""Distribution packaging, upgrade diffing, and engine-alignment auditing.

Split out of opsgate.py (relocation, not a rewrite). These are the engine-maintenance
commands - build-distributions, build-replit-install, diff-upgrade, release-notes, audit-engine
- run by hand inside this repo, never called mid-task by a live agent (they're deliberately
excluded from the MCP tool surface, see mcp-server/opsgate_mcp_server.py).
"""
import datetime as _dt
import json
import re
import shutil
import zipfile
from pathlib import Path

from opsgate_io import ROOT_DIR, capture_python, copy_recursive, list_files, print_json, sha256, usage, write_python_data, write_text, same_bytes
from opsgate_profiles import read_json


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
        usage("Usage: python3 tools/opsgate.py diff-upgrade <old-engine-root> [new-engine-root]")
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
    if not argv:
        usage("Usage: python3 tools/opsgate.py release-notes <old-engine-root>")
    diff = json.loads(capture_python("diff-upgrade", [argv[0], "canonical"]))
    changed = "\n".join(f"- {item}" for item in diff["changed"]) or "- None"
    added_engine = "\n".join(f"- {item}" for item in [item for item in diff["added"] if "ENGINE" in item or "gold-standard" in item or "claude-skills" in item][:40]) or "- None detected"
    print(f"""# Engine Release Notes

Generated from upgrade diff.

## Summary

- Added files: {len(diff["added"])}
- Changed files: {len(diff["changed"])}
- Removed or relocated files: {len(diff["removed"])}

## Reinstall Guidance

- Rebuild Claude distribution when project instructions, templates, references, specifications, or Claude skill sources changed.
- Reinstall Replit distribution when `references/replit.md`, `references/ai/**`, or `references/replit-skills/**` changed.
- Run `python3 tools/opsgate.py validate-engine` before release.

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
    check("tools exist", (ROOT_DIR / "tools/opsgate.py").exists(), "<engine-dir>/tools/opsgate.py")
    result = {"project_root": str(project_root), "checks": checks, "pass": not any(item["status"] == "FAILED" for item in checks)}
    print_json(result)
    if not result["pass"]:
        raise SystemExit(1)
