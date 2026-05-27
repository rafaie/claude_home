---
name: implementation-phase
description: This skill should be used when the user asks to "run implementation phase", "implement work item end to end", "full implementation cycle for", "run the full cycle for", or wants to execute the complete test-plan → write-tests → implement-feature sequence for a single work item.
version: 1.0.0
---

# Implementation Phase

Orchestrate the full implementation cycle for a single work item. Runs three skills in strict order: test-plan, write-tests, implement-feature.

## Setup

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or context.

Read:
1. `CLAUDE.md` — project constraints and command overrides
2. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria
3. `spec/features/<work-id>-<slug>/status.md` — current phase

If the feature folder does not exist, use the feature-kickoff skill first.

## Execution Sequence

Run the following three steps in strict order for the same work item. Do not start the next step until the current step succeeds or is explicitly deferred.

### Step 1: Test Plan

Use the test-plan skill to generate a test strategy from the acceptance criteria. Output is written to `test-plan.md` in the work item folder.

**Gate:** `test-plan.md` must contain at least one test case and one smoke scenario before proceeding.

### Step 2: Write Tests

Use the write-tests skill to implement test code from the test plan. Tests are run in quick mode after writing.

**Gate:** All new tests must be present and the quick test command must exit cleanly before proceeding. If tests fail, use the debug-loop skill before continuing.

### Step 3: Implement Feature

Use the implement-feature skill to complete the acceptance criteria checklist, run full checks, and document results.

**Gate:** All acceptance criteria verified, full test run passes, smoke test passes with artifacts.

## Error Handling

- Single deterministic failure → use the debug-loop skill
- Multiple simultaneous failures → use the failure-triage skill
- Hold until the current step is resolved or explicitly deferred with a recorded reason

## Completion Summary

After all three steps succeed, produce:

```
## Implementation Phase Complete — <work-id>

Steps completed: test-plan ✓, write-tests ✓, implement-feature ✓
Blockers: none (or list any deferred items)
Next: ship-feature
```

Recommend the ship-feature skill as the next action.
