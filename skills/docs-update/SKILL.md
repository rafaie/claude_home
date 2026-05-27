---
name: docs-update
description: This skill should be used when the user asks to "update docs after shipping", "update readme", "add changelog entry", "update user-facing documentation", or when a work item has been shipped and the project's user-visible documentation needs to reflect the changes.
version: 1.0.0
---

# Docs Update

Update user-facing documentation and the changelog after a work item is shipped.

## Setup

Identify the work item ID from user request or context.

Read:
1. `spec/features/<work-id>-<slug>/feature.md` — acceptance criteria and scope
2. `spec/features/<work-id>-<slug>/implementation.md` — files changed and decisions
3. `spec/features/<work-id>-<slug>/test-results.md` — smoke evidence
4. `README.md` — current user-facing documentation

## Determine What Changed

Identify which of the following changed:
- CLI flags, subcommands, or invocation syntax
- API endpoints, request/response schemas, or contracts
- Configuration files or environment variables
- Default behavior or output format
- Installed files, directories, or artifacts

Only update documentation for changes that affect users of the system. Internal refactors and test-only changes do not require doc updates.

## Update `README.md`

For each user-visible change:
- Update the quickstart or usage section to reflect new behavior
- Update any code examples that are now incorrect
- Add new examples for new features
- Remove or mark deprecated any features removed in this work item

Keep examples short and runnable.

## Update `spec/` Documentation

Update these files as applicable:
- `spec/docstrings.md` — if docstring standards changed
- Any spec file whose content is now stale due to this work item

## Add Changelog Entry

Append to `spec/changelog.md` (prepend to the top):

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

## Update Work Item Status

Update `spec/features/<work-id>-<slug>/status.md`:
- Note documentation status: `Docs: updated`

Update `spec/features/<work-id>-<slug>/implementation.md`:
- Add the documentation files changed to the files-changed list

## Handoff

Recommend the docs-index-refresh skill to keep `spec/index.md` current.
