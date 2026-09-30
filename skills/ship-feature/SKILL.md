---
name: ship-feature
description: This skill should be used when the user asks to "ship this feature", "ship this story", "ship work item", "mark S-core-001 done", "finalize and ship", "ready to ship", "complete this story", or wants to validate the Definition of Done and declare a story (work item) ready for merge or release.
version: 2.0.0
---

# Ship Feature

Check the story's Definition of Done — including the independent review gate — and mark it `Done`.
Runs full checks, validates smoke artifacts, updates documentation, and produces a readiness summary.
Statuses and folder rules: `${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the story ID from user request or context and resolve its folder (`spec/stories/<story-id>-*/`,
or legacy `spec/features/<story-id>-*/`).

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
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py" <story-id>
```

- `PASS` → continue.
- `NO_REVIEW` or `STALE` (code changed since the reviewed commit) → use the independent-review skill,
  then re-check. For a story still in its fix loop, return to the implementation-phase skill.
- `FAIL` → stop. List the open high/medium findings; the story is not shippable.

Never mark a story Done with a failing or stale gate, and never edit review files or add waivers to get
past it — only the user can waive findings (see the independent-review skill).

## Step 2: Run Full Test Suite

Use the test-runner skill in full mode (format, lint, typecheck, full tests, smoke). Do not run
smoke-test separately unless artifacts from a prior run are missing or stale.

Gate: all checks pass before continuing.

## Step 3: Validate Smoke Artifacts

Verify these artifacts exist and are non-empty:
- `artifacts/smoke/<run-id>/summary.json`
- `artifacts/smoke/<run-id>/cases/` (at least one file)
- `artifacts/smoke/<run-id>/stdout.txt`
- `artifacts/smoke/<run-id>/stderr.txt`
- `artifacts/smoke/<run-id>/timing.json`

Record artifact paths in the story's `test-results.md`.

## Step 4: Architecture Review

Use the architecture-review skill if any of the following occurred:
- New external dependency added
- Significant design choice made
- New integration boundary introduced
- Existing interface changed incompatibly

Skip if no architectural decisions were made.

## Step 5: Documentation

Use the docs-update skill if any user-facing behavior changed:
- CLI flags or output format changed
- API contract changed
- README quickstart is affected

The docs-update skill also refreshes `spec/index.md` — no separate step needed. Markdown-only changes
do not invalidate the review; any code change does.

## Step 6: Update Story Files

- **`test-results.md`** — final check commands and outcomes, artifact paths.
- **`implementation.md`** — files changed, decisions made; tick completed tasks.
- **`story.md`** — tick every Definition of Done item that is now verified.
- **`status.md`** — `**Status:** Done`, `**Blockers:** none`, History line with the reviewed SHA.
- **Epic** (if `**Epic:**` is set) — update the story's row in `epic.md` and in `spec/backlog.md`.
  If every story in the epic is now Done, recommend the independent-review skill with scope `epic`.

Re-run `gate_check.py` once more; if code changed during this skill, the gate will report STALE —
go back to Step 1.

Commit the documentation and status updates as `<story-id>: done`, unless the project `CLAUDE.md` or the
user says not to commit.

## Step 7: Readiness Summary

```
## Ship Feature — <story-id>

Review gate:    ✓ r<N> PASS @ <sha> (<k> findings fixed, <l> low → follow-ups)
Full checks:    ✓ format, lint, types, tests
Smoke:          ✓ <n> scenarios, artifacts at artifacts/smoke/<run-id>/
Docstrings:     ✓ / n/a
ADR:            ✓ / n/a
Docs:           ✓ / n/a
Epic:           <E-nn: k/n stories Done> / n/a

Done — ready to ship.
```

Only write "Done — ready to ship" when every item passes. If anything is blocked, list what remains.
