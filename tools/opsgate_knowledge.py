"""Structured access to durable governance rules, read live from their source files.

Reads directly from `content/` at call time rather than holding a copied string constant -
there is exactly one place these rules are authored (the source file), so nothing here can
drift out of sync with it. Content is split into two categories per source file:

- durable: imperative, checkable rules a governed agent must follow.
- scaffolding: prose whose only job is telling a router *when* to show the durable content
  (an "Activation"/"read this when..." section, or a one-line summary of the same). That
  routing decision is meaningless once the content is always-on, so scaffolding sections are
  dropped rather than carried into the returned text.

`HITL_SPEC.md` is entirely durable rule content already (a numbered spec, not a prose object),
so it is returned unabridged.
"""
import re
from pathlib import Path

from opsgate_io import ROOT_DIR

HITL_SPEC_PATH = ROOT_DIR / "content" / "specifications" / "HITL_SPEC.md"
AI_OBJECTS_ROOT = ROOT_DIR / "content" / "references" / "ai"
SECURITY_RULES_PATH = AI_OBJECTS_ROOT / "security.md"
REPLIT_SKILLS_ROOT = ROOT_DIR / "content" / "references" / "replit-skills"

SCAFFOLDING_SECTIONS = {"activation"}

# Every ai/*.md "instruction object" this module extracts. Deliberately an explicit list, not
# a directory glob: ai/metco.md lives alongside these but is dropped, not extracted (verified
# to hold zero real METCO business data), so a glob would need this same exclusion anyway.
INSTRUCTION_OBJECT_NAMES = ["security", "backend", "database", "frontend", "ui-ux", "testing", "refactoring", "agents", "maintenance"]

# Every one of the objects above opens with an H1 title, then either a one-line summary or
# straight into "## Responsibility". That summary line is dropped as scaffolding by default -
# checked against the object's own "## Activation"/"## Must Not" sections file-by-file, it
# turns out to be a pure duplicate of Activation in every case except these two: agents.md's
# ("run only roles relevant to the task") and maintenance.md's (which uniquely names the
# instruction system's own scope - replit.md + ai/** + .agents/skills/**) each say something
# their own Activation/Must Not sections don't already say, so their summary line is kept.
KEEP_SUMMARY_LINE_FOR = {"agents", "maintenance"}


class UnknownSkillError(Exception):
    """Raised for a skill name with no matching content/references/replit-skills/<name>/SKILL.md."""


class UnknownInstructionObjectError(Exception):
    """Raised for a name with no matching content/references/ai/<name>.md instruction object."""


def _split_sections(text):
    """Splits a markdown doc into (title_block, [(heading, section_text), ...]).

    title_block is everything before the first '## ' heading (the H1 title plus any
    one-line summary under it); each section_text includes its own '## Heading' line.
    """
    chunks = re.split(r"\n(?=## )", text.strip())
    title_block, sections = chunks[0], chunks[1:]
    parsed = []
    for chunk in sections:
        heading_match = re.match(r"##\s+(.+)", chunk)
        heading = heading_match.group(1).strip() if heading_match else ""
        parsed.append((heading, chunk.rstrip()))
    return title_block, parsed


def _drop_scaffolding(text, title_only=True):
    title_block, sections = _split_sections(text)
    title_block = title_block.splitlines()[0] if title_only else title_block.rstrip()
    kept = [section_text for heading, section_text in sections if heading.strip().lower() not in SCAFFOLDING_SECTIONS]
    return "\n\n".join([title_block, *kept]).strip()


def hitl_protocol_text():
    return HITL_SPEC_PATH.read_text(encoding="utf-8").strip()


def _instruction_object_path(name):
    if name not in INSTRUCTION_OBJECT_NAMES:
        raise UnknownInstructionObjectError(f"No instruction object named {name!r} (known: {', '.join(INSTRUCTION_OBJECT_NAMES)})")
    return AI_OBJECTS_ROOT / f"{name}.md"


def instruction_object_text(name):
    """The durable rules of one `ai/<name>.md` instruction object, with routing scaffolding
    dropped: the "## Activation" section (superseded by `ROUTING_MANIFEST`'s per-route
    `references`/`signals`) and, for most of these objects, the pre-Activation summary line
    (superseded the same way - see KEEP_SUMMARY_LINE_FOR for the two verified exceptions).
    Every other section - Responsibility, Inputs, Must Not, each object's own domain sections,
    Workflow, Output Evidence - is kept verbatim.
    """
    text = _instruction_object_path(name).read_text(encoding="utf-8")
    return _drop_scaffolding(text, title_only=name not in KEEP_SUMMARY_LINE_FOR)


def security_rules_text():
    return instruction_object_text("security")


def list_skill_names():
    return sorted(path.parent.name for path in REPLIT_SKILLS_ROOT.glob("*/SKILL.md"))


def _skill_path(skill):
    path = REPLIT_SKILLS_ROOT / skill / "SKILL.md"
    if not path.exists():
        raise UnknownSkillError(f"No skill workflow named {skill!r} (known: {', '.join(list_skill_names())})")
    return path


def skill_workflow_text(skill):
    """The durable workflow procedure for one `replit-skills/<skill>/SKILL.md`, with its
    routing scaffolding dropped: the YAML frontmatter (name/description already live as
    `mode`/`skill`/`signals`/`capability` in `ROUTING_MANIFEST`, and as `requires` in
    `CAPABILITY_GATES`), the "Automatically select internal mode ..." sentence (== the same
    `mode` field), and step 1's "Read replit.md/ai/*.md" instruction (== `ROUTING_MANIFEST`'s
    `references` field, already surfaced to the agent via `opsgate_compile_prompt`'s
    `required_references`). The remaining numbered steps and the closing stop/never-access
    constraint are kept verbatim and renumbered from 1.
    """
    text = _skill_path(skill).read_text(encoding="utf-8")
    body = text.split("---", 2)[2].strip()
    title, _mode_sentence, numbered_steps, closing = [p.strip() for p in body.split("\n\n") if p.strip()]

    lines = numbered_steps.splitlines()[1:]  # drop step 1 (the reference-reading step)
    renumbered = [re.sub(r"^\d+\.", f"{index}.", line, count=1) for index, line in enumerate(lines, start=1)]

    return "\n\n".join([title, "\n".join(renumbered), closing])


def export_ruleset():
    """Read-only structured snapshot of every always-on rule this module currently exposes.

    The direct replacement for pulling a `dist/` bundle to see the current ruleset offline or
    in CI - a single call returns the same durable content the MCP resources below serve live.
    """
    return {
        "hitl_protocol": hitl_protocol_text(),
        "security_rules": security_rules_text(),
        "skill_workflows": {skill: skill_workflow_text(skill) for skill in list_skill_names()},
        "instruction_objects": {name: instruction_object_text(name) for name in INSTRUCTION_OBJECT_NAMES},
        "sources": {
            "hitl_protocol": str(HITL_SPEC_PATH.relative_to(ROOT_DIR)),
            "security_rules": str(SECURITY_RULES_PATH.relative_to(ROOT_DIR)),
            "skill_workflows": str(REPLIT_SKILLS_ROOT.relative_to(ROOT_DIR)) + "/<skill>/SKILL.md",
            "instruction_objects": str(AI_OBJECTS_ROOT.relative_to(ROOT_DIR)) + "/<name>.md",
        },
    }
