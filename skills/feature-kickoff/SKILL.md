---
name: feature-kickoff
description: This skill should be used when the user asks to "kick off feature", "create work item docs", "set up spec folder for", "initialize documentation for work item", or wants to create the full documentation folder structure for a specific work item before implementation.
version: 1.0.0
---

# Feature Kickoff

Create the complete documentation folder for a work item. Establishes all required artifacts that downstream skills (implement-feature, test-plan, ship-feature) depend on.

## Setup

Identify the work item ID from the user's request or conversation context.
Format: `S-<stream>-<nnn>` (e.g. `S-core-001`).

Read:
1. `spec/backlog.md` — to find the work item's goal and acceptance criteria
2. `CLAUDE.md` — for project constraints

Derive a slug from the work item title (kebab-case, 3–5 words).
Folder path: `spec/features/<work-id>-<slug>/`

## Folder Structure to Create

Create all six files. Do not overwrite if they already exist with content.

### `feature.md`
```markdown
# <Work Item ID> — <Title>

## Goal
<one paragraph from backlog or qa-intake brief>

## Acceptance Criteria
- [ ] <criterion>

## Out of Scope
- <exclusion>

## Open Questions
- <any unresolved items>

## Decisions
- <architectural decisions made during implementation — leave empty initially>
```

### `implementation.md`
```markdown
# Implementation Notes — <Work Item ID>

## Approach
<to be filled during implementation>

## Files Changed
<to be filled during implementation>

## Key Decisions
<to be filled during implementation>
```

### `test-plan.md`
```markdown
# Test Plan — <Work Item ID>

## Test Matrix
<to be filled by the test-plan skill>

## Smoke Scenarios
<to be filled by the test-plan skill>
```

### `test-results.md`
```markdown
# Test Results — <Work Item ID>

## Results
<to be filled by the test-runner and smoke-test skills>
```

### `status.md`
```markdown
# Status — <Work Item ID>

**Current phase:** Planning
**Blockers:** none

## History
- <date> — folder created by feature-kickoff
```

### `evidence/README.md`
```markdown
# Evidence — <Work Item ID>

Smoke test artifacts and validation evidence will be recorded here.
```

## ADR Initialization

If no ADR exists in `spec/decisions/`, create `spec/decisions/ADR-0001-initial-architecture.md` as a stub. Do not create an ADR if decisions already exist.

## Update Index

Add or update the work item entry in `spec/index.md` under the appropriate stream section with status `Planned` and a link to `feature.md`.

## Handoff

List all files created. Recommend next steps:
- Use the spec-linter skill to validate the documentation
- Use the implementation-phase skill to begin full implementation
- Use the qa-intake skill if acceptance criteria are still unclear
