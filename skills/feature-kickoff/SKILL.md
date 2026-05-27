---
name: feature-kickoff
description: This skill should be used when the user asks to "kick off feature", "create work item docs", "set up spec folder for", "initialize documentation for work item", or wants to create the full documentation folder structure for a specific work item before implementation.
version: 1.1.0
---

# Feature Kickoff

Create the complete documentation folder for a work item using bundled templates. Establishes all artifacts that downstream skills (implement-feature, test-plan, ship-feature) depend on.

## Setup

Identify the work item ID from the user's request or context.
Format: `S-<stream>-<nnn>` (e.g. `S-core-001`).

Read:
1. `spec/backlog.md` — work item goal and acceptance criteria
2. `CLAUDE.md` — project constraints

Derive a slug from the work item title (kebab-case, 3–5 words).
Target folder: `spec/features/<work-id>-<slug>/`

If the folder already exists with content, report what is present and skip creating files that already have content.

## Templates

All file templates live in `${CLAUDE_PLUGIN_ROOT}/templates/`. Copy each template, replacing `{{WORK_ITEM_ID}}` with the actual ID, `{{TITLE}}` with the work item title, and `{{date}}` with today's date.

## Files to Create

Create these six files. Do not overwrite existing files that already have content.

| Target file | Template |
|---|---|
| `spec/features/<work-id>-<slug>/feature.md` | `${CLAUDE_PLUGIN_ROOT}/templates/feature.md` |
| `spec/features/<work-id>-<slug>/implementation.md` | `${CLAUDE_PLUGIN_ROOT}/templates/implementation.md` |
| `spec/features/<work-id>-<slug>/test-plan.md` | `${CLAUDE_PLUGIN_ROOT}/templates/test-plan.md` |
| `spec/features/<work-id>-<slug>/test-results.md` | `${CLAUDE_PLUGIN_ROOT}/templates/test-results.md` |
| `spec/features/<work-id>-<slug>/status.md` | `${CLAUDE_PLUGIN_ROOT}/templates/status.md` |
| `spec/features/<work-id>-<slug>/evidence/README.md` | `${CLAUDE_PLUGIN_ROOT}/templates/evidence-readme.md` |

After copying, populate `feature.md` with any goal and acceptance criteria already known from `spec/backlog.md` or a prior qa-intake session.

## ADR Initialization

If no ADR exists in `spec/decisions/`, create `spec/decisions/ADR-0001-initial-architecture.md` as a stub. Skip if ADRs already exist.

## Update Index

Add or update the work item entry in `spec/index.md` under the appropriate stream section:
- Status: `Planned`
- Link to `feature.md`

## Handoff

List all files created and any that were skipped (already existed). Recommend next steps:
- Use the spec-linter skill to validate the documentation before starting
- Use the qa-intake skill if acceptance criteria are still unclear
- Use the implementation-phase skill once the spec is complete and linted
