"""Shared logic for writing a project's external profile config + business file, used by both
tools/init-profile.py (direct CLI flags, for scripted/CI use) and tools/apply-setup.py (parses a
filled-in PROJECT_SETUP_TEMPLATE.md, for the Agent-driven first-run setup flow described in
canonical/references/replit.md). Kept in one place so both tools write the exact same
opsgate.profile.json shape that tools/opsgate_tools.py's load_external_profile_config() expects,
and the exact same business-file structure ai/metco.md follows.

Nothing here ever writes inside this engine's own directory - every function takes an explicit
target_root and writes only under it.
"""
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

{business_facts_block}

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

DEFAULT_BUSINESS_FACTS_BLOCK = '''<!-- FILL IN: replace this section with the project's real domain facts -
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
- Known drift to watch for: [anything the docs say that code no longer does].'''


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def validate_profile_key(profile):
    if not PROFILE_KEY_RE.match(profile):
        fail(
            f"profile key {profile!r} must be lowercase letters/digits, hyphen-separated "
            "(e.g. acme, my-project) - matching the existing metco / generic-replit convention."
        )


def resolve_existing_target_root(explicit_target_root):
    """Find the outer project's root for a call that expects opsgate.profile.json to already
    exist (a second+ profile, or any apply-setup.py run after the first). Skips the .git-based
    stop at the starting directory itself, same reasoning as opsgate_tools.py's
    external_profile_config_path() - the engine's own directory almost always has its own .git
    when used as a submodule, and that must not block the walk from reaching the outer project."""
    if explicit_target_root:
        root = Path(explicit_target_root).expanduser().resolve()
        if not root.is_dir():
            fail(f"--target-root {explicit_target_root!r} is not an existing directory.")
        return root
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


def build_entry(
    profile,
    frontend_root=None,
    backend_root=None,
    description=None,
    extra_never_access=None,
    test_policy="risk_based_existing_scripts_only",
    distribution="replit",
    business_file=None,
):
    entry = {
        "description": description
        or f"{profile} Replit project profile. Select explicitly (OPSGATE_PROFILE={profile} or request.profile).",
        "business_file": business_file or f"ai/{profile}.md",
        "frontend_root": frontend_root,
        "backend_root": backend_root,
        "protected_policy": profile,
        "test_policy": test_policy,
        "distribution": distribution,
    }
    if extra_never_access:
        entry["extra_never_access"] = list(extra_never_access)
    return entry


def write_profile(target_root, profile, entry, business_facts_block=None, force=False):
    """Write `entry` into <target_root>/opsgate.profile.json under `profile`, and generate its
    business file at <target_root>/<entry['business_file']>. Refuses to touch an existing
    profile key (edit that file by hand instead); refuses to overwrite an existing business
    file unless force=True. Returns (config_path, business_file_path)."""
    config_path = target_root / CONFIG_FILENAME
    config = load_config(config_path)
    if profile in config["profiles"]:
        fail(
            f"profile {profile!r} already exists in {config_path} - "
            "edit it by hand if you need to change it; this tool only adds new profiles."
        )
    business_file_path = target_root / entry["business_file"]
    if business_file_path.exists() and not force:
        fail(
            f"{business_file_path} already exists - pass --force to overwrite, "
            "or choose a different business_file."
        )

    config["profiles"][profile] = entry
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    title = profile.replace("-", " ").replace("_", " ").title()
    business_file_path.parent.mkdir(parents=True, exist_ok=True)
    business_file_path.write_text(
        BUSINESS_FILE_TEMPLATE.format(
            title=title, business_facts_block=business_facts_block or DEFAULT_BUSINESS_FACTS_BLOCK
        ),
        encoding="utf-8",
    )
    return config_path, business_file_path
