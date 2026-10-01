---
name: feature-slicer
description: This skill should be used when the user asks to "slice this feature", "split this epic into stories", "split this story", "break down work item", "decompose into smaller pieces", "split this into shippable slices", or when an epic or story (work item) is too large and needs to be decomposed into independently deliverable stories.
version: 2.0.0
---

# Feature Slicer

Split an epic into stories, or an oversized story into smaller stories. Model, IDs, and statuses:
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Identify the target epic (`E-<nn>`) or story (`S-<area>-<nnn>`) from the user's request.

Read:
1. `spec/backlog.md` — the target's goal and acceptance criteria
2. The target's `epic.md` or `story.md` (and `status.md`), if a folder exists
3. `spec/brief.md` or `spec/index.md` — project context and constraints
4. `CLAUDE.md` — size or scope constraints

## Slicing Criteria

Each resulting story must satisfy all four properties:
- **Vertically valuable** — delivers observable end-to-end value, not just a layer
- **Independently testable** — can be verified without the other new stories being complete
- **Low-risk-first** — foundational stories come before the ones that depend on them
- **Right-sized** — 2–6 acceptance criteria, one focused session

Do not create horizontal slices ("write all tests", "create all models"). Prefer thin vertical cuts.

## Process

### 1. Find the fault lines

Read the acceptance criteria. Look for distinct user-visible behaviors, independent integrations,
separable data flows, or phased complexity (simple case first, edge cases later).

### 2. Decide the shape

| Target | Result |
|---|---|
| Epic | 3–8 stories in that epic |
| Story that splits into 2 stories | 2 sibling stories in the same epic (or standalone) |
| Story that splits into 3 or more | Promote it: create an epic `E-<nn>` from the story's goal, and put the new stories in it |

### 3. Write the new stories

Assign IDs continuing from the highest existing number in the area (e.g. `S-core-014`, `S-core-015`).
For each story: title, "As a … I want … so that …", 2–6 ACs (`AC-1…n`, Given/When/Then), priority,
and dependencies. Every original AC must land in exactly one new story — list the mapping.

### 4. Retire the original story (story targets only)

- Record it: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/story_state.py" split <story-id> --into <new IDs>`
  (sets `**Status:** Split` and `**Superseded by:**`, the History line, and the backlog/epic rows). `Split`
  is terminal — the story leaves the workflow.
- If the original was `In Progress` with commits, tell the user. The first new story inherits its
  `**Base commit:**` and existing code; note this in that story's History.
- Keep its folder for history; do not delete it.

### 5. Update indexes

Update `spec/backlog.md`, the epic's `## Stories` table, and `spec/index.md` (new stories under their
epic with status `Backlog`; the original under Split/Archived).

## Output

| ID | Title | ACs from original | Priority | Depends on |
|---|---|---|---|---|
| S-core-014 | ... | AC-1, AC-2 | P1 | none |

## Handoff

Recommend the feature-kickoff skill for the new stories (starting with the first in dependency order),
then the spec-linter skill.
