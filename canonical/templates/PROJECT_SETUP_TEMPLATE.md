# Project Setup (filled in by the Replit Agent, not the user)

This file is for you, the Agent, to fill in - the user is never expected to open or edit it
themselves. Work through the fields below: ask the user about each one in your own words, as a
normal conversation (don't paste these headings or dump the whole file at them), and write their
answer into this file yourself as you go, directly below that field's `<!-- key: ... -->` marker,
in place of the `[FILL IN: ...]` text. Keep every `<!-- key: ... -->` marker exactly as it is - it
is how `tools/apply-setup.py` finds each answer afterward.

If the user doesn't know an answer yet, leave that field's `[FILL IN: ...]` text in place rather
than guessing on their behalf - it can be filled in and setup re-run later. Group related
questions together where it reads naturally (e.g. ask the Business Facts questions as one
conversation rather than one at a time), but write each answer into its own field regardless of
how the questions were asked.

Once every field the user was able to answer is filled in, run:

```
python3 <engine-dir>/tools/apply-setup.py --template PROJECT_SETUP.md --target-root .
```

from this project's root (see `replit.md`'s "First-run setup check" for the full walkthrough).

## Profile key

A short lowercase identifier for this project, hyphen-separated (e.g. `acme`, `my-project`). This becomes
the value of `OPSGATE_PROFILE` once setup is done.

<!-- key: profile -->
[FILL IN: e.g. acme]

## Project name

The project's real name, used in the generated business file's title and this file's own summary.

<!-- key: project_name -->
[FILL IN: e.g. Acme Field Services]

## Frontend root

The folder where this project's frontend source code lives, relative to this project's root (e.g.
`client/src`). Leave the bracket text in place if this project has no separate frontend.

<!-- key: frontend_root -->
[FILL IN: e.g. client/src, or leave as-is if none]

## Backend root

The folder where this project's backend/API source code lives, relative to this project's root (e.g.
`server/src`). Leave the bracket text in place if this project has no separate backend.

<!-- key: backend_root -->
[FILL IN: e.g. server/src, or leave as-is if none]

## Extra protected paths

Any folders or files specific to this project that should never be opened, edited, or referenced by the
Agent, beyond the universal baseline (`.git/**`, `.env`, `node_modules/**`, `.github/workflows/**`,
`.claude/**`, `.agents/memory/**`, always protected regardless of this field). One glob per line. Leave
the bracket text in place if there are none.

<!-- key: extra_never_access -->
[FILL IN: one glob per line, e.g.
legacy-service/**
vendor/**
- or leave as-is if none]

## Business Facts

The project's own domain ground truth - the more specific, the fewer wrong assumptions the Agent will
make later. See `ai/metco.md` in the `replit-opsgate` engine repo for a filled-in example of the level of
detail each of these is meant to hold; it is only an example to look at, not something this project
depends on.

### Source

Where these facts come from - a BRD/spec document and its date, or "none yet" if this is being defined as
you go.

<!-- key: business_source -->
[FILL IN: e.g. BRD-ACME-001 v1.0 (2026-08-01), or "none yet - fill in as decisions are made"]

### Roles

Who can do what. List each role and what it owns / cannot do.

<!-- key: business_roles -->
[FILL IN: list roles and what each owns / cannot do]

### Lifecycle

Entity state machines, if any (e.g. an order goes Draft -> Scheduled -> Completed).

<!-- key: business_lifecycle -->
[FILL IN: entity state machines, if any]

### ID formats

Any standardized identifier formats this project uses (e.g. invoice numbers, order IDs).

<!-- key: business_id_formats -->
[FILL IN: any standardized identifier formats]

### Key business rules

Non-exhaustive is fine - list the rules that matter most. The Agent will escalate rather than invent
anything not covered here.

<!-- key: business_rules -->
[FILL IN: non-exhaustive list of key business rules]

### Design system

Visual/UX conventions worth restating for every task (palette, component conventions, things to
preserve).

<!-- key: business_design_system -->
[FILL IN: visual/UX conventions worth restating for every task]

### Known drift to watch for

Anything older docs/specs say that the current code no longer actually does.

<!-- key: business_known_drift -->
[FILL IN: anything the docs say that code no longer does, or "none known yet"]
