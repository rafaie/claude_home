---
name: ship-feature
description: This skill should be used when the user asks to "ship this feature", "ship work item", "finalize and ship", "ready to ship", "complete this work item", or wants to validate everything is in order and declare a work item ready for merge or release.
version: 1.0.0
---

# Ship Feature

Validate completeness and readiness, then declare a work item ready to ship. Runs full checks, validates smoke artifacts, updates documentation, and produces a readiness summary.

## Setup

Identify the work item ID from user request or context.

Read:
1. `CLAUDE.md` — command overrides
2. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria
3. `spec/features/<work-id>-<slug>/test-plan.md` — smoke scenarios and artifact expectations
4. `spec/features/<work-id>-<slug>/status.md` — current phase

## Pre-Execution Verification

Confirm the feature.md includes and is complete:
- [ ] Acceptance criteria present and all checked off (no unchecked items)
- [ ] Definition of Done section present with all items checked off
- [ ] At least one smoke scenario in test-plan.md
- [ ] Fixture definitions for smoke scenarios
- [ ] Docstring requirements noted for any API changes

If any item is missing or unchecked, use the spec-linter skill to identify gaps before proceeding. Do not proceed to Step 1 if any acceptance criterion or DoD item is unchecked.

## Step 1: Run Full Test Suite

Use the test-runner skill in full mode. Full mode includes format, lint, typecheck, full tests, and smoke. Do not run smoke-test separately unless artifacts from a prior run are missing or stale.

Gate: all checks pass before continuing.

## Step 2: Validate Smoke Artifacts

Verify these artifacts exist and are non-empty:
- `artifacts/smoke/<run-id>/summary.json`
- `artifacts/smoke/<run-id>/cases/` (at least one file)
- `artifacts/smoke/<run-id>/stdout.txt`
- `artifacts/smoke/<run-id>/stderr.txt`
- `artifacts/smoke/<run-id>/timing.json`

Record artifact paths in `spec/features/<work-id>-<slug>/test-results.md`.

## Step 3: Architecture Review

Use the adr-review skill if any of the following occurred:
- New external dependency added
- Significant design choice made
- New integration boundary introduced
- Existing interface changed incompatibly

Skip if no architectural decisions were made.

## Step 4: Documentation

Use the docs-update skill if any user-facing behavior changed:
- CLI flags or output format changed
- API contract changed
- README quickstart is affected

Use the docs-index-refresh skill to update `spec/index.md` to reflect the completed status.

## Step 5: Update Work Item Files

**`test-results.md`** — record final check commands and outcomes, artifact paths.
**`implementation.md`** — record files changed, decisions made.
**`status.md`** — set phase to `Shipped`. Remove all blockers.

## Step 6: Readiness Summary

Output:

```
## Ship Feature — <work-id>

Full checks:    ✓ format, lint, types, tests
Smoke:          ✓ <n> scenarios, artifacts at artifacts/smoke/<run-id>/
Docstrings:     ✓ / n/a
ADR:            ✓ / n/a
Docs:           ✓ / n/a

Ready to ship.
```

Only write "Ready to ship" when all required checks pass. If anything is blocked, list what remains.
