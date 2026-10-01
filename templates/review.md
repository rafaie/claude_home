# Review r{{ROUND}} — {{TARGET}}

**Verdict:** {{PASS | FAIL}}
**Scope:** {{story | epic | range}} · **Reviewer:** {{subagent | headless | codex}} · **Date:** {{date}}
**Range:** `{{base-short}}..{{head-short}}`
**Open:** {{h}} high · {{m}} medium · {{l}} low

## Summary
{{one paragraph — overall assessment, biggest risk}}

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 | met / partial / not_met / unverifiable | {{test and source references}} |

## Findings

### F1 — {{title}} ({{severity}}, {{category}}, {{status}})
- **Where:** `{{file}}:{{line}}` · **AC:** {{AC-n or none}}
- **Severity change:** {{previous → current — the new evidence; omit this line when unchanged}}
- **Failure scenario:** {{concrete input/state → wrong result}}
- **Evidence:** {{what in the code shows this}}
- **Recommendation:** {{smallest fix}}

## Previous Findings
{{for round ≥ 2: table of prior IDs with fixed / still open — or "n/a (round 1)"}}

## Checks Run

| Command | Result | Notes |
|---|---|---|
| `{{command}}` | pass / fail / skipped | {{notes}} |
