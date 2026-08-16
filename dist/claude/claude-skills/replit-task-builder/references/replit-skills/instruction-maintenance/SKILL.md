---
name: instruction-maintenance
description: Audit, simplify, reconcile, or extend replit.md, ai instruction files, and .agents/skills workflows. Use for explicit instruction-system changes involving faster loading, concise rules, new scenario skills, automatic mode/path consistency, broken references, duplication removal, validation, and version updates without application changes.
---

# Instruction Maintenance

Automatically select internal mode `INSTRUCTION_SYSTEM_MAINTENANCE`. This selects procedure; only explicitly authorized instruction paths may change.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, and `../../../ai/{maintenance}.md` plus every instruction being changed.
2. Require explicit instruction-change authority; capture scoped status/diff and exclude application code.
3. Inventory precedence, automatic modes, paths, triggers, duplicated rules, broken references, contradictions, and missing scenarios.
4. Keep authority, automatic mode mapping, and protection in root; cross-task process in the active profile's business file (e.g. `ai/metco.md` for the `metco` profile); details in domain files; and concise workflows in skills.
5. Make trigger descriptions specific; remove repeated prose; use progressive disclosure; ensure skills never grant authority.
6. Validate names/frontmatter/references, automatic mode-to-skill and path consistency, distribution-copy parity, protected boundaries, and unchanged application files.
7. Update version for material changes and report additions, removals, resolved conflicts, checks, and scope.

Stop before weakening a permanent protection or broadening write authority without explicit policy approval.
