# Project Setup (filled in by the Replit Agent, not the user)

This file is for you, the Agent, to fill in - the user is never expected to open or edit it
themselves. This engine exists to help people with no technical background use Replit safely, so
the user should do as little of the work as possible: detect what you can from the project's own
files before asking anything, and only ask the user about the handful of fields below marked
"ask the user" - in plain, everyday language, never using the field names or technical terms below.

Write each answer into this file yourself, directly below that field's `<!-- key: ... -->` marker,
in place of the `[FILL IN: ...]` text. Keep every `<!-- key: ... -->` marker exactly as it is - it
is how `tools/apply-setup.py` finds each answer afterward. If the user doesn't know an answer yet,
leave that field's `[FILL IN: ...]` text in place rather than guessing or pressing them - it can be
filled in and setup re-run later.

Once every field you could detect or the user could answer is filled in, run:

```
python3 <engine-dir>/tools/apply-setup.py --template PROJECT_SETUP.md --target-root .
```

from this project's root (see `replit.md`'s "First-run setup check" for the full walkthrough).

## Profile key

**Agent: derive this yourself - do not ask the user.** Take the project's real name (below),
lowercase it, and turn spaces/punctuation into hyphens (e.g. "Acme Field Services" -> `acme-field-
services`). This becomes the value of `OPSGATE_PROFILE` once setup is done.

<!-- key: profile -->
[FILL IN: derived from the project name, e.g. acme-field-services]

## Project name

**Ask the user** (a plain, natural question - "what's this project called?"). Used in the
generated business file's title and this file's own summary.

<!-- key: project_name -->
[FILL IN: e.g. Acme Field Services]

## Frontend root

**Agent: try to detect this yourself first.** Look at the project's actual folders for one with
its own `package.json` and a client-side framework, an `index.html`, or a components/pages
structure - that is almost always the frontend root. Only ask the user if you genuinely cannot
tell, and keep it plain: "does your app have a separate front-end folder, or is everything in one
place?" Leave the bracket text in place if this project has no separate frontend.

<!-- key: frontend_root -->
[FILL IN: e.g. client/src, detected or confirmed - leave as-is if none]

## Backend root

**Agent: try to detect this yourself first.** Look for a folder with route/API handler files, a
server entry point, or database access code - that is almost always the backend root. Only ask
the user if you genuinely cannot tell, and keep it plain. Leave the bracket text in place if this
project has no separate backend.

<!-- key: backend_root -->
[FILL IN: e.g. server/src, detected or confirmed - leave as-is if none]

## Extra protected paths

**Agent: skip this by default - most projects need nothing here.** Only fill this in if the user
brings up, unprompted, something that should always stay completely off-limits. Never ask this as
a standalone technical question ("any glob patterns to protect?") - that is exactly the kind of
question this engine exists to avoid asking. Leave the bracket text in place otherwise.

<!-- key: extra_never_access -->
[FILL IN: one per line, only if the user brings it up unprompted - otherwise leave as-is]

## Business Facts

**Ask the user** - these are the only questions that truly need their own knowledge; everything
above this line, you should have detected or derived yourself. Ask in plain, everyday language (as
shown in the examples below, not the technical-sounding field names), as one natural conversation
rather than reading off a list. See `ai/metco.md` in the `replit-opsgate` engine repo for a
filled-in example of the level of detail these are meant to hold - only an example to look at, not
something this project depends on. It is completely fine if the user can only answer some of these
right now.

### Source

Ask: "does any of this come from an existing document, or are we figuring it out as we go?"

<!-- key: business_source -->
[FILL IN: e.g. a document name and date, or "none yet - figuring it out as we go"]

### Roles

Ask: "who uses this, and what can each type of person do (and not do)?"

<!-- key: business_roles -->
[FILL IN: who uses this and what each type of person can/can't do]

### Lifecycle

Ask: "does anything move through stages or steps, like a job going from scheduled to in-progress to
done?"

<!-- key: business_lifecycle -->
[FILL IN: how things move through stages, if anything does]

### ID formats

Ask: "do you use specific numbering for things like orders, invoices, or jobs (e.g. INV-2026-001)?"

<!-- key: business_id_formats -->
[FILL IN: any specific numbering/ID formats used]

### Key business rules

Ask: "are there any rules that must always be followed, or things that should never happen?"

<!-- key: business_rules -->
[FILL IN: rules that must always/never be broken]

### Design system

Ask: "is there anything about how it looks or is laid out that should always stay the same?"

<!-- key: business_design_system -->
[FILL IN: anything about look/layout worth keeping consistent]

### Known drift to watch for

Ask: "is there anything in old notes or plans that's no longer actually true about how it works
today?"

<!-- key: business_known_drift -->
[FILL IN: anything outdated docs say that isn't true anymore, or "nothing known yet"]
