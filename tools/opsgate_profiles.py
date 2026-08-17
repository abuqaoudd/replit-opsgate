"""Protected-path matching, plus the generic Python-contract/manifest reader.

Every profile this engine resolves - by tenant ID, via opsgate_tenants.py - is resolved there;
this module has no profile-resolution concern of its own.
"""
import copy
import json
import re
from pathlib import Path

import opsgate_contracts

ROOT_DIR = Path(__file__).resolve().parent.parent


def read_json(relative_path):
    if relative_path in opsgate_contracts.CONTRACTS:
        return copy.deepcopy(opsgate_contracts.CONTRACTS[relative_path])
    with (ROOT_DIR / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_pattern(pattern):
    return re.sub(r"\*\*/?", "", str(pattern)).replace("*", "")


def matches_protected(candidate, protected_pattern):
    needle = normalize_pattern(protected_pattern).rstrip("/")
    return candidate == needle or candidate.startswith(f"{needle}/") or f"/{needle}/" in candidate or needle in candidate
