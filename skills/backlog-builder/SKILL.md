---
name: backlog-builder
description: This skill should be used when the user asks to "build the backlog", "create backlog", "create epics and stories", "organize work items into streams", "convert specs to backlog", or wants to take a project brief and turn it into a structured, prioritized backlog of epics and stories.
version: 2.0.0
---

# Backlog Builder

Convert project specifications into a prioritized backlog of epics and stories. Model, IDs, and statuses:
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`.

## Setup

Read in order:
1. `CLAUDE.md` — project constraints and context
2. `spec/brief.md` — goals, scope, constraints, milestones
3. `spec/index.md` — current navigation and any existing structure
4. `spec/backlog.md` — existing epics and stories, so new ones extend rather than duplicate

## Process

### 1. Identify Areas

Pick 2–6 areas — short kebab-case labels for domain or layer (`core`, `api`, `cli`, `infra`, `docs`).
Areas are labels used in story IDs, not levels of the hierarchy.

### 2. Identify Epics

Group the brief's goals into epics — outcomes a user would recognize (e.g. "Auth hardening"). Each epic
gets `E-<nn>`, a one-paragraph outcome, and 1–3 success measures. Small projects may have no epics;
stories can be standalone.

### 3. Define Stories

For each epic, write 3–8 stories. Each story must be:
- **Vertically valuable** — delivers observable value end-to-end, not a single layer
- **Independently testable** — can be verified in isolation
- **Right-sized** — 2–6 acceptance criteria, completable in one focused session

Use `S-<area>-<nnn>` with zero-padded numbers, continuing from the highest existing number in that area.
Write each story as "As a <who>, I want <what>, so that <why>" with draft ACs in Given/When/Then form,
numbered `AC-1…n`.

### 4. Priority and Dependencies

Mark each story `P1` (must-have), `P2` (should-have), or `P3` (nice-to-have). Record dependencies as story
IDs. Check that dependencies have no cycles.

### 5. Write `spec/backlog.md`

```markdown
# Backlog

## E-01 — <epic title>
**Status:** Backlog · **Outcome:** <one sentence>

| ID | Title | Area | Priority | Status | Depends on |
|---|---|---|---|---|---|
| S-core-001 | <title> | core | P1 | Backlog | none |

### S-core-001 — <title>
As a <who>, I want <what>, so that <why>.
- AC-1 — Given <context>, when <action>, then <outcome>.

## Standalone stories
<same table and entries for stories without an epic>

## Follow-ups
<low-severity review findings added by the independent-review skill>
```

Update `spec/index.md` to link to the backlog and list epics.

## Handoff

Summarize: number of epics, number of stories, and the top three P1 stories that have no unfinished
dependencies. Recommend the feature-kickoff skill for the highest-priority story (or its epic). If any
story looks too large, recommend the feature-slicer skill first.
