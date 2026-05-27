---
name: docs-index-refresh
description: This skill should be used when the user asks to "refresh the spec index", "update spec/index.md", "sync the index", "the index is out of date", or after shipping or documenting a work item when the navigation hub needs to reflect current project state.
version: 1.0.0
---

# Docs Index Refresh

Maintain `spec/index.md` as a living navigation hub that accurately reflects the current state of the project.

## Treat the Index as a Living Artifact

`spec/index.md` is not a one-time document — it is the primary entry point into the project specification. Prioritize:
- Functional links over complete coverage
- Current state over historical accuracy
- Concise descriptions over exhaustive detail

## Setup

Read all of the following before writing:
1. `spec/index.md` — current state
2. `spec/brief.md` — project goal and scope
3. `spec/backlog.md` — all work items and their statuses
4. `spec/decisions/` — list all ADR files
5. `spec/features/` — scan for status.md in each work item folder
6. `spec/architecture.md` — if it exists

## Structure of `spec/index.md`

Rebuild or update these sections:

### Project Summary
One paragraph: goal, current maturity, and key constraints.

### Current Status
3–5 bullet points reflecting today's state:
- What is working and shipped
- What is actively in progress
- What is blocked and why

### Work Items

Organize by stage:

```markdown
## In Progress
- [S-core-001 — Title](features/S-core-001-slug/feature.md) — Phase: Implementation

## Planned
- [S-core-002 — Title](features/S-core-002-slug/feature.md) — P1

## Shipped
- [S-core-000 — Title](features/S-core-000-slug/feature.md) — ✓
```

Link to `feature.md` for each item. Include current phase for In Progress items. Include priority for Planned items.

### Decisions

List all ADRs in `spec/decisions/`:
```markdown
## Decisions
- [ADR-0001: Title](decisions/ADR-0001-slug.md)
```

### Architecture
Link to `spec/architecture.md` if it exists.

### Quick Links
Link to `spec/brief.md`, `spec/backlog.md`, `spec/changelog.md`.

## Verification

Before writing, verify every link target exists. Remove or mark broken links as `(pending)` rather than leaving dead links.

## Handoff

No further action required. `spec/index.md` is now current.
