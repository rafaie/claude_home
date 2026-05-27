---
name: feature-slicer
description: This skill should be used when the user asks to "slice this feature", "break down work item", "decompose into smaller pieces", "split this into shippable slices", or when a work item is too large and needs to be decomposed into independently deliverable sub-items.
version: 1.0.0
---

# Feature Slicer

Decompose a large feature or stream into manageable, independently shippable work items.

## Setup

Identify the target stream or work item from the user's request.

Read:
1. `spec/backlog.md` — to find the target item's goals and acceptance criteria
2. `spec/brief.md` or `spec/index.md` — for project context and constraints
3. `CLAUDE.md` — for any size or scope constraints

## Slicing Criteria

Each resulting slice must satisfy all four properties:
- **Vertically valuable** — delivers observable end-to-end value, not just a layer
- **Independently testable** — can be verified without other slices being complete
- **Low-risk-first** — order slices so foundational pieces come before dependent ones
- **Reasonably sized** — completable in a single focused session

Do not create slices that are purely horizontal (e.g. "write all tests" or "create all models"). Prefer thin vertical cuts through the stack.

## Process

### 1. Analyze the target item

Read the acceptance criteria. Identify natural fault lines: distinct user-visible behaviors, independent integrations, separable data flows, or phased complexity.

### 2. Create 5–12 slices

Assign new work item IDs in sequence within the same stream. If the original item was `S-core-001`, slices become `S-core-002`, `S-core-003`, etc. (or use a sub-stream if the stream is dedicated to this feature).

For each slice, define:
- ID and short title
- Goal (one sentence)
- Key acceptance criteria (2–4 items)
- Dependencies on other slices

### 3. Update `spec/backlog.md`

Add all new slice entries. Mark the original large item as `Superseded by: S-<stream>-<nnn> through S-<stream>-<nnn>` and set its status to `Sliced`.

### 4. Update `spec/index.md`

Add new items to the Planned section with links. Move the original item to a Sliced or Archived section.

## Output

Summarize the slices as a table:

| ID | Title | Priority | Depends On |
|---|---|---|---|
| S-core-002 | ... | P1 | none |

## Handoff

Recommend the feature-kickoff skill for the first slice in priority order.
