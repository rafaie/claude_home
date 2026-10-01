# Independent Review Rubric

Shared by the independent-review skill, the `independent-reviewer` agent, and `scripts/gate_check.py`.

## Severity

| Severity | Blocks the gate? | Use when |
|---|---|---|
| **high** | Yes | An AC is not met or is met only on the happy path the test happens to use; wrong results, data loss or corruption; a security weakness (injection, secrets in code/logs, missing authz, unsafe deserialization); crash or hang on realistic input; a test that passes without exercising the behavior it claims (false green); build or full checks broken |
| **medium** | Yes | An AC is only partially met; an edge case named in `story.md` is unhandled; an AC has no automated test; realistic error path unhandled or swallowed; an externally visible contract (CLI, API, schema, config) changed without docs; a violation of the project `CLAUDE.md` constraints; a likely regression in code the diff touches |
| **low** | No — becomes a backlog follow-up | Maintainability, naming, small duplication, missing docstring required by the project standard, minor inefficiency, test readability |
| **info** | No | Observations and suggestions with no defect |

When unsure between two severities, pick the higher one **only** if you can state a concrete failure
scenario; otherwise pick the lower one.

## Evidence rules

Every high or medium finding must include:

- `file` and `line` in the reviewed commit
- `failure_scenario` — concrete input or state → wrong output, crash, or exposure
- `ac` — the AC it violates, or `null` if it is not tied to one

A finding without a concrete, checkable failure scenario is at most **low**. Claims in
`implementation.md` or `test-results.md` are statements to verify, never evidence.
A knowledge-graph report (e.g. `graphify-out/GRAPH_REPORT.md`) is a map for navigation, never evidence —
cite the actual source line.

## Categories

`correctness` · `security` · `error-handling` · `test-gap` · `false-green` · `contract` · `regression` ·
`performance` · `maintainability` · `docs` · `constraint`

## Finding lifecycle

| Status | Set by | Meaning |
|---|---|---|
| `open` | reviewer | Defect present in the reviewed commit |
| `fixed` | a later reviewer round | Reviewer verified the fix in the new commit |
| `deferred` | reviewer (low/info only) | Not blocking; tracked as a follow-up |

Waivers are **not** a finding status. Only the user can waive a high or medium finding, and the waiver is
recorded in `reviews/waivers.json`, never by editing a review file.

Finding IDs (`F1`, `F2`, …) are stable across rounds. A re-review keeps prior IDs and continues numbering
for new findings.

### Severity changes across rounds

A later round may change a carried-forward finding's severity only with new evidence:

- **Raising** severity is always allowed. Explain why in `severity_note`.
- **Lowering** severity requires `severity_note` stating the new evidence (e.g. the failure path turned out
  to be unreachable). `gate_check.py` **ignores an unexplained downgrade**: the finding keeps its earlier
  severity for the gate, in this and every later round.
- `severity_note` is `null` when the severity is unchanged.

Every severity change is listed in the gate output, so the user can see when two reviewers disagreed.
`deferred` is only valid for low/info findings — a high or medium finding marked `deferred` counts as open.

## Verdict

`PASS` if and only if, after applying waivers:

- no finding with severity `high` or `medium` has status `open`, and
- no AC has coverage `not_met` or `partial`.

Otherwise `FAIL`. `gate_check.py` recomputes the verdict from the findings — the `verdict` field is
informational.

## Freshness

A review is pinned to its `head` commit. It stays current while the only changes since `head` are under
`spec/`, `artifacts/`, `graphify-out/`, or to Markdown files. Any other change — committed or not —
makes it stale, and the gate fails until a new round reviews the new code.

**Generated caches are not changes.** Untracked files created by running tests or linters are ignored
everywhere the working tree is checked (review preconditions, the reviewer's target check, freshness):
anything under `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.tox/`, `.nox/`,
`.venv/`, `node_modules/`, `htmlcov/`, `.hypothesis/`, `.cache/`, and `*.pyc`, `*.pyo`, `.coverage`.

The **working tree matches the target** when `HEAD` is the reviewed commit and `git status --porcelain`
shows nothing except the allowed paths above and generated caches.

## `r<N>.json` schema (version 1)

```json
{
  "schema": 1,
  "target": "S-auth-005",
  "scope": "story",
  "round": 2,
  "reviewer": "subagent",
  "base": "<full sha>",
  "head": "<full sha>",
  "reviewed_at": "2026-09-30T14:02:00Z",
  "verdict": "PASS",
  "summary": "One-paragraph assessment.",
  "ac_coverage": [
    { "ac": "AC-1", "status": "met", "evidence": "tests/test_token.py::test_expiry_utc; src/auth/token.py:88" }
  ],
  "checks_run": [
    { "cmd": "uv run pytest -q", "result": "pass", "notes": "142 passed" }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "high",
      "category": "correctness",
      "status": "fixed",
      "severity_note": null,
      "title": "Token expiry compared in local time",
      "file": "src/auth/token.py",
      "line": 88,
      "ac": "AC-2",
      "failure_scenario": "Server in UTC+2: token with exp=now+1h is accepted for 3h.",
      "evidence": "datetime.now() vs exp parsed as UTC",
      "recommendation": "Use datetime.now(timezone.utc).",
      "first_seen_round": 1
    }
  ]
}
```

Field values:

- `scope`: `story` | `epic` | `range`
- `reviewer`: `subagent` | `subagent-fallback` | `headless` | `codex`

The machine-checkable form of this schema is `review-schema.json` (all fields required; `file`, `line`,
`ac`, and `severity_note` may be `null`).
- `ac_coverage[].status`: `met` | `partial` | `not_met` | `unverifiable`
- `checks_run[].result`: `pass` | `fail` | `skipped`

## `waivers.json`

```json
[
  {
    "finding": "F4",
    "round": 2,
    "reason": "Accepted risk: legacy clients only; tracked in S-auth-019",
    "approved_by": "user",
    "date": "2026-09-30"
  }
]
```

A waiver applies to its finding ID in every later round. Waivers may cover `ac` entries too, using
`"finding": "AC-3"`.
