---
name: work-item-status
description: This skill should be used when the user asks "what's the status of S-core-001", "where are we on this work item", "show me the status card for", "how far along is", or wants a concise summary of a specific work item's current state across all its documentation files.
version: 1.0.0
---

# Work Item Status

Produce a concise status card for a specific work item by reading all its documentation files and the live repo state.

## Setup

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or context.

Locate the work item folder: `spec/features/<work-id>-*/`

If the folder does not exist, report that the work item has no documentation yet and suggest the feature-kickoff skill.

## Read All Work Item Files

Read in parallel:
1. `feature.md` — goal, acceptance criteria, out of scope, open questions
2. `implementation.md` — approach, files changed, decisions
3. `test-plan.md` — test matrix, smoke scenarios
4. `test-results.md` — latest test and smoke results
5. `status.md` — current phase, blockers, history
6. `evidence/README.md` — smoke artifact paths

Also check git state scoped to this work item:
```bash
git log --oneline -5 -- spec/features/<work-id>-*/
git status --short -- spec/features/<work-id>-*/
```

## Produce the Status Card

```
## Work Item Status — <work-id>: <title>

Phase:      <from status.md>
Blockers:   <from status.md, or "none">

### Acceptance Criteria
- [x] <completed criterion>
- [ ] <pending criterion>

### Test Coverage
Test plan:    <present / missing>
Tests:        <written / not written>
Last run:     <result from test-results.md, or "not run">
Smoke:        <passed / failed / not run> — <artifact path if available>

### Documentation
implementation.md:  <filled / stub>
test-results.md:    <filled / stub>
evidence/:          <artifacts present / empty>

### Recent Activity
<last 3–5 git log entries for this work item folder>

### Open Questions
<from feature.md, or "none">

### Recommended Next Step
<one sentence — what should happen next based on current phase>
```

## Recommended Next Step Logic

| Phase | Recommended next step |
|---|---|
| Planning | Use the spec-linter skill to validate docs, then implementation-phase |
| Test Plan Written | Use the write-tests skill |
| Tests Written | Use the implement-feature skill |
| Implementation Complete | Use the ship-feature skill |
| Shipped | No action needed — work item is complete |
| Blocked | Address the listed blocker; use the debug-loop or failure-triage skill |
