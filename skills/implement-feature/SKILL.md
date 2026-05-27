---
name: implement-feature
description: This skill should be used when the user asks to "implement feature S-core-001", "code this feature", "write the code for", "implement-feature", or wants to complete the coding work for a specific work item. Use this skill for the implementation step only. If the user wants the full test-plan → write-tests → implement cycle, use the implementation-phase skill instead.
version: 1.0.0
---

# Implement Feature

Complete the implementation of a single work item end-to-end.

## Setup

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or context.

Read in order:
1. `CLAUDE.md` — command overrides and project constraints
2. `spec/features/<work-id>-<slug>/feature.md` — goal and acceptance criteria
3. `spec/features/<work-id>-<slug>/implementation.md` — approach and prior decisions
4. `spec/features/<work-id>-<slug>/test-plan.md` — test cases and smoke specs

## Implementation Process

### 1. Build the acceptance criteria checklist

Convert each acceptance criterion from `feature.md` into a checkbox. Work through them one at a time.

### 2. Implement iteratively

Make the minimal change to satisfy one criterion at a time. After each criterion:
- Run the quick test command
- Verify the criterion is met before moving to the next

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
- Phase: `Implementation Complete`
- Remove any blockers that are resolved

## Failure Protocol

- Check failures → use the debug-loop skill
- User-facing behavior changes → use the docs-update skill after shipping

## Completion Criteria

All of the following must be true before declaring this skill complete:
- [ ] All acceptance criteria checked off
- [ ] Full test run passes
- [ ] Smoke test passes with artifacts recorded
- [ ] `implementation.md`, `test-results.md`, and `status.md` updated
