---
name: spec-linter
description: This skill should be used when the user asks to "review this spec", "is the spec ready", "check work item docs", "lint the spec for", "validate the feature docs", or wants to verify that a work item's documentation is complete and testable before implementation begins.
version: 1.0.0
---

# Spec Linter

Review a work item's documentation folder for completeness, clarity, and testability. Identifies gaps before implementation begins, saving debugging time later.

## Setup

Identify the work item ID from user request or context.

Locate the work item folder:
- New format: `spec/features/<work-id>-<slug>/`
- Legacy format: `spec/<work-id>.md` (handle gracefully if folder structure is absent)

## Validation Checklist

Run through each check. Report pass (✓) or fail (✗) with a specific remediation for each failure.

### `feature.md`
- [ ] Goal is present and states observable outcome (not just a task description)
- [ ] Acceptance criteria exist (at least two items)
- [ ] Each criterion is testable — it describes a verifiable behavior, not an internal implementation detail
- [ ] Out of scope section is present (even if empty with "none")
- [ ] No open questions that block implementation

### `test-plan.md`
- [ ] At least one test case per acceptance criterion
- [ ] At least one smoke scenario defined
- [ ] Each smoke scenario includes: entry point command, input fixture, expected artifacts, pass condition
- [ ] Mock strategy documented for external dependencies

### `implementation.md`
- [ ] Approach section is present (stub is acceptable at this stage)
- [ ] No contradictions with `feature.md`

### `status.md`
- [ ] Current phase is set
- [ ] Blockers section present (even if "none")

### `evidence/README.md`
- [ ] File exists (stub is acceptable)

### Docstring coverage
- [ ] For any API changes: docstring requirements noted in `feature.md` or `implementation.md`
- [ ] Explicit acknowledgment if docstrings are not required for this work item

## Output Format

```
## Spec Linter — <work-id>

feature.md:        ✓ / ✗ <issue>
test-plan.md:      ✓ / ✗ <issue>
implementation.md: ✓ / ✗ <issue>
status.md:         ✓ / ✗ <issue>
evidence/:         ✓ / ✗ <issue>
docstrings:        ✓ / n/a / ✗ <issue>

Overall: PASS / FAIL — <n> issues found

<remediation list>
```

## Handoff

On pass: recommend the implementation-phase skill.
On fail: list specific fixes needed and recommend re-running the spec-linter skill after addressing them.
