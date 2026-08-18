"""Shared entry-building logic for a tenant's profile record.

Pure - no file I/O, no target-root coupling - which is exactly why opsgate_tenants.create_profile()
reuses it directly: this function only shapes the dict, and never needs to be caught for a
recoverable error the way file-writing code would.
"""


def build_entry(
    profile,
    frontend_root=None,
    backend_root=None,
    description=None,
    extra_never_access=None,
    business_file=None,
):
    entry = {
        "description": description
        or f"{profile} Replit project profile. Select explicitly (a --tenant flag or tenant token).",
        "business_file": business_file or f"ai/{profile}.md",
        "frontend_root": frontend_root,
        "backend_root": backend_root,
    }
    if extra_never_access:
        entry["extra_never_access"] = list(extra_never_access)
    return entry
