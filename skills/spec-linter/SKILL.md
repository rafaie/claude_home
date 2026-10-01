---
name: spec-linter
description: This skill should be used when the user asks to "review this spec", "is the spec ready", "is this story ready", "check the definition of ready", "check work item docs", "lint the spec for", "validate the feature docs", or wants to verify that a story's (work item's) documentation is complete and testable before implementation begins.
version: 2.0.0
---

# Spec Linter

Check a story against its **Definition of Ready** and the completeness of its documentation folder.
On pass, move the story from `Backlog` to `Ready`. Model and statuses:
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the story ID from user request or context. Resolve the folder:
- `spec/stories/<story-id>-<slug>/` with `story.md`
- legacy `spec/features/<story-id>-<slug>/` with `feature.md` (mention that the project can be migrated)
- oldest legacy `spec/<story-id>.md` — lint what exists and recommend feature-kickoff

## Validation Checklist

Report pass (✓) or fail (✗) with a specific remediation for each failure.

### `story.md` — Definition of Ready
- [ ] Header has Area, Priority, and Depends on (Epic may be `none`)
- [ ] Story statement names who benefits and the observable outcome (not a task description)
- [ ] 2–6 acceptance criteria, each with an ID (`AC-1`, `AC-2`, …) and Given/When/Then wording
- [ ] Each AC is observable and machine-verifiable — not an internal detail or "should be fast"
- [ ] At least one AC covers an error path, invalid input, or boundary
- [ ] Every story in Depends on is `Done`, or the dependency is explicitly marked non-blocking
- [ ] Out of Scope present (even if "none")
- [ ] No open question blocks implementation
- [ ] Definition of Done present and includes the independent review gate

Legacy `feature.md` without AC IDs: fail with the remediation "number the criteria AC-1…n (qa-intake can
do this)" — the test plan and the review reference AC IDs.

### `test-plan.md` (only if already populated)
- [ ] Every AC ID appears in the Test Matrix
- [ ] At least one smoke scenario with command, input fixture, expected artifacts, pass condition
- [ ] Mock strategy documented for external dependencies

### `implementation.md`
- [ ] Tasks section present (≤ ~5 tasks; more suggests the story should be split)
- [ ] No contradictions with `story.md`

### `status.md`
- [ ] `**Status:**`, `**Blockers:**`, `**Base commit:**`, `**Review:**` lines present

### `evidence/README.md`
- [ ] File exists (stub is acceptable)

### Docstring coverage
- [ ] For API changes: docstring requirements noted in `story.md` or `implementation.md`, or explicitly
      marked not required

## On Pass

If the story's status is `Backlog`, record the transition:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/story_state.py" ready <story-id>
```

It re-checks the mechanical parts of the Definition of Ready (at least two numbered ACs; every dependency
Done or Split), then ticks the Definition of Ready, sets `**Status:** Ready`, adds the History line, and
updates the backlog and epic rows. If a dependency is not Done but the user has explicitly agreed it is
non-blocking, pass `--allow-dep <ID>`; never pass it on your own judgment. If it refuses, report the
reason as a lint failure.

## Output Format

```
## Spec Linter — <story-id>

Definition of Ready:  ✓ / ✗ <issue>
test-plan.md:         ✓ / n/a / ✗ <issue>
implementation.md:    ✓ / ✗ <issue>
status.md:            ✓ / ✗ <issue>
evidence/:            ✓ / ✗ <issue>
docstrings:           ✓ / n/a / ✗ <issue>

Overall: READY / NOT READY — <n> issues found

<remediation list>
```

## Handoff

- **Ready:** recommend the implementation-phase skill.
- **Not ready:** list specific fixes; recommend the qa-intake skill for AC problems or the
  feature-slicer skill if the story is too large, then re-run the spec-linter skill.
