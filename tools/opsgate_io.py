"""Generic file I/O, fixture/data loading, and small shared CLI helpers.

Split out of opsgate.py (relocation, not a rewrite - every function body below is
unchanged from where it used to live). Nothing here knows about profiles, routing, or prompt
content; it's the low-level layer everything else is built on.
"""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import opsgate_fixtures

ROOT_DIR = Path(__file__).resolve().parent.parent


def read_text(relative_path):
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def write_text(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def write_python_data(path, variable_name, value, header):
    import pprint

    body = f"{header}\n\n{variable_name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n"
    write_text(path, body)


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


def print_json(value):
    print(json.dumps(value, indent=2))


def usage(message):
    print(message, file=sys.stderr)
    raise SystemExit(2)


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
    if normalized in ["gold:bounded-frontend-request", "bounded-frontend-request"]:
        return copy.deepcopy(opsgate_fixtures.GOLD_STANDARD_BOUNDED_FRONTEND_REQUEST)
    if normalized in ["gold:phased-migration-request", "phased-migration-request"]:
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


def capture_python(command, args):
    return subprocess.check_output([sys.executable, str(ROOT_DIR / "tools" / "opsgate.py"), command, *args], cwd=ROOT_DIR, text=True)


def run_python(command, args, expect=None):
    completed = subprocess.run([sys.executable, str(ROOT_DIR / "tools" / "opsgate.py"), command, *args], cwd=ROOT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if expect is not None and completed.returncode != expect:
        raise RuntimeError(completed.stderr or completed.stdout)
    if expect is None and completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return completed
