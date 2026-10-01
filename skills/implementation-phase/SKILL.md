---
name: implementation-phase
description: This skill should be used when the user explicitly asks to "run the full implementation cycle", "run implementation phase for", "do all the steps for", "take this story through review", or wants to orchestrate the complete test-plan → write-tests → implement-feature → independent review sequence end-to-end for a single story (work item). Do NOT use this skill when the user asks to implement a feature directly — use the implement-feature skill for that — or for several stories at once — use the story-runner skill for that.
version: 2.1.0
---

# Implementation Phase

Orchestrate the full delivery cycle for a single story: test-plan → write-tests → implement-feature →
commit → independent review (with fix loop). Detects and skips steps that are already complete. The
story model, statuses, and folder rules are in `${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the story ID (format: `S-<area>-<nnn>`) from the user's request or context and resolve its
folder (`spec/stories/<story-id>-*/`, or legacy `spec/features/<story-id>-*/`).

Read:
1. `CLAUDE.md` — project constraints, `## Commands`, and `## Review` settings
2. `story.md` — acceptance criteria (required)
3. `status.md` — status, base commit, review state
4. `test-plan.md` — check if already populated
5. `test-results.md` — check if tests have been run

If the story folder does not exist, use the feature-kickoff skill first and return.

Use the work-item-status skill for a quick orientation when resuming from a previous session.

## Entry: Definition of Ready

If `**Status:**` is `Backlog`, use the spec-linter skill. Continue only when it sets the status to
`Ready`. If a story in `**Depends on:**` is not `Done`, stop and report it.

## Start work

When moving from `Ready` to `In Progress`:
- If on the default branch, create `story/<story-id>-<slug>` first.
- Record the transition (sets the status, the base commit — never overwriting an existing one — the
  History line, and the backlog/epic rows):
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/story_state.py" start <story-id>
  ```

## Partial Completion Detection

| Step | Already done if... |
|---|---|
| 1 test-plan | `test-plan.md` Test Matrix has a row for every AC ID in `story.md` |
| 2 write-tests | `test-results.md` has a Quick Test Run entry |
| 3 implement-feature | every AC in `story.md` is checked and `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_checks.py" --verify <story-id>` passes |
| 4 commit | `git status --porcelain` shows no changes outside `spec/`, `artifacts/` |
| 5 review | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py" <story-id>` exits 0 |

Report which steps are skipped and why, then resume from the first incomplete step. Do not re-run a
completed step unless the user asks.

## Execution Sequence

Run incomplete steps in strict order. Do not start the next step until the current gate passes or the
user explicitly defers it (record the reason in `status.md`).

### Step 1: Test Plan
Use the test-plan skill. **Gate:** every AC ID has at least one test case; at least one smoke scenario.

### Step 2: Write Tests
Use the write-tests skill. **Gate:** a test exists for every AC; tests run without collection or fixture
errors; pre-existing tests still pass. New tests for not-yet-built behavior are expected to fail (red).

### Step 3: Implement
Use the implement-feature skill. **Gate:** all ACs checked, and a full check run recorded with
`run_checks.py --mode full --record <story-id>` passes (format, lint, types, tests, smoke with artifacts).

### Step 4: Commit
Commit the story's code, tests, and spec updates in one commit:

```
<story-id>: <story title>

<one line per AC implemented>
```

The review is pinned to this commit. If the project `CLAUDE.md` or the user says not to commit, stop here
and ask how to proceed — do not run a review on uncommitted code.

### Step 5: Independent Review
Use the independent-review skill (scope `story`). **Gate:** `gate_check.py` passes.

**Fix loop** when the gate fails:
1. Fix each open high/medium finding with the smallest change — use implement-feature for behavior gaps
   and debug-loop for failures. Add or fix tests so each fix is covered.
2. Re-run and record the full checks: `run_checks.py --mode full --record <story-id>`.
3. Commit: `<story-id>: address review r<N> (F<ids>)`.
4. Run the independent-review skill again — a new round with a fresh reviewer.

If the gate reports `ESCALATE` (round limit reached), stop and ask the user. Never waive findings, edit
review files, or trim the reviewer prompt to get a PASS — see the independent-review integrity rules.
If you believe a finding is wrong, say so to the user with your evidence and let them decide.

## Error Handling

- Single deterministic failure → use the debug-loop skill
- Multiple simultaneous failures → use the failure-triage skill
- Story too large (more than ~5 tasks, or ACs keep growing) → set `**Blockers:** needs split`, stop, and
  recommend the feature-slicer skill
- Hold at the current step until resolved or explicitly deferred with a recorded reason

## Completion Summary

```
## Implementation Phase Complete — <story-id>

Steps:     test-plan ✓ · write-tests ✓ · implement ✓ · commit ✓ · review ✓ (r<N> PASS @ <sha>)
Skipped:   <steps skipped with reason>
Findings:  <n> fixed across <N> rounds · <l> low → backlog follow-ups
Blockers:  none (or list deferred items)
Next:      ship-feature
```

Recommend the ship-feature skill as the next action.
