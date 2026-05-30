---
name: docs-update
description: This skill should be used when the user asks to "update docs after shipping", "update readme", "add changelog entry", "update user-facing documentation", "refresh the spec index", "update spec/index.md", or when a work item has been shipped and project documentation needs to reflect the changes.
version: 2.0.0
---

# Docs Update

Update user-facing documentation, the changelog, and `spec/index.md` after a work item is shipped. Combines what was previously split between docs-update and docs-index-refresh.

## Setup

Identify the work item ID from user request or context.

Read:
1. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria and scope
2. `spec/features/<work-id>-<slug>/implementation.md` — files changed and decisions
3. `spec/features/<work-id>-<slug>/test-results.md` — smoke evidence
4. `README.md` — current user-facing documentation
5. `spec/index.md` — current navigation hub

## Part 1: User-Facing Documentation

### Determine what changed

Only update docs for changes that affect users of the system. Internal refactors and test-only changes do not require doc updates.

Identify which of the following changed:
- CLI flags, subcommands, or invocation syntax
- API endpoints, request/response schemas, or contracts
- Configuration files or environment variables
- Default behavior or output format
- Installed files, directories, or artifacts

### Update `README.md`

For each user-visible change:
- Update the quickstart or usage section to reflect new behavior
- Update any code examples that are now incorrect
- Add new examples for new features
- Remove or mark deprecated any features removed in this work item

Keep examples short and runnable.

### Update other `spec/` documentation

Update these files as applicable:
- `spec/docstrings.md` — if docstring standards changed
- Any other spec file whose content is now stale due to this work item

### Add changelog entry

Prepend to `spec/changelog.md`:

```markdown
## <version or date> — <Work Item ID>

### Added
- <new capability>

### Changed
- <modified behavior>

### Fixed
- <bug corrected>

### Deprecated
- <feature marked for removal>
```

Use only the sections that apply. Omit empty sections.

## Part 2: Refresh `spec/index.md`

The index is a living navigation hub, not a one-time document. Prioritize functional links, current state, and concise descriptions.

Scan all `spec/features/*/status.md` files and `spec/decisions/` before writing.

Rebuild or update these sections:

### Project Summary
One paragraph: goal, current maturity, key constraints.

### Current Status
3–5 bullet points reflecting today's state — working, in progress, blocked.

### Work Items

```markdown
## In Progress
- [S-core-001 — Title](features/S-core-001-slug/feature.md) — Phase: Implementation

## Planned
- [S-core-002 — Title](features/S-core-002-slug/feature.md) — P1

## Shipped
- [S-core-000 — Title](features/S-core-000-slug/feature.md) — ✓
```

### Decisions
List all ADRs in `spec/decisions/`.

### Architecture
Link to `spec/architecture.md` if it exists.

### Quick Links
Link to `spec/brief.md`, `spec/backlog.md`, `spec/changelog.md`.

### Verification
Before writing, verify every link target exists. Mark broken links `(pending)` rather than leaving them dead.

## Part 3: Update Work Item Status

Update `spec/features/<work-id>-<slug>/status.md`:
- Note documentation status: `Docs: updated`

Update `spec/features/<work-id>-<slug>/implementation.md`:
- Add documentation files changed to the files-changed list

## Handoff

Report what was updated:
- README sections changed
- Changelog entry added
- Index sections rebuilt
- Status file updated

No further skill recommended — docs are now current.
