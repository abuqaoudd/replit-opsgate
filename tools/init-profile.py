#!/usr/bin/env python3
"""Scaffold a new profile for adopting this engine on a fresh Replit project.

Automates the manual steps described in canonical/README-v6.md "Adopting
this kit in a different Replit project": it appends one profile entry to
PROFILES and PROTECTED_PATHS in opsgate_contracts.py, and generates a
starter business file (default: canonical/references/ai/<profile>.md), so
onboarding a new project does not require hand-editing Python contracts
from a blank page.

This is additive only. It refuses to touch a profile key that already
exists in opsgate_contracts.py - editing an existing profile is a manual
edit, not something this tool will surgically rewrite. --force only
controls whether an already-existing business file may be overwritten.

Usage:
  python3 tools/init-profile.py --profile acme --frontend-root client/src --backend-root server/src
  python3 tools/init-profile.py --profile acme --frontend-root client/src \
      --extra-never-access "legacy-service/**" --extra-never-access "vendor/**"

After running this, rebuild and validate:
  python3 tools/build-distributions.py && python3 tools/validate-kit.py
Then fill in the generated business file's Business Facts section, and set
OPSGATE_PROFILE=<profile> (or pass "profile" on requests) to select it.
"""
import argparse
import re
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_PATH = ROOT / "tools" / "opsgate_contracts.py"

PROFILE_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

import ast


def _pos_to_index(source, lineno, col_offset):
    """Convert a 1-indexed (lineno, col_offset) ast position into a flat
    string index into `source`."""
    lines = source.splitlines(keepends=True)
    return sum(len(l) for l in lines[: lineno - 1]) + col_offset


def _find_profiles_dict_end(source, top_level_name):
    """Return the flat string index right after the last existing entry in
    <top_level_name>['profiles'], via AST rather than a brittle text anchor -
    this keeps working no matter how many profiles have already been added
    by earlier runs of this tool, not just the original two."""
    tree = ast.parse(source)
    for node in tree.body:
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == top_level_name
        ):
            continue
        top_dict = node.value
        if not isinstance(top_dict, ast.Dict):
            continue
        for key_node, value_node in zip(top_dict.keys, top_dict.values):
            if isinstance(key_node, ast.Constant) and key_node.value == "profiles":
                inner_dict = value_node
                if not isinstance(inner_dict, ast.Dict) or not inner_dict.values:
                    fail(f"{top_level_name}['profiles'] is empty or not a dict literal - add the profile by hand instead.")
                last_value = inner_dict.values[-1]
                return _pos_to_index(source, last_value.end_lineno, last_value.end_col_offset)
    fail(
        f"could not locate {top_level_name}['profiles'] via AST in opsgate_contracts.py - "
        "has the file structure changed materially? Add the profile by hand instead."
    )


def _profile_already_exists(source, profile):
    tree = ast.parse(source)
    for node in tree.body:
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in ("PROFILES", "PROTECTED_PATHS")
        ):
            continue
        top_dict = node.value
        if not isinstance(top_dict, ast.Dict):
            continue
        for key_node, value_node in zip(top_dict.keys, top_dict.values):
            if isinstance(key_node, ast.Constant) and key_node.value == "profiles":
                inner_dict = value_node
                if isinstance(inner_dict, ast.Dict):
                    for k in inner_dict.keys:
                        if isinstance(k, ast.Constant) and k.value == profile:
                            return True
    return False

