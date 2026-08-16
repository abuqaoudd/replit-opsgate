#!/usr/bin/env python3
"""Scaffold a new profile for adopting this engine on a fresh Replit project - written
entirely OUTSIDE this engine's own repo, in the consuming project's own root, so a project
that drops this engine in as a submodule never has to commit its own profile config or business
facts into the engine's shared git history.

This is the direct, flags-only path for scripted/CI use. For the Agent-driven, plain-language
setup flow (a fill-in template instead of CLI flags), see tools/apply-setup.py and
canonical/references/replit.md's "First-run setup check" - that is the primary onboarding path
for a human setting up a new project; this tool is the lower-level primitive both it and any
future automation call into (see tools/opsgate_setup_lib.py).

Writes two things at --target-root (the outer project's own root, NOT anywhere inside this
engine):

  <target-root>/opsgate.profile.json   - profile + protected-path config; tools/opsgate_tools.py's
                                          read_json() merges this on top of the built-in
                                          metco/generic-replit profiles at runtime.
  <target-root>/ai/<profile>.md        - starter business file, structured like ai/metco.md,
                                          with a Business Facts section left as fill-in
                                          placeholders.

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
     up from the working directory tools are run from.
  3. Nothing in this engine's own repo needs to change or be rebuilt - the profile lives
     entirely in the outer project.
"""
import argparse
import sys

import opsgate_setup_lib as lib


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
    p.add_argument("--business-file", default=None, help="defaults to ai/<profile>.md, relative to --target-root")
    p.add_argument("--force", action="store_true", help="overwrite an existing business file at the target path")
    return p.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    lib.validate_profile_key(args.profile)
    if not args.frontend_root and not args.backend_root:
        print(
            "init-profile: warning - neither --frontend-root nor --backend-root was given; "
            "this profile will behave like generic-replit except for its own business file "
            "and any --extra-never-access paths.",
            file=sys.stderr,
        )

    target_root = lib.resolve_existing_target_root(args.target_root)
    entry = lib.build_entry(
        args.profile,
        frontend_root=args.frontend_root,
        backend_root=args.backend_root,
        description=args.description,
        extra_never_access=args.extra_never_access,
        business_file=args.business_file,
    )
    config_path, business_file_path = lib.write_profile(target_root, args.profile, entry, force=args.force)

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
