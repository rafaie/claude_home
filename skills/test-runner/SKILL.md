---
name: test-runner
description: This skill should be used when the user asks to "run tests", "run the test suite", "verify tests pass", "check test status", "run quick checks", "run full checks", or wants to execute quality verification in either quick or full mode.
version: 2.0.0
---

# Test Runner

Run the project's quality checks in quick or full mode with `run_checks.py`, which reads the commands from
the project `CLAUDE.md`, runs them in order, stops at the first failure, validates smoke artifacts, and —
when asked to record — writes the results. Check results are only ever written by the script.

## Command Resolution

`run_checks.py` reads `## Commands` from the project `CLAUDE.md` and falls back to these defaults:

| Command | Default |
|---|---|
| test_quick | `uv run pytest -q` |
| test_full | `uv run pytest -q` |
| lint | `uv run ruff check .` |
| format | `uv run ruff format . --check` |
| typecheck | `uv run mypy src` |
| smoke | `uv run python scripts/smoke.py` |
| docstrings | not run unless configured |

A command set to `skip` (or `none`/`off`) is recorded as skipped — use that only for checks the project
genuinely does not have.

## Running

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_checks.py" --mode quick                  # between milestones
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_checks.py" --mode full --record <story>  # shipping milestones
```

| Mode | Steps, in order |
|---|---|
| quick (default) | format → lint → docstrings (if configured) → test_quick → smoke |
| full | format → lint → typecheck → docstrings (if configured) → test_full → smoke |

- `--record <story-id | run-id | folder>` writes `evidence/checks.json` (used by `story_state.py done`)
  and appends the result block to the story's `test-results.md`. Record whenever the result is evidence
  for a story: after implementing, after review fixes, and when shipping.
- `--keep-going` runs every step even after a failure (useful for triage); the overall result still fails.
- `--verify <story>` reports whether the recorded run passed and is still valid for the current code.
- Smoke counts as passed only if the run produced a new `artifacts/smoke/<run-id>/` with `summary.json`,
  `cases/` (at least one file), `stdout.txt`, `stderr.txt`, and `timing.json`.

Per-step logs are written to `artifacts/checks/<timestamp>/`.

## Failure Categorization

After any failure, categorize before recommending a path forward:

| Category | Symptom | Recommended next step |
|---|---|---|
| Deterministic | Same failure every run | debug-loop skill |
| Multiple failures | 3+ independent failures (re-run with `--keep-going` to see them all) | failure-triage skill |
| Flaky | Passes sometimes, fails sometimes | flaky-test-hunter skill |
| Smoke only | Unit/integration pass, smoke fails or artifacts incomplete | smoke-test skill for detailed triage |

## Output

Show the script's summary as-is (step results, smoke run, failure tails, overall). Do not restate a
result the script did not produce.

## Handoff

On pass: recommend the ship-feature skill if at a shipping milestone, or report clean and continue.
On fail: recommend the appropriate skill based on the failure category above.
