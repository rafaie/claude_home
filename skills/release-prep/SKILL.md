---
name: release-prep
description: This skill should be used when the user asks to "prepare release", "run release checks", "ready to release", "prep for release", "generate release notes", or wants to validate that all quality gates pass and documentation is current before cutting a release.
version: 1.1.0
---

# Release Prep

Run all quality gates and prepare documentation before cutting a release.

## Command Resolution

`run_checks.py` reads the commands from the project `CLAUDE.md` (`## Commands`) and falls back to the
defaults listed in the test-runner skill.

## Quality Gate Sequence

Run all five gates with one command — it runs them in this order, stops at the first failure, and
validates the smoke artifacts:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_checks.py" --mode full
```

Report its output as-is; never restate a result it did not produce. The gates it runs, and what each
failure means:

### Gate 1: Formatting
All files must be correctly formatted. Run the formatter (without `--check`) if there are formatting issues, then re-check.

### Gate 2: Linting
Zero lint errors. Warnings are acceptable if they were pre-existing.

### Gate 3: Type Checking
Zero type errors. New errors introduced since the last release must be fixed.

### Gate 4: Full Test Suite
All tests pass. No skipped tests that were previously passing.

### Gate 5: Smoke Tests
All smoke scenarios pass, and the run produced complete artifacts (`summary.json`, `cases/`, `stdout.txt`,
`stderr.txt`, `timing.json`). Smoke is a required gate — release preparation cannot complete without it.

## Story Status Check

Before running quality gates, actively scan all story status files:

```bash
grep -rE "^\*\*(Status|Current phase):\*\*" spec/stories/*/status.md spec/features/*/status.md 2>/dev/null
```

Flag any story whose status is `In Progress` or `In Review` (legacy phases: map them per
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`). An in-flight story means the release may be premature. For
each flagged story, use the work-item-status skill to assess whether it should be finished, deferred, or
explicitly excluded from this release.

For every `Done` story, confirm it passed its review gate when it was shipped:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py" <story-id> --skip-freshness
```

(`--skip-freshness` because later stories legitimately changed the code after this one was reviewed.)
A Done story with `NO_REVIEW` or `FAIL` must be reviewed or explicitly accepted by the user before release.

Do not proceed to quality gates until all in-flight stories are either Done or explicitly deferred with a
recorded reason in their `status.md`.

## Documentation Verification

After all gates pass:

- [ ] `README.md` quickstart matches current behavior
- [ ] `spec/changelog.md` has an entry for this release
- [ ] `spec/index.md` is current (run the docs-update skill if stale)
- [ ] All in-flight stories resolved (Done or deferred with reason)
- [ ] Every Done story passed its review gate (or the user accepted the exception)

## Release Notes

Generate a release summary from `spec/changelog.md`:

```markdown
## Release <version> — <date>

### Highlights
<2–3 bullet points summarizing the most significant changes>

### Full Changelog
<copy the latest changelog section>

### Quality Gates
- Format: ✓
- Lint: ✓
- Types: ✓
- Tests: ✓ (<n> passed)
- Smoke: ✓ (<n> scenarios)
- Reviews: ✓ (<n> stories, all gates passed)
```

## Completion Declaration

Only write "Release is ready" when all five quality gates pass and documentation is verified.

If any gate fails, list what must be fixed before re-running release prep.
