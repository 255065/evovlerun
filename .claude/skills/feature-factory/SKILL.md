---
name: feature-factory
description: Run a feature from a rough idea to a validated, PR-ready change through the 7-agent pipeline (research → story → spec → backend → frontend → verify → validate) with three human checkpoints. Use when the user says "build feature X", "ship X through the factory", "run the feature factory", or gives a feature request they want done end-to-end with review gates.
---

# Feature Factory

You are the orchestrator. You drive EvolveRun's 7 specialist agents in order
and STOP at three human checkpoints. You do not write feature code yourself —
you launch the right agent at each step via the Agent tool and pass forward
exactly what the next agent needs.

The agents live in `.claude/agents/`: `codebase-researcher`, `story-writer`,
`spec-writer`, `backend-builder`, `frontend-builder`, `test-verifier`,
`implementation-validator`.

## Scope sentinel (drives the hard path-enforcement hook)

A `PreToolUse` hook reads `.claude/.active-scope` and blocks file writes
outside the active scope. You MUST keep it in sync, using Bash:

- Before launching **backend-builder**:   write `backend`  to `.claude/.active-scope`
- Before launching **frontend-builder**:  write `frontend` to `.claude/.active-scope`
- Before launching **test-verifier**:      write `tests`    to `.claude/.active-scope`
- After the last builder/verifier finishes, or at any pause: **delete**
  `.claude/.active-scope` (so normal editing isn't blocked).

```bash
printf backend  > .claude/.active-scope   # before backend-builder
printf frontend > .claude/.active-scope   # before frontend-builder
printf tests    > .claude/.active-scope   # before test-verifier
rm -f .claude/.active-scope               # at every pause / on completion
```

The read-only agents (researcher, story, spec, validator) need no sentinel —
they can't write anyway.

## The pipeline

**Step 1 — Research.** Launch `codebase-researcher` with the raw feature
request. Wait for its report.

**Step 2 — Story.** Launch `story-writer` with the request + the Researcher's
report. It returns a user story, acceptance criteria, edge cases, out-of-scope,
open questions.

**⏸ CHECKPOINT 1 — Approve the story.** Show the story to the user verbatim.
If it has open questions, ask them. Do NOT proceed until the user approves.

**Step 3 — Spec.** Launch `spec-writer` with the approved story + Researcher's
report. It returns the technical brief (data model, flow, API, frontend, tests,
risks, files-that-change).

**⏸ CHECKPOINT 2 — Approve the brief.** Show the brief to the user. Call out
any "NEW INFRA — needs approval" flags and any anti-patterns the spec caught.
Do NOT touch a single file until the user approves.

**Step 4 — Backend.** `printf backend > .claude/.active-scope`, then launch
`backend-builder` with the approved brief. Capture its summary (the API
contract). On finish, `rm -f .claude/.active-scope`.

**Step 5 — Frontend.** `printf frontend > .claude/.active-scope`, then launch
`frontend-builder` with the approved brief + the Backend Builder's summary. If
it reports an API mismatch, loop back to `backend-builder` to fix the contract,
then re-run. On finish, `rm -f .claude/.active-scope`.

**Step 6 — Verify.** `printf tests > .claude/.active-scope`, then launch
`test-verifier` with the story + brief + both summaries. It writes acceptance
tests and reports PASS/FAIL per criterion. On finish, `rm -f .claude/.active-scope`.
Route any FAIL back to the owning builder (set the sentinel again for that
builder), fix, then re-run the verifier until green.

**Step 7 — Validate.** Launch `implementation-validator`. It audits disk vs
story+brief and reports Critical / Important / Minor. Route Criticals back to
the owning agent and loop. Repeat until no Criticals remain.

**⏸ CHECKPOINT 3 — Review & PR.** Summarize what shipped (files, tests, any
migrations to apply manually, validator status). The user reviews and opens the
PR. Follow CLAUDE.md git rules: branch if on the default branch, commit/push
only when the user asks.

## Rules
- Never skip a checkpoint. The three pauses are the whole point.
- Never let a builder run with the wrong sentinel set, and always clear the
  sentinel at a pause so the user can edit freely.
- If the Researcher or Spec surfaces that the feature is under-specified, stop
  at the nearest checkpoint and ask — don't build on a guess.
- Keep each agent's input minimal and relevant — clean context per agent is
  why this beats one long thread.
