# HITL decision required

**ID:** `HITL-[task]-P[phase]-Q[number]`  
**Case:** `[1, 2, or 3] — [case description]`

## Blocked step

[The exact outcome or next step that cannot continue.]

## Question

[One smallest answer needed from the human.]

## Evidence checked

- [Approved evidence or convention checked]
- [What was established]
- [What remains unknown or unresolved]

## Decision detail

For case 1, state the missing answer or next-step information and why bounded inspection could not determine it.

For case 2, present both materially correct answers, their tradeoffs, and the affected behavior. Do not silently choose a default.

For case 3, state the current approved boundary, the agent-made assumption that would be required, and the exact proposed scope expansion. Do not perform the expanded work.

## Options

Offer 2-4 labeled options. Do not ask only for free text.

- A. [option label] - [exact scope effect and outcome]
- B. [option label] - [exact scope effect and outcome]
- C. [optional option label] - [exact scope effect and outcome]
- D. [optional option label] - [exact scope effect and outcome]

For case 1, include a conservative option that stays inside the current approved scope and a separate option for each valid next step Replit can name. For case 2, include both materially correct options and their tradeoffs. For case 3, include one option that stays inside the current approved boundary and one option that explicitly expands scope.

## Pause state

- Entire task paused: yes
- Exact resume point: [phase and blocked step]
- Work permitted before a valid reply: none
- Do not stop, abandon, complete, or restart the task; resume from the exact resume point after a valid reply.

Respond with:

`DECIDE [HITL-ID]: [answer and exact scope]`

Return only this decision request when HITL activates, then wait. Do not inspect, edit, test, plan later work, or report completion while paused. Do not say the task is stopped; say it is paused at the exact resume point.

When the user replies, confirm the ID matches the latest unresolved request and the answer resolves the question within existing authority. If not, ask one narrowed follow-up with the same ID and remain paused. If valid, record the decision, perform the minimal scoped drift check defined in `replit.md`, and resume from the exact blocked step without restarting completed discovery or phases.

Omit irrelevant case-specific fields. Do not add HITL modes, risk levels, gate statuses, or routine approval language.
