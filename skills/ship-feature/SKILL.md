---
name: ship-feature
description: This skill should be used when the user asks to "ship this feature", "ship this story", "ship work item", "mark S-core-001 done", "finalize and ship", "ready to ship", "complete this story", or wants to validate the Definition of Done and declare a story (work item) ready for merge or release.
version: 3.0.0
---

# Ship Feature

Check the story's Definition of Done — including the independent review gate — and mark it `Done`.
Updates documentation first, then runs the full checks on the final state of the work, then lets
`story_state.py` mark the story Done only if every condition holds. Statuses and folder rules:
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

Below, `GC` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py"`,
`CHECKS` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_checks.py"`, and
`STATE` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/story_state.py"`.

## Setup

Identify the story ID from user request or context and resolve its folder (`spec/stories/<story-id>-*/`).
A legacy folder (`spec/features/…`) must be migrated first (`scripts/migrate_spec.py`) — `STATE` refuses
legacy folders.

Read:
1. `CLAUDE.md` — command overrides
2. `story.md` — acceptance criteria and Definition of Done
3. `test-plan.md` — smoke scenarios and artifact expectations
4. `status.md` — status, review state

## Pre-Execution Verification

- [ ] Every AC in `story.md` is checked off
- [ ] At least one smoke scenario in `test-plan.md`, with fixtures defined
- [ ] Docstring requirements noted for any API changes

If anything is missing, use the spec-linter skill to identify gaps. Do not proceed while any AC is
unchecked. The remaining Definition of Done items are verified by the steps below.

## Step 1: Review Gate

```bash
GC <story-id>
```

- `PASS` → continue.
- `NO_REVIEW` or `STALE` (code changed since the reviewed commit) → use the independent-review skill,
  then re-check. For a story still in its fix loop, return to the implementation-phase skill.
- `FAIL` → stop. List the open high/medium findings; the story is not shippable.

Never mark a story Done with a failing or stale gate, and never edit review files or add waivers to get
past it — only the user can waive findings (see the independent-review skill).

## Step 2: Architecture Review

Use the architecture-review skill if any of the following occurred:
- New external dependency added
- Significant design choice made
- New integration boundary introduced
- Existing interface changed incompatibly

Skip if no architectural decisions were made.

## Step 3: Documentation

Use the docs-update skill if any user-facing behavior changed:
- CLI flags or output format changed
- API contract changed
- README quickstart is affected

The docs-update skill also refreshes `spec/index.md`. Markdown-only changes do not invalidate the review,
but they must still pass the checks in Step 4 — formatters and linters may check Markdown and the code
blocks inside it. That is why the checks run after this step.

Also update `implementation.md` (files changed, decisions made) now.

## Step 4: Full Checks — after the last edit

```bash
CHECKS --mode full --record <story-id>
```

The script runs format, lint, typecheck, docstrings (if configured), the full test suite, and smoke, in
that order; stops at the first failure; validates the smoke artifacts (`summary.json`, `cases/`,
`stdout.txt`, `stderr.txt`, `timing.json`); and records the result in `test-results.md` and
`evidence/checks.json`, tied to the current commit. **Never write check results by hand** — the recorded
result is the evidence `STATE done` relies on.

- **PASS** → continue.
- **FAIL** → fix the failing step. If the fix changed code, the review is now stale: go back to Step 1.
  If it only changed docs or specs, re-run Step 4.
- Any edit after this step (other than the status updates `STATE` makes) means running Step 4 again.

## Step 5: Mark Done

```bash
STATE done <story-id> [--note "<anything worth recording, e.g. ADR-0004 added>"]
```

It changes nothing and reports why unless **all** of these hold:
- the review gate passes and is current,
- the recorded full check run passed on the current code,
- every AC in `story.md` is ticked.

On success it ticks the Definition of Done and the Tasks, sets `**Status:** Done` and `**Blockers:** none`,
updates the story's row in `spec/backlog.md` and the epic's `epic.md`, and writes the History line with
the reviewed and checked commits. If it refuses, fix the cause it names — never edit status files by hand
to get around it.

If the story belongs to an epic and every story in it is now Done, recommend the independent-review skill
with scope `epic`.

## Step 6: Commit

Commit the documentation and status updates as `<story-id>: done`, unless the project `CLAUDE.md` or the
user says not to commit.

## Step 7: Readiness Summary

```
## Ship Feature — <story-id>

Review gate:    ✓ r<N> PASS @ <sha> (<k> findings fixed, <l> low → follow-ups)
Full checks:    ✓ format, lint, types, tests, smoke — recorded @ <sha> (run_checks.py)
Smoke:          ✓ <n> cases, artifacts at artifacts/smoke/<run-id>/
Docstrings:     ✓ / n/a
ADR:            ✓ / n/a
Docs:           ✓ / n/a
Epic:           <E-nn: k/n stories Done> / n/a

Done — ready to ship.
```

Only write "Done — ready to ship" when `STATE done` succeeded. If anything is blocked, list what remains.
