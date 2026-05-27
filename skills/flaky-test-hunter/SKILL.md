---
name: flaky-test-hunter
description: This skill should be used when the user says "find flaky tests", "stabilize this flaky test", "test passes sometimes", "test fails intermittently", "non-deterministic test failure", or wants to identify and fix tests that do not produce consistent results across runs.
version: 1.0.0
---

# Flaky Test Hunter

Identify, classify, and stabilize non-deterministic tests. Emphasizes root cause fixes over suppression.

## Step 1: Reproduce the Flakiness

Run the suspected test multiple times to confirm non-determinism:
```bash
# Run 5–10 times with randomized ordering
uv run pytest path/to/test.py -v --count=5 2>/dev/null || \
for i in {1..5}; do uv run pytest path/to/test.py -v; done
```

Record:
- Pass rate (e.g. "3 of 5 runs pass")
- Any pattern in failure timing or ordering

If the test fails every run, it is a deterministic failure — use the debug-loop skill instead.

## Step 2: Classify the Flake Source

Identify which category applies. Most flaky tests fall into one of these:

| Category | Symptoms | Typical fix |
|---|---|---|
| **Timing** | Failures after slow ops, race conditions | Add explicit waits, remove `time.sleep`, mock time |
| **Ordering** | Fails when run after specific other tests | Isolate shared state, reset in teardown |
| **Shared state** | Database, filesystem, or global variable pollution | Use transactions, temp dirs, fixture isolation |
| **External system** | Network calls, API timeouts | Mock or stub the external call |
| **Random seed** | Non-deterministic sampling, shuffling | Pin the random seed in the test |
| **Concurrency** | Thread or process race conditions | Serialize access, use locks, avoid shared mutable state |

## Step 3: Apply Stabilization

Apply the fix appropriate to the category:

**Shared state:**
- Use `tmp_path` (pytest) or `tempfile.TemporaryDirectory` instead of hardcoded paths
- Wrap database operations in transactions with rollback in teardown
- Reset global state in a `yield` fixture

**Timing:**
- Replace `time.sleep(n)` with polling loops that wait for a condition
- Mock `time.time()` or `datetime.now()` for time-dependent assertions

**External system:**
- Use `unittest.mock.patch` or `respx` (for httpx) to stub outbound calls
- Return deterministic fixtures instead of live responses

**Random seed:**
```python
import random
random.seed(42)  # pin in fixture
```

## Step 4: Add Regression Coverage

Write a test that verifies the stabilization holds:
- Run the fixed test 10 times in CI to confirm consistent results
- Add a comment in the test noting the flake root cause

## Step 5: Document Findings

Update `spec/features/<work-id>-<slug>/test-results.md` (if this is tied to a work item):

```markdown
## Flaky Test Resolution — <date>
Test: <test name>
Root cause: <one sentence>
Fix: <one sentence>
Verification: passed 10/10 runs
```

## Completion Criteria

- [ ] Flake root cause identified and documented
- [ ] Fix applied (not suppressed or skipped)
- [ ] Test passes consistently for at least 5 consecutive runs
