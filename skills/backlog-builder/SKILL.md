---
name: backlog-builder
description: This skill should be used when the user asks to "build the backlog", "create backlog", "organize work items into streams", "convert specs to backlog", or wants to take a project brief and turn it into a structured, prioritized backlog.
version: 1.0.0
---

# Backlog Builder

Convert project specifications into a structured, stream-organized backlog of work items.

## Setup

Read in order:
1. `CLAUDE.md` — project constraints and context
2. `spec/brief.md` — goals, scope, constraints, milestones
3. `spec/index.md` — current navigation and any existing structure
4. `spec/backlog.md` — to understand any existing work items before adding new ones

## Process

### 1. Identify Streams

Organize work into 2–6 logical streams. A stream groups related work by domain, layer, or phase. Examples: `core`, `api`, `cli`, `infra`, `docs`, `test`.

Each stream gets a short kebab-case identifier used in work item IDs.

### 2. Define Work Items

For each stream, create 3–10 work items. Each item must be:
- **Vertically valuable** — delivers observable value end-to-end
- **Independently testable** — can be verified in isolation
- **Appropriately sized** — completable in a single focused session

Use the format `S-<stream>-<nnn>` with zero-padded three-digit numbers (e.g. `S-core-001`).

### 3. Assign Priority and Dependencies

Mark each item as one of: `P1` (must-have), `P2` (should-have), `P3` (nice-to-have).
Note explicit dependencies with `depends: S-<stream>-<nnn>`.

### 4. Write `spec/backlog.md`

Structure:

```markdown
# Backlog

## Stream: <name>

### S-<stream>-001 — <title>
**Priority:** P1
**Status:** Planned
**Goal:** <one sentence>
**Acceptance Criteria:**
- [ ] <criterion>
**Dependencies:** none
```

Update `spec/index.md` to link to the backlog and list streams.

## Handoff

Summarize the backlog: number of streams, total items, and top three P1 items. Recommend the feature-kickoff skill for the highest-priority item. If any item appears too large for a single session, recommend the feature-slicer skill to decompose it first.
