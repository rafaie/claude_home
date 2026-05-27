---
name: test-runner
description: This skill should be used when the user asks to "run tests", "run the test suite", "verify tests pass", "check test status", "run quick checks", "run full checks", or wants to execute quality verification in either quick or full mode.
version: 1.0.0
---

# Test Runner

Execute quality checks in quick or full mode. Treats smoke testing as a distinct stage separate from unit and integration tests.

## Command Resolution

Read `CLAUDE.md` for command overrides. Fall back to defaults:

| Command | Default |
|---|---|
| test_quick | `uv run pytest -q` |
| test_full | `uv run pytest -q` |
| lint | `uv run ruff check .` |
| format | `uv run ruff format . --check` |
| typecheck | `uv run mypy src` |
| smoke | `uv run python scripts/smoke.py` |

## Quick Mode

Run when making incremental changes between milestones:

1. **Format check** — `format` command
2. **Lint** — `lint` command
3. **Docstring validation** — `docstrings` command, if configured
4. **Scoped tests** — `test_quick` command
5. **Smoke** — `smoke` command with the current work item scoped if supported

Quick mode is the default. Skip to full mode when explicitly requested or at shipping milestones.

## Full Mode

Run at shipping milestones (before ship-feature, before release):

1. **Format check**
2. **Lint**
3. **Type check** — `typecheck` command
4. **Docstring validation** — if configured
5. **Full test suite** — `test_full` command
6. **Smoke** — full run without scope restriction

## Failure Categorization

After any failure, categorize before recommending a path forward:

| Category | Symptom | Recommended next step |
|---|---|---|
| Deterministic | Same failure every run | debug-loop skill |
| Multiple failures | 3+ independent failures | failure-triage skill |
| Flaky | Passes sometimes, fails sometimes | flaky-test-hunter skill |
| Smoke only | Unit/integration pass, smoke fails | smoke-test skill for detailed triage |

## Output Format

```
## Test Runner — <mode> mode

Format:    ✓ / ✗
Lint:      ✓ / ✗
Types:     ✓ / ✗ (full mode only)
Tests:     ✓ <n> passed / ✗ <n> failed
Smoke:     ✓ / ✗

Overall:   PASS / FAIL

<failure details if any>
```

## Handoff

On pass: recommend the ship-feature skill if at a shipping milestone, or report clean and continue.
On fail: recommend the appropriate skill based on failure category above.
