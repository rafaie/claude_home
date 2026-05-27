---
name: debug-loop
description: This skill should be used when the user says "debug this failure", "tests are failing", "fix this error", "something is broken", "debug-loop", or when a test or runtime failure needs systematic diagnosis and resolution.
version: 1.0.0
---

# Debug Loop

Systematically resolve test or runtime failures. Emphasizes reproducibility, minimal reproduction cases, and regression coverage before applying a fix.

## Setup

If the failure is tied to a specific work item, use the work-item-status skill first to confirm the current phase, recent activity, and any prior test results. This prevents re-investigating issues that are already documented.

## Command Resolution

Read `CLAUDE.md` for command overrides. Defaults:
- Quick test: `uv run pytest -q`
- Full test: `uv run pytest -q`

## Step 1: Reproduce the Failure

Run the failing test or command and capture the full output. Confirm the failure is reproducible before proceeding. If the failure is intermittent, use the flaky-test-hunter skill instead.

Record:
- Exact command that triggers the failure
- Full error message and stack trace
- Environment details if relevant (Python version, OS, dependencies)

## Step 2: Minimize the Case

Reduce the reproduction to the smallest possible input or test case:
- Isolate the failing test from the suite: `pytest path/to/test.py::test_name -v`
- Remove irrelevant setup and fixtures
- Confirm the minimal case still fails

A minimal reproduction case makes root cause identification faster and the fix verifiable.

## Step 3: Add a Regression Test

Before applying the fix, write a test that:
- Reproduces the exact failure
- Will pass once the fix is applied
- Is small and focused on the root cause

Run the new test to confirm it fails (red). This locks in the fix boundary.

## Step 4: Fix the Root Cause

Identify the root cause from the stack trace and minimal case. Apply the minimal fix:
- Fix the logic, not the test
- Do not suppress errors or add try/except to mask failures
- Do not add feature flags or special cases when the real issue can be corrected

Run the regression test after applying the fix (should now pass — green).

## Step 5: Validate

Run the full test suite to confirm no regressions:
```
<test_full command>
```

If new failures appear, repeat from Step 1 for each new failure. If multiple failures appear simultaneously, use the failure-triage skill.

## Step 6: Document

Update `spec/features/<work-id>-<slug>/status.md` if this was blocking a work item:
- Remove the blocker
- Note the root cause in one sentence

If the failure reveals a spec gap, update `feature.md` acceptance criteria.

## Completion Criteria

- [ ] Regression test added and passing
- [ ] Full test suite passing
- [ ] Root cause documented (one sentence)
