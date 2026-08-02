# METCO Human-in-the-Loop Specification

Specification version: 6

## 1. Exclusive triggers

HITL activates only when:

1. `HITL-CASE-1`: the answer or next step remains unknown after bounded approved inspection;
2. `HITL-CASE-2`: two materially correct answers remain and no requirement, convention, or evidence chooses one;
3. `HITL-CASE-3`: proceeding requires the agent to make a decision that changes or expands approved scope.

Risk, complexity, security, destructiveness, review readiness, or routine authorization requirements are not independent HITL triggers.

## 2. Pre-trigger test

Before pausing:

1. inspect only approved direct evidence;
2. apply governing requirements and existing conventions;
3. eliminate options that violate scope, contracts, or protections;
4. use a safe assumption only when it stays inside the approved outcome and does not alter security, data meaning, public contracts, or destructive behavior.

## 3. Check frequency

The three triggers in §1 apply at two grains, not one:

- **Per-Action Gate**: run before every individual state-changing action — one edit, one destructive command, one move to the next workflow step. Lightweight: confirm only that none of the three triggers apply to this specific action, and state the result inline (`Gate: OK` or `Gate: BLOCKED`) before acting. Never batch several actions before checking, and never defer a blocked action to a later report.
- **Mandatory HITL Gate**: run once before editing starts, once before each phase, and once before the final report. Heavier: an explicit 8-row evidence table (see `replit.md`).

The Per-Action Gate never substitutes for the Mandatory HITL Gate at the checkpoints where the table is required. A `BLOCKED` result from either tier triggers the same pause contract in §4 below. A final report must confirm the Per-Action Gate actually ran at each action taken, not only reconstruct plausible answers for it afterward.

## 4. Pause contract

When a trigger applies, Replit MUST:

- stop the entire task before making the unresolved decision;
- perform no further inspection, commands, edits, tests, planning, or independent work;
- return only one decision request;
- keep the task unfinished;
- wait for the next user message.

## 5. Decision request

The request contains:

- stable `HITL-[task]-P[phase]-Q[number]` ID, omitting phase for bounded work;
- case number;
- exact blocked step;
- one smallest question;
- evidence checked and remaining unknown;
- both correct options and tradeoffs for case 2;
- current and proposed boundaries for case 3;
- effect of each answer;
- exact resume point;
- required reply `DECIDE [HITL-ID]: [answer and exact scope]`.

## 6. Resume protocol

1. Match the reply to the latest unresolved ID.
2. Confirm the answer resolves the exact question.
3. Confirm the resulting scope remains authorized and permanently allowed.
4. If wrong, incomplete, or ambiguous, ask one narrowed follow-up with the same ID and remain paused.
5. If valid, record the human decision and scope effect.
6. Run only minimal scoped drift checks for evidence that may have changed while waiting.
7. If drift invalidates the decision or prerequisites, issue an updated question and pause.
8. Otherwise resume the exact blocked step.
9. Reuse completed discovery, phases, and checks.

## 7. Final evidence

For every HITL interaction, record:

- ID and case;
- question;
- human answer;
- scope effect;
- drift evidence;
- resumed step;
- post-resume verification.

HITL never overrides protected paths, explicit capability gates, or platform safety.
