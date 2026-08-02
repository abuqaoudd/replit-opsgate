# METCO Instruction Maintenance Object

Use when the router automatically selects `INSTRUCTION_SYSTEM_MAINTENANCE` from an explicit instruction-change request. Modify only the exact authorized `replit.md`, `ai/**`, and `.agents/skills/**` targets; do not modify application code.

## Responsibility

Own instruction-system updates for root rules, domain instruction objects, scenario skills, progressive disclosure, references, indexes, validation expectations, and distribution consistency.

## Activation

Use this object only for explicit instruction-change requests routed to `INSTRUCTION_SYSTEM_MAINTENANCE`. It never authorizes application, schema, package, config, generated, or protected-path changes.

## Inputs

- Exact authorized instruction paths, requested policy change, affected modes/skills/references, and preserved protections.
- Current root instructions, domain files, skill frontmatter, Python contracts, generated copies, and validation results.
- Versioning, indexes, duplicate source locations, and release/build expectations.

## Must Not

- Broaden authority, weaken permanent protections, add fictional paths/modes, duplicate Python contract truth in Markdown, or leave stale generated copies.
- Modify application code or unrelated instructions.
- Make material policy changes without explicit user authorization and documentation.

## Design

- Root: precedence, scope, protection, automatic internal mode catalog, lifecycle, and permanent capability gates.
- `ai/metco.md`: cross-project task record and evidence.
- Domain files: non-duplicated domain rules.
- Skills: short scenario workflows that reference root/domain files and never grant permission.

Keep trigger descriptions specific. Use imperative steps, progressive disclosure, tables for routing, and one source of truth per rule. Remove contradictions, broken references, repeated prose, obsolete sections, and fictional paths/modes. Internal modes must map to real skills and never grant authority. Preserve permanent protections unless the user explicitly authorizes and documents a policy change.

For material changes update the root instruction version and all affected indexes/skill references.

## Workflow

1. Identify the instruction objects, root rules, specs, templates, Python contracts, generated copies, and skills affected by the requested change.
2. Preserve one source of truth per rule and remove contradictions or duplicate stale prose.
3. Keep object responsibilities, inputs, boundaries, workflows, and output evidence aligned.
4. Update indexes, versions, references, templates, and validation expectations when the contract changes.
5. Rebuild distributions and validate canonical/generated parity before release.

## Output Evidence

Report version, files changed, rules added/changed/removed, contradictions fixed, validation results, and scope compliance.

## Validate

Confirm:

- every referenced file/skill exists and skill folder matches frontmatter name;
- skill frontmatter contains only `name` and `description`;
- every internal mode maps to an existing skill and every writable category is governed by a root capability gate;
- user-facing prompts do not ask users to choose a mode, skill, complexity label, or execution profile;
- no skill broadens root access;
- normal work cannot edit instructions/schema/packages/config;
- protected paths remain inaccessible;
- migration/seed workflows have explicit activation and environment guards;
- duplicated distribution copies match their canonical files;
- application/protected files did not change.
