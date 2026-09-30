---
name: work-item-status
description: This skill should be used when the user asks "what's the status of S-core-001", "where are we on this story", "where are we on this work item", "status of epic E-03", "show me the status card for", "how far along is", or wants a concise summary of a specific story's (work item's) or epic's current state across all its documentation files.
version: 2.0.0
---

# Story Status

Produce a concise status card for a story — or a rollup for an epic — from its documentation files, its
reviews, and the live repo state. Model and statuses: `${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the ID from the user's request or context: story `S-<area>-<nnn>` or epic `E-<nn>`.

Locate the folder: `spec/stories/<story-id>-*/` (legacy `spec/features/<story-id>-*/` — map its
`Current phase` to a status per hierarchy.md), or `spec/epics/<epic-id>-*/`.

If the folder does not exist, report that it has no documentation yet and suggest the feature-kickoff skill.

## Story: Read All Files

Read in parallel:
1. `story.md` — story statement, ACs, epic, dependencies, open questions
2. `implementation.md` — tasks, approach, files changed, decisions
3. `test-plan.md` — test matrix, smoke scenarios
4. `test-results.md` — latest test and smoke results
5. `status.md` — status, blockers, base commit, review line, history
6. `evidence/README.md` — smoke artifact paths

If `reviews/` exists, run the gate:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py" <story-id>
```

Check git state:
```bash
git log --oneline -5 -- spec/stories/<story-id>-*/
git log --oneline <base-commit>..HEAD      # if a base commit is recorded
git status --short
```

## Story: Status Card

```
## Story Status — <story-id>: <title>

Status:     <Backlog | Ready | In Progress | In Review | Done | Split>
Epic:       <E-nn or none> · Priority: <P> · Depends on: <ids, with their status>
Blockers:   <from status.md, or "none">

### Acceptance Criteria
- [x] AC-1 — <short text>
- [ ] AC-2 — <short text>

### Progress
Tasks:        <done>/<total> from implementation.md
Test plan:    <every AC covered / missing ACs: …>
Last run:     <result from test-results.md, or "not run">
Smoke:        <passed / failed / not run> — <artifact path if available>
Commits:      <n> since base <short-sha>

### Review
Gate:         <PASS | FAIL | STALE | not reviewed> — r<N>, <h>H/<m>M/<l>L open
Waived:       <ids or none>

### Recent Activity
<last 3–5 git log entries for this story>

### Open Questions
<from story.md, or "none">

### Recommended Next Step
<one sentence>
```

## Recommended Next Step Logic

| Status / state | Recommended next step |
|---|---|
| Backlog | qa-intake if ACs are unclear; otherwise spec-linter (Definition of Ready) |
| Ready | implementation-phase |
| In Progress, no test plan | implementation-phase (resumes at test-plan) |
| In Progress, tests written | implementation-phase (resumes at implement) |
| In Progress, all ACs met, uncommitted | implementation-phase (commit, then review) |
| In Review, gate FAIL | fix open findings, commit, re-run independent-review |
| In Review, gate ESCALATE | ask the user: another round, waive, split, or stop |
| In Review, gate STALE | independent-review (new round for the changed code) |
| In Review, gate PASS | ship-feature |
| Done | none — story complete |
| Blockers present | address the blocker; debug-loop, failure-triage, or feature-slicer for "needs split" |

## Epic: Rollup Card

Read `epic.md`, then each member story's `status.md` (and gate result if reviewed).

```
## Epic Status — <epic-id>: <title>

Status:    <Backlog | In Progress | Done>   <k>/<n> stories Done
Outcome:   <one line>

| Story | Status | Review | Priority | Depends on |
|---|---|---|---|---|
| S-auth-004 | Done | r1 PASS | P1 | none |
| S-auth-005 | In Review | r2 FAIL (1H) | P1 | S-auth-004 |

Integration review:  <not run | r<N> PASS/FAIL>
Next:                <the first story, in dependency order, that is not Done — and its next step;
                      or independent-review (scope epic) when all stories are Done>
```
