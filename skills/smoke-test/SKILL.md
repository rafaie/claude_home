---
name: smoke-test
description: This skill should be used when the user asks to "run smoke tests", "smoke test this work item", "validate with smoke", "run the smoke harness", or wants to execute smoke tests and capture structured artifacts for a work item.
version: 1.0.0
---

# Smoke Test

Execute smoke tests for a work item and capture structured artifacts. Smoke tests run real subprocesses against actual entry points — not mocked calls.

## Setup

Identify the work item ID from user request or context.

Read:
1. `CLAUDE.md` — `smoke` command override
2. `spec/features/<work-id>-<slug>/test-plan.md` — smoke scenarios

Resolve the smoke command:
1. Use the `smoke` command from project `CLAUDE.md` if present
2. Fall back to `uv run python scripts/smoke.py`

## Execution

Scope the smoke run to the work item when supported:
```bash
<smoke-command> --work-item <work-id>
```

Run without `--work-item` for full smoke if scoping is not supported.

## Required Artifacts

After a successful run, verify all of the following exist under `artifacts/smoke/<run-id>/`:

| Artifact | Description |
|---|---|
| `summary.json` | Overall pass/fail counts, run metadata |
| `cases/` | Per-scenario result files |
| `stdout.txt` | Full standard output |
| `stderr.txt` | Full standard error |
| `timing.json` | Per-scenario execution times |

If any artifact is missing, the run is incomplete — do not treat it as a pass.

## Failure Classification

Map failures to one of these 18 buckets and report the exit code:

| Exit Code | Category |
|---|---|
| 10 | Import or startup error |
| 11 | Configuration missing |
| 12 | Credential missing |
| 13 | Entry point not found |
| 14 | Fixture not found |
| 20 | Schema validation failure |
| 21 | Output format mismatch |
| 22 | Unexpected output content |
| 30 | Subprocess timeout |
| 31 | Budget exceeded |
| 32 | Rate limit hit |
| 40 | External API error |
| 41 | Network unreachable |
| 50 | Assertion failure |
| 51 | Missing expected artifact |
| 52 | Extra unexpected artifact |
| 60 | Flaky — intermittent failure |
| 99 | Unknown error |

## Evidence Recording

Write artifact paths and a brief summary to `spec/features/<work-id>-<slug>/test-results.md`:

```markdown
## Smoke Run — <date>
Run ID: <run-id>
Command: `<command>`
Result: <pass/fail>, <n> scenarios

Artifacts:
- summary.json: artifacts/smoke/<run-id>/summary.json
- stdout: artifacts/smoke/<run-id>/stdout.txt

Summary: <1–2 sentence description of what passed/failed>
```

## Handoff

On pass: recommend the ship-feature skill.
On deterministic failure: recommend the debug-loop skill.
On flaky failure (exit 60): recommend the flaky-test-hunter skill.
