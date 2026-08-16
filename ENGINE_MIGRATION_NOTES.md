# Engine Migration Notes

## Goal

Move the underlying prompt-based instructions from a document-only format toward a Replit-ready orchestration engine, reusable across any Replit project (METCO was the first adopting project).

## Architecture

See root [README.md](README.md)'s "Distribution model" and "Engine direction" sections for the canonical-source/generated-output split, the Python-contracts-vs-Markdown principle, and what `tools/opsgate_contracts.py`/`tools/opsgate_fixtures.py` hold - that is the one place this is explained, not restated here.

## Markdown cleanup strategy

Keep existing Markdown content, but improve it gradually:

1. Remove repeated rule bodies once the rule is represented in a Python contract.
2. Keep Replit-facing files operational and concise.
3. Keep artifact templates focused on final output quality.
4. Keep specifications normative, not repetitive.
5. Reference Python-backed rules instead of restating them in every file.

The tools added after the initial foundation pass are recorded in `CHANGELOG.md`'s `6.0.0 Engine Foundation` entry, not repeated here - that changelog entry is the historical record; this document only tracks still-open migration work.

## Suggested v6 work

- Make the prompt compiler template-aware for every artifact type, not just a generated operational prompt.
- Replace the lightweight Python schema validator with a fuller validation implementation if dependencies are allowed.
- Add a richer compatibility checker for v6-to-v6 upgrades.
- Add stronger fixture coverage for multi-deliverable requests and invalid HITL resumes.
