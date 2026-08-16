"""Structural validation helpers: markdown report/prompt parsing and a lightweight JSON-Schema
subset validator.

Split out of opsgate_tools.py (relocation, not a rewrite). Everything here answers "does this
document/data have the shape it's required to have" - used by the lint-report, lint-prompt,
and validate-json commands.
"""
import re


def extract_section(source, heading):
    pattern = re.compile(rf"(^|\n)#+\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n#+\s+|$)", re.I)
    match = pattern.search(source)
    return match.group(2).strip() if match else ""


def parse_markdown_table(section):
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|") and not re.match(r"^\|\s*-+", line):
            rows.append([cell.strip() for cell in line[1:-1].split("|")])
    return rows


def is_placeholder(value):
    return (not value) or value == "-" or value == "NA" or re.search(r"\[[^\]]+\]", value) or re.search(r"evidence\s*(here|checked|needed|tbd|todo)?", value, re.I)


REQUIRED_GATE_ROWS = [
    "Is the exact owner/path known?",
    "Is the write scope explicitly authorized?",
    "Are protected paths excluded?",
    "Are package/config/schema/seed/destructive changes needed?",
    "If risky changes are needed, are they explicitly authorized?",
    "Are there two materially valid implementation choices?",
    "Would proceeding require inventing a business rule, permission rule, data rule, or API contract?",
    "Is verification possible in a safe environment?",
]


def validate_value(value, spec, schema, pointer="$", failures=None):
    failures = failures if failures is not None else []
    if not spec:
        return failures
    if "$ref" in spec:
        ref = spec["$ref"]
        if ref.startswith("#/$defs/"):
            spec = schema.get("$defs", {}).get(ref[len("#/$defs/"):], {})
    expected_type = spec.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            failures.append(f"{pointer} must be object")
            return failures
        for required in spec.get("required", []):
            if required not in value:
                failures.append(f"{pointer}.{required} is required")
        for key, child in spec.get("properties", {}).items():
            if key in value:
                validate_value(value[key], child, schema, f"{pointer}.{key}", failures)
    elif expected_type == "array":
        if not isinstance(value, list):
            failures.append(f"{pointer} must be array")
            return failures
        if "minItems" in spec and len(value) < spec["minItems"]:
            failures.append(f"{pointer} must have at least {spec['minItems']} items")
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            failures.append(f"{pointer} must have at most {spec['maxItems']} items")
        for index, item in enumerate(value):
            validate_value(item, spec.get("items", {}), schema, f"{pointer}[{index}]", failures)
    elif expected_type == "string":
        if not isinstance(value, str):
            failures.append(f"{pointer} must be string")
        else:
            if "minLength" in spec and len(value) < spec["minLength"]:
                failures.append(f"{pointer} is too short")
            if "pattern" in spec and not re.search(spec["pattern"], value):
                failures.append(f"{pointer} does not match {spec['pattern']}")
            if "enum" in spec and value not in spec["enum"]:
                failures.append(f"{pointer} must be one of {', '.join(spec['enum'])}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            failures.append(f"{pointer} must be integer")
        elif "enum" in spec and value not in spec["enum"]:
            failures.append(f"{pointer} must be one of {', '.join(map(str, spec['enum']))}")
    elif expected_type == "boolean" and not isinstance(value, bool):
        failures.append(f"{pointer} must be boolean")
    return failures