BUSINESS_FILE_TEMPLATE = '''# {title} Task Control Instruction Object

Read for every task. `replit.md` remains authoritative.

## Responsibility

Own the cross-project task record for **{title}**: outcome, scope, selected
instruction objects, authority, ownership, pre-existing work, verification
plan, evidence, final reporting, and scope compliance. Also own this
project's business ground truth below, so domain facts are grounded instead
of re-derived or invented on every task.

## Activation

Use this object for every task before any other domain object. It
coordinates loaded instructions but does not override `replit.md`,
capability gates, protected paths, or explicit user scope.

## Inputs

- User outcome, acceptance criteria, allowed write/read scope, preserved
  behavior, and explicit authorizations.
- Automatically selected internal mode, primary skill, relevant domain
  instruction objects, and current run/phase state.
- Current project evidence, owners, consumers, tests, pre-existing changes,
  and stop conditions.
- The Business Facts below, used as ground truth unless current code
  evidence proves drift.

## Business Facts (ground truth reference)

<!-- FILL IN: replace this section with the project's real domain facts -
     roles/permissions, lifecycle/state machines, ID formats, key business
     rules, design-system conventions, and any known drift to watch for.
     See canonical/references/ai/metco.md in this kit for a filled-in
     example of the level of detail this section is meant to hold. -->

- Source: [BRD / spec document and date, or "none yet - fill in as decisions are made"].
- Roles: [list roles and what each owns / cannot do].
- Lifecycle: [entity state machines, if any].
- ID formats: [any standardized identifier formats].
- Key business rules: [non-exhaustive list; escalate rather than invent].
- Design system: [visual/UX conventions worth restating for every task].
- Known drift to watch for: [anything the docs say that code no longer does].

## Must Not

- Ask the user to choose internal modes, skills, complexity labels, or
  execution profiles.
- Treat selected mode, selected skill, loaded object, or recommendation as
  authority.
- Invent business rules, permissions, data rules, API contracts, owners,
  dates, or acceptance evidence not covered by the Business Facts above or
  by direct current-code evidence.
- Silently override a Business Fact above with an assumption; if current
  code evidence conflicts with a fact above, trust the code, and report the
  drift explicitly.
- Expand scope, touch protected paths, or perform destructive work without
  explicit authorization.

## Start record

Before edits record:

- outcome and observable acceptance criteria;
- automatically selected internal mode, primary skill, and routing
  evidence;
- approved writes and minimum reads;
- protected/locked categories and stop conditions;
- owning entry point, current behavior, consumers, tests, and expected
  files;
- relevant instructions/skill;
- verification plan and known pre-existing changes;
- any Business Fact above that current code evidence contradicts.

Use the narrowest safe interpretation. Ask only when ambiguity changes
security, data integrity, public contracts, or destructive behavior.

## Workflow

1. Record outcome, acceptance criteria, selected mode/skill/object set,
   approved scope, locked categories, and stop conditions.
2. Identify owner, current behavior, direct consumers, pre-existing
   changes, and relevant checks before editing.
3. Cross-check current behavior against the Business Facts above; note any
   drift instead of silently trusting either source.
4. Apply the narrowest safe interpretation and selected object budgets.
5. Coordinate cross-artifact work in the correct order while preserving
   contracts and evidence.
6. Report changed files, decisions, checks, limitations, residual risk,
   scope compliance, and any Business Fact drift found.

## Output Evidence

Final output must identify changed files, behavior, ownership and reuse
decisions, new-unit justification, exact checks/results, pre-existing work
preserved, limitations, remaining risk, scope compliance, and any drift
found between this file's Business Facts and current code. Limited checks
never prove whole-project correctness.
'''


def fail(message):
    print(f"init-profile: {message}", file=sys.stderr)
    sys.exit(1)


def parse_args(argv):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--profile", required=True, help="profile key, e.g. acme (lowercase, hyphen-separated)")
    p.add_argument("--frontend-root", default=None, help="normal write path for frontend source, e.g. client/src")
    p.add_argument("--backend-root", default=None, help="normal write path for backend source, e.g. server/src")
    p.add_argument("--description", default=None, help="human-readable profile description")
    p.add_argument(
        "--extra-never-access",
        action="append",
        default=[],
        help="repeatable; extra never_access glob on top of the universal baseline",
    )
    p.add_argument("--test-policy", default="risk_based_existing_scripts_only")
    p.add_argument("--distribution", default="replit")
    p.add_argument("--business-file", default=None, help="defaults to ai/<profile>.md")
    p.add_argument("--force", action="store_true", help="overwrite an existing business file at the target path")
    return p.parse_args(argv)


def build_profiles_entry(args):
    desc = args.description or (
        f"{args.profile} Replit project profile. Select explicitly "
        f"(OPSGATE_PROFILE={args.profile} or request.profile)."
    )
    business_file = args.business_file or f"ai/{args.profile}.md"
    lines = [
        f"              {args.profile!r}: {{'description': {desc!r},",
        f"                                 'business_file': {business_file!r},",
        f"                                 'frontend_root': {args.frontend_root!r},",
        f"                                 'backend_root': {args.backend_root!r},",
        f"                                 'protected_policy': {args.profile!r},",
        f"                                 'test_policy': {args.test_policy!r},",
        f"                                 'distribution': {args.distribution!r}}}",
    ]
    return "\n".join(lines)


def build_protected_paths_entry(args):
    write_paths = [p for p in (args.frontend_root, args.backend_root) if p]
    normal_write_paths = [f"{p.rstrip('/')}/**" for p in write_paths]
    lines = [f"                    {args.profile!r}: {{'normal_write_paths': {normal_write_paths!r},"]
    if args.extra_never_access:
        extra = ", ".join(repr(p) for p in args.extra_never_access)
        lines.append(f"                        'never_access': [*_UNIVERSAL_NEVER_ACCESS, {extra}],")
    else:
        lines.append("                        'never_access': list(_UNIVERSAL_NEVER_ACCESS),")
    lines.append("                        'locked_by_default': list(_UNIVERSAL_LOCKED_BY_DEFAULT)}")
    return "\n".join(lines)


