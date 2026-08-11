#!/usr/bin/env python3
"""Scaffold a new profile for adopting this engine on a fresh Replit project - written
entirely OUTSIDE this engine's own repo, in the consuming project's own root, so a project
that drops this kit in as a submodule never has to commit its own profile config or business
facts into the engine's shared git history.

Writes two things at --target-root (the outer project's own root, NOT anywhere inside this
engine):

  <target-root>/opsgate.profile.json   - profile + protected-path config; tools/opsgate_tools.py's
                                          read_json() merges this on top of the built-in
                                          metco/generic-replit profiles at runtime.
  <target-root>/ai/<profile>.md        - starter business file, structured like ai/metco.md,
                                          with a Business Facts section left as fill-in
                                          placeholders. This is exactly where the Replit
                                          installation step (canonical/README-v6.md) already
                                          expects a project's ai/**  files to live, so no
                                          copy step is needed for this file specifically.

This is additive only: it refuses to touch a profile key that already exists in
opsgate.profile.json (edit that file by hand instead), and refuses to overwrite an
existing business file unless --force.

Usage:
  python3 tools/init-profile.py --profile acme --target-root /path/to/outer-project \
      --frontend-root client/src --backend-root server/src
  python3 tools/init-profile.py --profile acme --target-root /path/to/outer-project \
      --frontend-root client/src --extra-never-access "legacy-service/**" --extra-never-access "vendor/**"

After running this:
  1. Fill in the generated business file's Business Facts section.
  2. Set OPSGATE_PROFILE=<profile> (Repl Secret is the usual place). OPSGATE_PROFILE_CONFIG
     only needs to be set explicitly if opsgate.profile.json is not discoverable by walking
     up from the working directory tools are run from (see external_profile_config_path()
     in tools/opsgate_tools.py for the exact resolution order).
  3. Nothing in this engine's own repo needs to change or be rebuilt - the profile lives
     entirely in the outer project.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROFILE_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
CONFIG_FILENAME = "opsgate.profile.json"

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
     ai/metco.md in the replit-opsgate engine repo is a filled-in example
     of the level of detail this section is meant to hold - it is only an
     example to look at, not something this project depends on. -->

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
    p.add_argument(
        "--target-root",
        default=None,
        help="the outer/consuming project's own root - NOT this engine's directory. "
        "If omitted, walks up from the current directory looking for an existing "
        "opsgate.profile.json, stopping at the first directory containing .git.",
    )
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
    p.add_argument("--business-file", default=None, help="defaults to ai/<profile>.md, relative to --target-root")
    p.add_argument("--force", action="store_true", help="overwrite an existing business file at the target path")
    return p.parse_args(argv)


def resolve_target_root(args):
    if args.target_root:
        root = Path(args.target_root).expanduser().resolve()
        if not root.is_dir():
            fail(f"--target-root {args.target_root!r} is not an existing directory.")
        return root
    # Skip the .git-based stop for the starting directory itself, same reasoning as
    # opsgate_tools.external_profile_config_path(): this engine's own directory almost
    # always has its own .git when used as a submodule, and that must not stop the walk
    # before it ever climbs into the outer project.
    start = Path.cwd()
    current = start
    for _ in range(12):
        if (current / CONFIG_FILENAME).exists():
            return current
        if current != start and (current / ".git").exists():
            fail(
                f"no {CONFIG_FILENAME} found by walking up from {Path.cwd()}, but reached a .git "
                f"root at {current} with none there either - pass --target-root explicitly "
                "(the outer project's own root, not this engine's directory)."
            )
        if current.parent == current:
            break
        current = current.parent
    fail(
        f"could not find an existing {CONFIG_FILENAME} by walking up from {Path.cwd()} - "
        "pass --target-root explicitly for a first-time setup."
    )


def load_config(config_path):
    if not config_path.exists():
        return {"profiles": {}}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{config_path} exists but is not valid JSON ({exc}) - fix it by hand first.")
    data.setdefault("profiles", {})
    return data


def build_entry(args):
    entry = {
        "description": args.description
        or f"{args.profile} Replit project profile. Select explicitly (OPSGATE_PROFILE={args.profile} or request.profile).",
        "business_file": args.business_file or f"ai/{args.profile}.md",
        "frontend_root": args.frontend_root,
        "backend_root": args.backend_root,
        "protected_policy": args.profile,
        "test_policy": args.test_policy,
        "distribution": args.distribution,
    }
    if args.extra_never_access:
        entry["extra_never_access"] = list(args.extra_never_access)
    return entry


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

    target_root = resolve_target_root(args)
    config_path = target_root / CONFIG_FILENAME
    config = load_config(config_path)

    if args.profile in config["profiles"]:
        fail(
            f"profile {args.profile!r} already exists in {config_path} - "
            "edit it by hand if you need to change it; this tool only adds new profiles."
        )

    entry = build_entry(args)
    business_file_path = target_root / entry["business_file"]
    if business_file_path.exists() and not args.force:
        fail(
            f"{business_file_path} already exists - pass --force to overwrite, "
            "or choose a different --business-file."
        )

    config["profiles"][args.profile] = entry
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    title = args.profile.replace("-", " ").replace("_", " ").title()
    business_file_path.parent.mkdir(parents=True, exist_ok=True)
    business_file_path.write_text(BUSINESS_FILE_TEMPLATE.format(title=title), encoding="utf-8")

    print(f"Added profile {args.profile!r} to {config_path}:")
    print(f"  frontend_root: {entry['frontend_root']!r}")
    print(f"  backend_root: {entry['backend_root']!r}")
    print(f"  business_file: {entry['business_file']!r}")
    print(f"  extra_never_access: {entry.get('extra_never_access', [])!r}")
    print(f"Generated starter business file: {business_file_path}")
    print()
    print("Next steps:")
    print("  1. Fill in the Business Facts section of the generated business file.")
    print(f"  2. Set OPSGATE_PROFILE={args.profile} (or pass \"profile\": \"{args.profile}\" on requests).")
    print(
        "  3. Nothing in this engine's own repo needs to change - tools/opsgate_tools.py's "
        f"read_json() picks up {config_path.name} automatically by walking up from wherever "
        "the tools are run, or via OPSGATE_PROFILE_CONFIG if that walk won't reach it."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
