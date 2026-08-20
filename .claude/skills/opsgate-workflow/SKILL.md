---
name: opsgate-workflow
description: Start the OpsGate governed-prompt workflow for a Replit-hosted project - compiles a gated, self-contained prompt for Replit from a plain-language request and processes its reports back.
disable-model-invocation: true
---

# OpsGate workflow

You were explicitly invoked to start the OpsGate prompt-compiler workflow (`/opsgate-workflow`).
This only runs when called this way - the OpsGate MCP tools being connected is never itself a
reason to use them for an unrelated request.

## What this does

Turns a plain-language request into a governed, self-contained prompt for a Replit Agent, tracks
state across Replit's disposable sessions (Replit has no memory between prompts), and turns
Replit's reports back into the next phase's prompt.

## Steps

1. Read the `opsgate://knowledge/claude-mcp-workflow` MCP resource for the full numbered chain
   (intake -> route -> preflight -> compile -> init_run -> hand off -> parse_report ->
   next_phase_prompt) and the rules for using each tool correctly.
2. If a task description was given alongside this invocation, treat that as the plain-language
   request to run through the chain. Otherwise, ask what should be built or changed for the
   Replit-hosted project before proceeding.
3. Follow the chain from that resource exactly, calling the connected `opsgate_*` MCP tools -
   never re-derive gates, routing, or prompt structure by hand when a tool exists for it.
