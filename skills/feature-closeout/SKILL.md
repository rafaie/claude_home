---
name: feature-closeout
description: This skill should be used when the user asks to "close out this feature", "verify feature is done", "feature-closeout", or wants a final verification pass on a work item. Note: this skill is deprecated — prefer the ship-feature skill for new work.
version: 1.0.0
---

# Feature Closeout (Deprecated)

> **Deprecated.** This skill exists for compatibility with older repositories. For new work, use the ship-feature skill instead, which provides the same functionality with improved structure.

Verify that a work item is fully complete and meets all exit criteria before marking it as done.

## Verification Checklist

Run through each item. Do not declare closeout complete until all pass.

### Acceptance Criteria
- [ ] All acceptance criteria from `feature.md` are satisfied and checked off
- [ ] No criterion marked as "deferred" without an explicit follow-up work item

### Quality Checks
- [ ] Full test suite passes (format, lint, typecheck, tests)
- [ ] Smoke tests pass with valid artifacts

### Smoke Artifacts
Verify these exist under `artifacts/smoke/<run-id>/`:
- [ ] `summary.json`
- [ ] At least one file under `cases/`
- [ ] `stdout.txt`
- [ ] `stderr.txt`
- [ ] `timing.json`

Record in `test-results.md`:
```
Smoke artifacts: artifacts/smoke/<run-id>/
Smoke summary: <one sentence — scenarios passed, any notable behavior>
```

### Documentation
- [ ] Run the adr-review skill if architectural decisions were made
- [ ] Run the docs-update skill if user-facing behavior changed
- [ ] Run the docs-index-refresh skill to update `spec/index.md`

### Work Item Files
Update:
- `test-results.md` — final check commands and outcomes
- `implementation.md` — files changed and decisions
- `status.md` — set phase to `Shipped`, remove all blockers

## Closeout Declaration

When all items above pass:

```
Work item <work-id> is ready to merge/release.
```

Only write this statement when all checks pass.

## Migration Note

To use the ship-feature skill instead:
- Ship-feature runs the full test-runner in full mode automatically
- Ship-feature validates smoke artifacts
- Ship-feature orchestrates ADR, docs, and index refresh
- Ship-feature produces a structured readiness summary
