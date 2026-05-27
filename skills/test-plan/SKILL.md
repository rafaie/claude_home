---
name: test-plan
description: This skill should be used when the user asks to "create test plan", "write test strategy for", "plan tests for", "generate test matrix", or wants to produce a structured test plan from acceptance criteria before writing test code.
version: 1.0.0
---

# Test Plan

Generate a comprehensive test strategy from a work item's acceptance criteria. Produces `test-plan.md` that drives the write-tests skill.

## Setup

Identify the work item ID from the user's request or context.

Read:
1. `CLAUDE.md` — project constraints and command overrides
2. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria (required)
3. `spec/features/<work-id>-<slug>/test-plan.md` — check for existing content
4. `spec/features/<work-id>-<slug>/implementation.md` — approach, if available

If `test-plan.md` already contains a Test Matrix with at least one test case, summarize what is already there and only fill gaps — do not overwrite existing test cases. Report what was preserved and what was added.

## Phase 1: Input Gathering

Map each acceptance criterion to one or more test cases. Identify:
- Inputs and expected outputs for each criterion
- Boundary conditions and edge cases
- External dependencies that need mocking or stubbing
- Smoke scenarios that require real subprocess execution

## Phase 2: Test Matrix

Produce a matrix covering all four test types for each criterion:

| Criterion | Unit | Integration | E2E / Smoke | Negative |
|---|---|---|---|---|
| <criterion text> | describe | describe | describe | describe |

**Test type definitions:**
- **Unit** — pure logic, no I/O, fast
- **Integration** — crosses a module or layer boundary
- **E2E / Smoke** — real subprocess or external call, artifact-producing
- **Negative** — invalid input, error paths, resource exhaustion

## Phase 3: Mock Strategy

For each external dependency (database, API, filesystem, subprocess), decide:
- **Mock** — when the dependency is unreliable or slow in CI
- **Real** — when correctness depends on actual behavior (prefer for smoke)

Document the decision and rationale.

## Phase 4: Smoke Spec

Define at least one smoke scenario per acceptance criterion that involves an observable side effect:
- Entry point command or API call
- Input fixture or payload
- Expected artifacts (`summary.json`, stdout, files created)
- Pass/fail criteria

## Output

Write the test plan to `spec/features/<work-id>-<slug>/test-plan.md`:

```markdown
# Test Plan — <Work Item ID>

## Test Matrix
<table from Phase 2>

## Mock Strategy
<decisions from Phase 3>

## Smoke Scenarios
### Scenario 1: <name>
- Command: `<command>`
- Input: `<fixture path or description>`
- Expected artifacts: `<list>`
- Pass condition: `<observable criterion>`
```

## Handoff

Recommend the write-tests skill as the next step.
