#!/usr/bin/env python3
"""Verifies opsgate_knowledge.py's extracted text against its canonical source files,
line-by-line where it claims to be verbatim, and section-by-section where it claims to drop
only scaffolding.

Run: python3 tools/test_opsgate_knowledge.py
"""
import re
import sys

import opsgate_knowledge as knowledge

RESULTS = []


def record(name, passed, detail=""):
    RESULTS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}" + (f" - {detail}" if detail and not passed else ""))


def main():
    hitl_source = knowledge.HITL_SPEC_PATH.read_text(encoding="utf-8").strip()
    hitl_out = knowledge.hitl_protocol_text()
    record("hitl_protocol_text is byte-identical to HITL_SPEC.md", hitl_out == hitl_source)

    security_source = knowledge.SECURITY_RULES_PATH.read_text(encoding="utf-8")
    security_out = knowledge.security_rules_text()

    record(
        "security_rules_text keeps the H1 title",
        security_out.startswith("# Security Instruction Object"),
    )
    record(
        "security_rules_text drops the Activation heading",
        not re.search(r"^##\s+Activation\s*$", security_out, re.M),
    )
    record(
        "security_rules_text drops the one-line pre-section summary",
        "Read for authentication, authorization" not in security_out,
    )

    durable_headings = ["Responsibility", "Inputs", "Must Not", "Rules", "Workflow", "Output Evidence"]
    for heading in durable_headings:
        source_section = re.search(rf"^##\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n##\s+|\Z)", security_source, re.M)
        out_section = re.search(rf"^##\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n##\s+|\Z)", security_out, re.M)
        record(
            f"security_rules_text section '{heading}' is byte-identical to source",
            bool(source_section and out_section and source_section.group(1).strip() == out_section.group(1).strip()),
        )

    skill_names = knowledge.list_skill_names()
    record("list_skill_names finds all 14 replit-skills", len(skill_names) == 14, f"found {len(skill_names)}")

    for skill in skill_names:
        source_text = knowledge._skill_path(skill).read_text(encoding="utf-8")
        source_body = source_text.split("---", 2)[2].strip()
        source_title, source_mode_sentence, source_steps, source_closing = [p.strip() for p in source_body.split("\n\n") if p.strip()]
        out = knowledge.skill_workflow_text(skill)

        record(f"{skill}: workflow keeps the H1 title", out.startswith(source_title))
        record(f"{skill}: workflow drops the mode-select sentence", source_mode_sentence not in out)
        record(f"{skill}: workflow drops step 1 (reference-reading)", source_steps.splitlines()[0] not in out)
        record(f"{skill}: workflow keeps the closing stop/never constraint verbatim", out.rstrip().endswith(source_closing))

        source_step_bodies = [re.sub(r"^\d+\.\s*", "", line) for line in source_steps.splitlines()[1:]]
        out_step_lines = [line for line in out.splitlines() if re.match(r"^\d+\.", line)]
        out_step_bodies = [re.sub(r"^\d+\.\s*", "", line) for line in out_step_lines]
        record(
            f"{skill}: remaining step text is byte-identical to source, renumbered from 1",
            out_step_bodies == source_step_bodies,
        )

    unknown_raised = False
    try:
        knowledge.skill_workflow_text("not-a-real-skill")
    except knowledge.UnknownSkillError:
        unknown_raised = True
    record("skill_workflow_text raises UnknownSkillError for an unknown skill", unknown_raised)

    common_headings = ["Responsibility", "Inputs", "Must Not", "Workflow", "Output Evidence"]
    for name in knowledge.INSTRUCTION_OBJECT_NAMES:
        source_text = knowledge._instruction_object_path(name).read_text(encoding="utf-8")
        title_block, _sections = knowledge._split_sections(source_text)
        title_lines = title_block.strip().splitlines()
        h1, summary = title_lines[0], "\n".join(title_lines[1:]).strip()
        out = knowledge.instruction_object_text(name)

        record(f"instruction_object_text({name!r}) keeps the H1 title", out.startswith(h1))
        record(f"instruction_object_text({name!r}) drops the Activation heading", not re.search(r"^##\s+Activation\s*$", out, re.M))
        if name in knowledge.KEEP_SUMMARY_LINE_FOR:
            record(f"instruction_object_text({name!r}) keeps its verified non-redundant summary line", bool(summary) and summary in out)
        else:
            record(f"instruction_object_text({name!r}) drops its redundant summary line", bool(summary) and summary not in out)

        for heading in common_headings:
            source_section = re.search(rf"^##\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n##\s+|\Z)", source_text, re.M)
            out_section = re.search(rf"^##\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n##\s+|\Z)", out, re.M)
            record(
                f"instruction_object_text({name!r}) section '{heading}' is byte-identical to source",
                bool(source_section and out_section and source_section.group(1).strip() == out_section.group(1).strip()),
            )

    unknown_object_raised = False
    try:
        knowledge.instruction_object_text("not-a-real-object")
    except knowledge.UnknownInstructionObjectError:
        unknown_object_raised = True
    record("instruction_object_text raises UnknownInstructionObjectError for an unknown name", unknown_object_raised)

    ruleset = knowledge.export_ruleset()
    record("export_ruleset includes hitl_protocol", ruleset.get("hitl_protocol") == hitl_out)
    record("export_ruleset includes security_rules", ruleset.get("security_rules") == security_out)
    record(
        "export_ruleset includes every skill workflow",
        ruleset.get("skill_workflows") == {skill: knowledge.skill_workflow_text(skill) for skill in skill_names},
    )
    record(
        "export_ruleset includes every instruction object",
        ruleset.get("instruction_objects") == {name: knowledge.instruction_object_text(name) for name in knowledge.INSTRUCTION_OBJECT_NAMES},
    )
    record(
        "export_ruleset records the real source paths",
        ruleset.get("sources") == {
            "hitl_protocol": "content/specifications/HITL_SPEC.md",
            "security_rules": "content/references/ai/security.md",
            "skill_workflows": "content/references/replit-skills/<skill>/SKILL.md",
            "instruction_objects": "content/references/ai/<name>.md",
        },
    )

    failed = [name for name, passed, _ in RESULTS if not passed]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
