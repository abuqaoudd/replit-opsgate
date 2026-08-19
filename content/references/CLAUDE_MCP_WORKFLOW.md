# OpsGate prompt-compiler workflow

Use the `opsgate` MCP tools to turn a plain-language request into a governed, self-contained
prompt for a Replit Agent, then read its report back. Replit sessions do not persist state
between prompts - each one is a fresh session with no memory of this conversation or of any
earlier Replit session - so this workflow exists to carry state across that gap from this side.

## The chain

1. If the user described what they want in plain language, call `opsgate_intake_request` first
   to turn it into a draft structured request (deliverable, outcome, module, likely
   authorizations). Refine the result with the user before treating it as final, especially if
   the tool's own `intake_notes` flag ambiguity.
2. Call `opsgate_route_request` to resolve the mode, skill, references, and execution shape for
   the request. Call `opsgate_preflight` on the same request before compiling anything - a
   missing authorization or a protected-path violation must block here, not surface later
   inside Replit's own session. Report a blocked gate to the user by name; do not compile a
   prompt for a request that failed preflight.
3. Call `opsgate_compile_prompt` to produce the actual prompt text. This is the literal content
   to hand to Replit as a new session - it is self-contained on purpose, since Replit will have
   nothing else to go on. Optionally call `opsgate_lint_prompt` first to confirm the compiled
   text states every required concept before handing it off.
4. If the request's execution shape is phased (not bounded), call `opsgate_init_run` once,
   immediately after compiling the first phase's prompt, to start tracking the run. This is what
   actually persists across Replit's disposable sessions - the server keeps this state on its
   own machine, not in this conversation.
5. Hand the compiled prompt to Replit and wait for its final report.
6. Feed Replit's final report text into `opsgate_parse_report` to get structured fields -
   outcome, PASSED/FAILED/NOT RUN checks, blockers, residual risk. Optionally call
   `opsgate_lint_report` first if there is any doubt the report actually filled in every
   required section with real evidence rather than placeholders.
7. For phased work, call `opsgate_next_phase_prompt` with the current run state and the parsed
   report to produce the next phase's prompt. Hand that to Replit as another fresh session.
   Repeat steps 6-7 until the run completes or a phase reports blocked.
8. If a human answers a HITL decision mid-task (a `HITL-[task]-P[phase]-Q[n]` question Replit's
   session raised), call `opsgate_record_decision` with the HITL id and the answer before
   resuming - this persists the decision outside the conversation, since neither this session
   nor whichever Replit session resumes the work will otherwise have it.

## Other tools available

- `opsgate_show_profile` - the active tenant's resolved profile, roots, and protected paths,
  with no request required.
- `opsgate_check_capability` / `opsgate_check_paths` - the individual deterministic gates
  `opsgate_preflight` runs together, for a narrower check mid-conversation without re-running
  the full gate.
- `opsgate_export_ruleset` - a snapshot of the durable governance rules (HITL protocol, security
  rules, skill workflows, instruction objects) for offline or CI use.

## Rules

- Never skip `opsgate_preflight` before compiling a prompt because the request "looks simple" -
  a missing authorization is exactly the kind of thing that is easy to assume and wrong to
  assume.
- Never treat a Replit session's own claims about what it did as a substitute for its final
  report going through `opsgate_parse_report` - parse the report, do not just summarize it by
  eye.
- A blocked gate is not a HITL decision - report it as blocked, state what is missing, and stop.
  Reserve HITL framing for genuine ambiguity (`opsgate_preflight`/`opsgate_check_paths`/
  `opsgate_check_capability` cannot see judgment calls; they only report what is
  deterministically missing).
