---
name: test-plan
description: This skill should be used when the user asks to "create test plan", "write test strategy for", "plan tests for", "generate test matrix", or wants to produce a structured test plan from acceptance criteria before writing test code.
version: 1.0.0
---

# Test Plan

Generate a comprehensive test strategy from a story's acceptance criteria. Produces `test-plan.md` that drives the write-tests skill.

## Setup

Identify the story ID from the user's request or context.

Read:
1. `CLAUDE.md` — project constraints and command overrides
2. `spec/stories/<story-id>-<slug>/story.md` — acceptance criteria (required)
3. `spec/stories/<story-id>-<slug>/test-plan.md` — check for existing content
4. `spec/stories/<story-id>-<slug>/implementation.md` — approach, if available

If the story is `Ready`, set `**Status:** In Progress` and record `**Base commit:**` (`git rev-parse HEAD`)
in `status.md` unless already set.

If `test-plan.md` already contains a Test Matrix with at least one test case, summarize what is already there and only fill gaps — do not overwrite existing test cases. Report what was preserved and what was added.

## Step 1: Input Gathering

Map each acceptance criterion (`AC-1…n` in `story.md`) to one or more test cases. Identify:
- Inputs and expected outputs for each AC
- Boundary conditions and edge cases
- External dependencies that need mocking or stubbing
- Smoke scenarios that require real subprocess execution

## Step 2: Test Matrix

Produce a matrix with one row per AC ID, covering all four test types:

| AC | Unit | Integration | E2E / Smoke | Negative |
|---|---|---|---|---|
| AC-1 | describe | describe | describe | describe |

Every AC must have a row — the independent reviewer checks AC-to-test coverage.

**Test type definitions:**
- **Unit** — pure logic, no I/O, fast
- **Integration** — crosses a module or layer boundary
- **E2E / Smoke** — real subprocess or external call, artifact-producing
- **Negative** — invalid input, error paths, resource exhaustion

## Step 3: Mock Strategy

For each external dependency (database, API, filesystem, subprocess), decide:
- **Mock** — when the dependency is unreliable or slow in CI
- **Real** — when correctness depends on actual behavior (prefer for smoke)

Document the decision and rationale.

## Step 4: Smoke Spec

Define at least one smoke scenario per AC that involves an observable side effect:
- AC IDs covered
- Entry point command or API call
- Input fixture or payload
- Expected artifacts (`summary.json`, stdout, files created)
- Pass/fail criteria

## Output

Write the test plan to `spec/stories/<story-id>-<slug>/test-plan.md`:

```markdown
# Test Plan — <Story ID>

## Test Matrix
<table from Step 2>

## Mock Strategy
<decisions from Step 3>

## Smoke Scenarios
### Scenario 1: <name>
- Covers: `<AC IDs>`
- Command: `<command>`
- Input: `<fixture path or description>`
- Expected artifacts: `<list>`
- Pass condition: `<observable criterion>`
```

## Handoff

Recommend the write-tests skill as the next step.
