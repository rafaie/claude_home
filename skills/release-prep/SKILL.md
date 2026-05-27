---
name: release-prep
description: This skill should be used when the user asks to "prepare release", "run release checks", "ready to release", "prep for release", "generate release notes", or wants to validate that all quality gates pass and documentation is current before cutting a release.
version: 1.0.0
---

# Release Prep

Run all quality gates and prepare documentation before cutting a release.

## Command Resolution

Read `CLAUDE.md` for command overrides. Defaults:
- Format: `uv run ruff format . --check`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src`
- Test (full): `uv run pytest -q`
- Smoke: `uv run python scripts/smoke.py`

## Quality Gate Sequence

Run checks in this order. Stop and report if any gate fails — do not skip ahead.

### Gate 1: Formatting
```bash
<format command>
```
All files must be correctly formatted. Run the formatter (without `--check`) if there are formatting issues, then re-check.

### Gate 2: Linting
```bash
<lint command>
```
Zero lint errors. Warnings are acceptable if they were pre-existing.

### Gate 3: Type Checking
```bash
<typecheck command>
```
Zero type errors. New errors introduced since the last release must be fixed.

### Gate 4: Full Test Suite
```bash
<test_full command>
```
All tests pass. No skipped tests that were previously passing.

### Gate 5: Smoke Tests
```bash
<smoke command>
```
All smoke scenarios pass. Artifacts produced and valid. Smoke is a required gate — release preparation cannot complete without it.

## Work Item Status Check

Before running quality gates, actively scan all work item status files:

```bash
grep -r "Current phase:" spec/features/*/status.md
```

Flag any item whose phase is not `Shipped` or `Planned`. A work item stuck at "Implementation Complete", "Testing", or any in-flight phase means the release may be premature. For each flagged item, use the work-item-status skill to assess whether it should be shipped, deferred, or explicitly excluded from this release.

Do not proceed to quality gates until all in-flight items are either shipped or explicitly deferred with a recorded reason in their `status.md`.

## Documentation Verification

After all gates pass:

- [ ] `README.md` quickstart matches current behavior
- [ ] `spec/changelog.md` has an entry for this release
- [ ] `spec/index.md` is current (run the docs-index-refresh skill if stale)
- [ ] All in-flight work items resolved (shipped or deferred with reason)

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
```

## Completion Declaration

Only write "Release is ready" when all five quality gates pass and documentation is verified.

If any gate fails, list what must be fixed before re-running release prep.
