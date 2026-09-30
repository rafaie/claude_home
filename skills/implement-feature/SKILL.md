---
name: implement-feature
description: This skill should be used when the user asks to "implement feature S-core-001", "code this feature", "write the code for", "implement-feature", or wants to complete the coding work for a specific work item. Use this skill for the implementation step only. If the user wants the full test-plan → write-tests → implement cycle, use the implementation-phase skill instead.
version: 1.0.0
---

# Implement Feature

Complete the implementation of a single story end-to-end.

## Setup

Identify the story ID (format: `S-<area>-<nnn>`) from the user's request or context.

Read in order:
1. `CLAUDE.md` — command overrides and project constraints
2. `spec/stories/<story-id>-<slug>/story.md` — goal and acceptance criteria
3. `spec/stories/<story-id>-<slug>/implementation.md` — approach and prior decisions
4. `spec/stories/<story-id>-<slug>/test-plan.md` — test cases and smoke specs

## Implementation Process

### 1. Build the acceptance criteria checklist

Use the ACs in `story.md` (`AC-1…n`) as the checklist, and the Tasks in `implementation.md` as the
steps. If no tasks are listed, write ≤ ~5 before coding; needing more suggests the story should be split
(feature-slicer). Work through the ACs one at a time.

If the project has a knowledge graph (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" status` is
`current` or `stale`), read `GRAPH_REPORT.md` first and run `graphify affected "<symbol>"` before changing
an existing function or class, so its dependents stay working and tested. See
`${CLAUDE_PLUGIN_ROOT}/references/graphify.md`; the graph is a map — verify in source.

### 2. Implement iteratively

Make the minimal change to satisfy one AC at a time. After each AC:
- Run the quick test command
- Verify the AC is met, tick it in `story.md`, and tick finished tasks in `implementation.md`

Add Google-style docstrings for:
- New public APIs
- CLI entrypoints
- Data models and schemas
- Integration boundaries
- Shared test fixtures

Do not add docstrings that merely restate the function name.

### 3. Run milestone checks

Run full checks (lint + format + typecheck + full tests + smoke) after:
- Completing the final acceptance criterion
- Any change to a core or shared module
- Any CLI, API, schema, or externally visible behavior change

### 4. Verify smoke test

Run the smoke-test skill. Confirm required artifacts exist:
- `artifacts/smoke/<run-id>/summary.json`
- `artifacts/smoke/<run-id>/stdout.txt`
- `artifacts/smoke/<run-id>/stderr.txt`
- `artifacts/smoke/<run-id>/timing.json`

## Documentation

After all criteria pass, update:

**`implementation.md`**
- Approach taken
- List of files changed with one-line descriptions
- Key decisions made

**`test-results.md`**
- Commands run and their outcomes
- Smoke artifact paths

**`status.md`**
- Keep `**Status:** In Progress` (the independent review moves it to `In Review`)
- History line: `<date> — implementation complete, all ACs met`
- Remove any blockers that are resolved

## Failure Protocol

- Check failures → use the debug-loop skill
- User-facing behavior changes → update docs before the review where practical (the reviewer checks
  contract docs); otherwise use the docs-update skill during ship-feature

## Completion Criteria

All of the following must be true before declaring this skill complete:
- [ ] All acceptance criteria checked off
- [ ] Full test run passes
- [ ] Smoke test passes with artifacts recorded
- [ ] `implementation.md`, `test-results.md`, and `status.md` updated

## Handoff

Next: commit and run the independent-review skill — the implementation-phase skill does both. A story is
not Done until the review gate passes and ship-feature confirms the Definition of Done.