def insert_profile(source, args):
    profiles_at = _find_profiles_dict_end(source, "PROFILES")
    source = source[:profiles_at] + ",\n" + build_profiles_entry(args) + source[profiles_at:]

    protected_at = _find_profiles_dict_end(source, "PROTECTED_PATHS")
    source = source[:protected_at] + ",\n" + build_protected_paths_entry(args) + source[protected_at:]
    return source


def verify_new_source(new_source, profile):
    """Write the candidate source to a throwaway module and import it, to prove
    the new profile actually resolves through PROFILES/PROTECTED_PATHS before
    the real file is touched - textual insertion is only trusted once it is
    also proven to import and behave correctly."""
    import ast

    try:
        ast.parse(new_source)
    except SyntaxError as exc:
        fail(f"generated opsgate_contracts.py would not parse ({exc}) - no files were changed.")

    tmp_path = ROOT / "tools" / "_init_profile_verify_tmp.py"
    tmp_path.write_text(new_source)
    try:
        spec = importlib.util.spec_from_file_location("_init_profile_verify_tmp", tmp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if profile not in module.PROFILES["profiles"]:
            fail("new profile did not appear in PROFILES after insertion - aborting, no files changed.")
        if profile not in module.PROTECTED_PATHS["profiles"]:
            fail("new profile did not appear in PROTECTED_PATHS after insertion - aborting, no files changed.")
        return module.PROFILES["profiles"][profile], module.PROTECTED_PATHS["profiles"][profile]
    finally:
        try:
            tmp_path.write_text("# verification scratch file, safe to ignore\n")
        except OSError:
            pass


def main(argv):
    args = parse_args(argv)

    if not PROFILE_KEY_RE.match(args.profile):
        fail(
            f"--profile {args.profile!r} must be lowercase letters/digits, hyphen-separated "
            "(e.g. acme, my-project) - matching the existing metco / generic-replit convention."
        )
    if not args.frontend_root and not args.backend_root:
        print(
            "init-profile: warning - neither --frontend-root nor --backend-root was given; "
            "this profile will behave like generic-replit except for its own business file "
            "and any --extra-never-access paths.",
            file=sys.stderr,
        )

    source = CONTRACTS_PATH.read_text()
    if _profile_already_exists(source, args.profile):
        fail(
            f"profile {args.profile!r} already exists in {CONTRACTS_PATH.relative_to(ROOT)} - "
            "edit it by hand if you need to change it; this tool only adds new profiles."
        )

    new_source = insert_profile(source, args)
    resolved_profile, resolved_protected = verify_new_source(new_source, args.profile)

    business_file_rel = resolved_profile["business_file"]
    business_file_path = ROOT / "canonical" / "references" / business_file_rel
    if business_file_path.exists() and not args.force:
        fail(
            f"{business_file_path.relative_to(ROOT)} already exists - pass --force to overwrite, "
            "or choose a different --business-file."
        )

    CONTRACTS_PATH.write_text(new_source)

    title = args.profile.replace("-", " ").replace("_", " ").title()
    business_file_path.parent.mkdir(parents=True, exist_ok=True)
    business_file_path.write_text(BUSINESS_FILE_TEMPLATE.format(title=title))

    verify_tmp = ROOT / "tools" / "_init_profile_verify_tmp.py"
    if verify_tmp.exists():
        try:
            verify_tmp.write_text("# verification scratch file, safe to ignore\n")
        except OSError:
            pass

    print(f"Added profile {args.profile!r} to {CONTRACTS_PATH.relative_to(ROOT)}:")
    print(f"  frontend_root: {resolved_profile['frontend_root']!r}")
    print(f"  backend_root: {resolved_profile['backend_root']!r}")
    print(f"  business_file: {resolved_profile['business_file']!r}")
    print(f"  normal_write_paths: {resolved_protected['normal_write_paths']!r}")
    if args.extra_never_access:
        print(f"  never_access: universal baseline + {args.extra_never_access!r}")
    else:
        print("  never_access: universal baseline only")
    print(f"Generated starter business file: {business_file_path.relative_to(ROOT)}")
    print()
    print("Next steps:")
    print("  1. Fill in the Business Facts section of the generated business file.")
    print("  2. python3 tools/build-distributions.py && python3 tools/validate-kit.py")
    print(f"  3. Set OPSGATE_PROFILE={args.profile} (or pass \"profile\": \"{args.profile}\" on requests) to select it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
