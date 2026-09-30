---
name: docs-update
description: This skill should be used when the user asks to "update docs after shipping", "update readme", "add changelog entry", "update user-facing documentation", "refresh the spec index", "update spec/index.md", or when a work item has been shipped and project documentation needs to reflect the changes.
version: 2.0.0
---

# Docs Update

Update user-facing documentation, the changelog, and `spec/index.md` after a story is shipped. Combines what was previously split between docs-update and docs-index-refresh.

## Setup

Identify the story ID from user request or context.

Read:
1. `spec/stories/<story-id>-<slug>/story.md` — acceptance criteria and scope
2. `spec/stories/<story-id>-<slug>/implementation.md` — files changed and decisions
3. `spec/stories/<story-id>-<slug>/test-results.md` — smoke evidence
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
- Remove or mark deprecated any features removed in this story

Keep examples short and runnable.

### Update other `spec/` documentation

Update these files as applicable:
- `spec/docstrings.md` — if docstring standards changed
- Any other spec file whose content is now stale due to this story

### Add changelog entry

Prepend to `spec/changelog.md`:

```markdown
## <version or date> — <Story ID>

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

Scan all `spec/epics/*/epic.md`, `spec/stories/*/status.md` (and legacy `spec/features/*/status.md`),
and `spec/decisions/` before writing.

Rebuild or update these sections:

### Project Summary
One paragraph: goal, current maturity, key constraints.

### Current Status
3–5 bullet points reflecting today's state — working, in progress, blocked.

### Stories

Group stories by epic, then standalone stories. Show each story's status and review state:

```markdown
## [E-03 — Auth hardening](epics/E-03-auth-hardening/epic.md) — In Progress (2/5 Done)
- [S-auth-004 — Title](stories/S-auth-004-slug/story.md) — Done ✓ (r1 PASS)
- [S-auth-005 — Title](stories/S-auth-005-slug/story.md) — In Review (r2 FAIL: 1H)
- [S-auth-006 — Title](stories/S-auth-006-slug/story.md) — Ready · P1

## Standalone stories
- [S-cli-002 — Title](stories/S-cli-002-slug/story.md) — Backlog · P2
```

### Decisions
List all ADRs in `spec/decisions/`.

### Architecture
Link to `spec/architecture.md` if it exists.

### Quick Links
Link to `spec/brief.md`, `spec/backlog.md`, `spec/changelog.md`.

### Verification
Before writing, verify every link target exists. Mark broken links `(pending)` rather than leaving them dead.

## Part 3: Update Story Status

Update `spec/stories/<story-id>-<slug>/status.md`:
- Note documentation status: `Docs: updated`

Update `spec/stories/<story-id>-<slug>/implementation.md`:
- Add documentation files changed to the files-changed list

## Handoff

Report what was updated:
- README sections changed
- Changelog entry added
- Index sections rebuilt
- Status file updated

No further skill recommended — docs are now current.
