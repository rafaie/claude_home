---
name: feature-kickoff
description: This skill should be used when the user asks to "kick off feature", "kick off story", "create story docs", "create work item docs", "set up spec folder for", "create epic E-03", "initialize documentation for work item", or wants to create the documentation folder for a story (work item) or an epic before implementation.
version: 2.0.0
---

# Feature Kickoff

Create the documentation folder for a story — or the `epic.md` for an epic — from bundled templates.
Establishes the artifacts that downstream skills (spec-linter, implementation-phase, independent-review,
ship-feature) depend on. Model, IDs, and layout: `${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the ID from the user's request or context:
- Story: `S-<area>-<nnn>` (e.g. `S-core-001`)
- Epic: `E-<nn>` (e.g. `E-03`)

Read:
1. `spec/backlog.md` — story or epic goal, acceptance criteria, epic membership, priority, dependencies
2. `CLAUDE.md` — project constraints

Derive a slug from the title (kebab-case, 3–5 words).

**Legacy projects:** if `spec/features/` exists and `spec/stories/` does not, the project uses the legacy
layout. Tell the user it can be migrated with
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py"` and ask whether to migrate first. If they
decline, create the new folder under `spec/features/` with `feature.md` so the project stays consistent.

If the target folder already exists with content, report what is present and skip files that already have
content.

## Templates

Templates live in `${CLAUDE_PLUGIN_ROOT}/templates/`. Replace `{{STORY_ID}}` / `{{EPIC_ID}}` with the ID,
`{{TITLE}}` with the title, and `{{date}}` with today's date. Fill header fields (Epic, Area, Priority,
Depends on) from the backlog.

## Story: Files to Create

Target folder: `spec/stories/<story-id>-<slug>/`

| Target file | Template |
|---|---|
| `story.md` | `story.md` |
| `implementation.md` | `implementation.md` |
| `test-plan.md` | `test-plan.md` |
| `test-results.md` | `test-results.md` |
| `status.md` | `status.md` |
| `evidence/README.md` | `evidence-readme.md` |

`reviews/` is created later by the independent-review skill.

After copying, populate `story.md` with the story statement and acceptance criteria already known from
`spec/backlog.md` or a prior qa-intake session. Number criteria `AC-1…n` in Given/When/Then form.

If the story belongs to an epic, add or update its row in the epic's `## Stories` table.

## Epic: File to Create

Target: `spec/epics/E-<nn>-<slug>/epic.md` from `epic.md`. Fill the outcome and list the member stories
from the backlog. Kick off member stories separately (or together, if the user asks).

## ADR Initialization

If no ADR exists in `spec/decisions/`, create `spec/decisions/ADR-0001-initial-architecture.md` as a stub.
Skip if ADRs already exist.

## Update Index

Add or update the entry in `spec/index.md`: under its epic (or "Standalone stories"), with status
`Backlog` and a link to `story.md` / `epic.md`.

## Handoff

List all files created and any that were skipped. Recommend next steps:
- Use the qa-intake skill if acceptance criteria are still unclear
- Use the spec-linter skill to check the Definition of Ready (moves the story to `Ready`)
- Use the implementation-phase skill once the story is `Ready`
