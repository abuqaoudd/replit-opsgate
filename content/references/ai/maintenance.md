# Instruction Maintenance Object

Use when the router automatically selects `INSTRUCTION_SYSTEM_MAINTENANCE` from an explicit instruction-change request. Modify only the exact authorized `replit.md`, `ai/**`, and `.agents/skills/**` targets; do not modify application code.

## Responsibility

Own instruction-system updates for root rules, domain instruction objects, scenario skills, progressive disclosure, references, indexes, and validation expectations.

## Activation

Use this object only for explicit instruction-change requests routed to `INSTRUCTION_SYSTEM_MAINTENANCE`. It never authorizes application, schema, package, config, generated, or protected-path changes.

## Inputs

- Exact authorized instruction paths, requested policy change, affected modes/skills/references, and preserved protections.
- Current root instructions, domain files, skill frontmatter, Python contracts, and validation results.
- Versioning and indexes.

## Must Not

- Broaden authority, weaken permanent protections, add fictional paths/modes, or duplicate Python contract truth in Markdown.
- Modify application code or unrelated instructions.
- Make material policy changes without explicit user authorization and documentation.

## Design

- Root: precedence, scope, protection, automatic internal mode catalog, lifecycle, and permanent capability gates.
- A tenant's own business file, if it has one: cross-project task record and evidence.
- Domain files: non-duplicated domain rules.
- Skills: short scenario workflows that reference root/domain files and never grant permission.

Keep trigger descriptions specific. Use imperative steps, progressive disclosure, tables for routing, and one source of truth per rule. Remove contradictions, broken references, repeated prose, obsolete sections, and fictional paths/modes. Internal modes must map to real skills and never grant authority. Preserve permanent protections unless the user explicitly authorizes and documents a policy change.

For material changes update the root instruction version and all affected indexes/skill references.

## Workflow

1. If the requested change is to bring this project's own instruction system (`replit.md`, `ai/**`, `.agents/skills/**`) current with the engine's canonical versions - or this is a brand-new project with none installed yet - call `opsgate_sync_instructions`. It returns every current file with its own target `path` (skill files install under `.agents/skills/`, not `replit-skills/`). Write each returned file to its `path`, creating anything missing and overwriting anything that differs, leaving unrelated local files untouched; then re-read each to confirm the write succeeded. This never creates a tenant or token - if a brand-new project also needs one, that stays a separate, deliberate step (see `ADOPTION_GUIDE.md`), not something this call does on its own.
2. Identify the instruction objects, root rules, specs, templates, Python contracts, and skills affected by the requested change.
3. Preserve one source of truth per rule and remove contradictions or duplicate stale prose.
4. Keep object responsibilities, inputs, boundaries, workflows, and output evidence aligned.
5. Update indexes, versions, references, and templates when the contract changes.
6. Validate before release.

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
- application/protected files did not change.
