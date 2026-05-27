---
name: implementation-phase
description: This skill should be used when the user explicitly asks to "run the full implementation cycle", "run implementation phase for", "do all three steps for", or wants to orchestrate the complete test-plan → write-tests → implement-feature sequence end-to-end for a single work item. Do NOT use this skill when the user asks to implement a feature directly — use the implement-feature skill for that.
version: 1.1.0
---

# Implementation Phase

Orchestrate the full implementation cycle for a single work item. Runs three steps in strict order: test-plan → write-tests → implement-feature. Detects and skips steps that are already complete.

## Setup

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or context.

Read:
1. `CLAUDE.md` — project constraints and command overrides
2. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria (required)
3. `spec/features/<work-id>-<slug>/status.md` — current phase
4. `spec/features/<work-id>-<slug>/test-plan.md` — check if already populated
5. `spec/features/<work-id>-<slug>/test-results.md` — check if tests have been run

If the feature folder does not exist, use the feature-kickoff skill first and return.

## Partial Completion Detection

Before running any step, check which steps are already done:

| Step | Already done if... |
|---|---|
| test-plan | `test-plan.md` has a Test Matrix section with at least one test case |
| write-tests | `test-results.md` has a Quick Test Run entry with a passing result |
| implement-feature | `status.md` phase is "Implementation Complete" or "Shipped" |

Report which steps are being skipped and why:
```
Step 1 (test-plan):       ✓ already complete — skipping
Step 2 (write-tests):     ✓ already complete — skipping
Step 3 (implement-feature): pending — running now
```

Resume from the first incomplete step. Do not re-run a step that is already complete unless the user explicitly asks to redo it.

## Execution Sequence

Run incomplete steps in strict order. Do not start the next step until the current one succeeds or is explicitly deferred.

### Step 1: Test Plan

Use the test-plan skill to generate a test strategy from the acceptance criteria. Output is written to `test-plan.md`.

**Gate:** `test-plan.md` must contain at least one test case and one smoke scenario.

### Step 2: Write Tests

Use the write-tests skill to implement test code and run it in quick mode.

**Gate:** All new tests present and quick test command exits cleanly. If tests fail, use the debug-loop skill before continuing.

### Step 3: Implement Feature

Use the implement-feature skill to complete the acceptance criteria checklist, run full checks, and document results.

**Gate:** All acceptance criteria verified, full test run passes, smoke test passes with artifacts.

## Error Handling

- Single deterministic failure → use the debug-loop skill
- Multiple simultaneous failures → use the failure-triage skill
- Hold at the current step until resolved or explicitly deferred with a recorded reason

## Completion Summary

```
## Implementation Phase Complete — <work-id>

Steps completed: test-plan ✓, write-tests ✓, implement-feature ✓
Skipped:         <any steps skipped with reason>
Blockers:        none (or list deferred items)
Next:            ship-feature
```

Recommend the ship-feature skill as the next action.
