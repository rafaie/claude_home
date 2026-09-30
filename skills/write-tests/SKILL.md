---
name: write-tests
description: This skill should be used when the user asks to "write tests for", "add tests for work item", "generate tests", "implement the test plan", or wants to turn a test plan into working test code and verify it runs.
version: 1.0.0
---

# Write Tests

Implement test code from the test plan and verify the tests run.

## Setup

Identify the story ID from the user's request or context.

Read:
1. `CLAUDE.md` — command overrides
2. `spec/stories/<story-id>-<slug>/story.md` — acceptance criteria
3. `spec/stories/<story-id>-<slug>/test-plan.md` — test matrix and smoke scenarios (required)

If `test-plan.md` is missing or empty, use the test-plan skill first.

## Implementation

### 1. Source acceptance criteria

Cross-reference `story.md` and `test-plan.md`. For each test case in the matrix, confirm the AC ID it covers.

### 2. Write test code

Place tests under `tests/` following the project's existing structure.

Conventions:
- One test file per module or feature area
- Descriptive test names that state the behavior being verified
- Reference the AC ID in each test — in the name (`test_ac2_rejects_expired_token`) or a short comment —
  so the reviewer can trace AC → test
- Each test must fail if the behavior it covers is removed; avoid assertions that pass trivially
- Google-style docstrings on shared fixtures only — not on every test function
- No docstrings that restate the function name

For each test type:
- **Unit** — test the function or class directly with minimal setup
- **Integration** — wire up real dependencies where the test plan specifies real; otherwise use stubs
- **Negative** — use `pytest.raises` or equivalent to assert error conditions

### 3. Implement fixtures

Create shared fixtures in `tests/conftest.py`. Reuse existing fixtures where they exist. Add Google-style docstrings to new shared fixtures.

### 4. Run quick tests

Execute the quick test command (`uv run pytest -q` or the project override).

Expected outcome:
- **Pre-existing tests pass.**
- **New tests for behavior that is not built yet fail on their assertions (red)** — this is the test-first
  signal that they test something real. Record which tests are red and for which AC.
- New tests for behavior that already exists pass.
- **No collection, import, or fixture errors** — those are test bugs, never an acceptable red.

If tests fail unexpectedly:
- Fix the test code if the test is wrong
- Note in `test-results.md` if a test reveals a spec gap (raise with the user)

### 5. Document results

Update `spec/stories/<story-id>-<slug>/test-results.md`:

```markdown
## Quick Test Run — <date>
Command: `<command used>`
Result: <pass / fail count> — red as expected: <test → AC list, or none>
Notes: <any issues>
```

## Completion Criteria

- [ ] All test cases from `test-plan.md` have corresponding test functions
- [ ] Quick test run has no errors; pre-existing tests pass; every red test is for a not-yet-built AC
- [ ] `test-results.md` updated

## Handoff

Recommend the implement-feature skill as the next step. The tests are now in place for the implementation to satisfy.
