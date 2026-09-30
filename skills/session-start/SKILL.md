---
name: session-start
description: This skill should be used when the user asks "what should we work on", "start a session", "what's the project status", "current priorities", "where did we leave off", or wants an overview of the project state before diving in.
version: 1.1.0
---

# Session Start

Establish project context — from both spec files and the actual repo state — and surface the most valuable next actions before any implementation begins.

## Process

Follow these steps in order:

### 1. Review configuration

Read `CLAUDE.md` and the project's own `CLAUDE.md` (if present) for setup details, command overrides, and active constraints.

### 2. Read the specification

Check `spec/index.md` first. Fall back to `spec/brief.md` if `index.md` is absent or empty.

### 3. Consult the backlog

Review `spec/backlog.md` when available. Note which epics are active and which stories are In Progress, In Review, Ready, or blocked, plus any open `## Follow-ups`.

### 4. Check live repo state

Augment the spec picture with actual git state:

```bash
git log --oneline -10          # recent activity
git status --short             # uncommitted changes
git branch --show-current      # active branch
```

Scan `spec/stories/*/status.md` files for status, blockers, and review state. If the project still has
`spec/features/` (legacy layout), read those too, map `Current phase` per
`${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md`, and note in the summary that the project can be migrated
with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py"`.

Check the knowledge graph (optional): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" status`. If it
is `current` or `stale`, skim `GRAPH_REPORT.md` for the project's core abstractions; mention a
`missing`/`stale` graph or a pending docs pass in the summary (it is refreshed at the next run or review).

Check for an unfinished run: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_state.py" latest`. If one
exists, show it with `run_state.py show <run-id>` — resuming it usually outranks everything else.

For stories In Review, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py" <story-id>` to get the
current gate result.

The spec may lag behind the code — git state and status files are more reliable indicators of what is
actually in progress.

Reconcile any discrepancies between `spec/backlog.md` status and `status.md` files. Note them in the summary.

### 5. Document current status

Produce a 5–10 point summary of the project landscape, drawing on both spec and git:
- What exists and is working (confirmed by commits, not just spec)
- What is actively in progress (branch, modified files, or status In Progress / In Review)
- What is blocked, has open questions, or has a failing review gate
- Any recent completions (recent commits or status Done) and epic progress (k/n stories Done)
- Any discrepancies between spec and actual state

### 6. Identify priorities

Suggest three focused stories as thin vertical slices. For each:
- Story ID (or proposed ID)
- One-sentence justification
- Recommended first action

Finishing comes before starting: a story In Review with a failing gate outranks a new story. Then prefer Ready stories whose dependencies are Done, in epics already in progress. Deprioritize stories with open questions or missing documentation.

### 7. Recommend next step

Suggest the follow-up skill based on project state:
- Use the story-runner skill to resume an unfinished run, or to run several Ready stories (or an epic)
  end to end
- Use the qa-intake skill to clarify requirements for an unrefined story
- Use the feature-kickoff skill to create documentation for a backlog story
- Use the spec-linter skill to move a documented story to Ready
- Use the implementation-phase skill to run the full cycle (through independent review) for a Ready story
- Use the independent-review skill for a story In Review whose gate is failing or stale
- Use the ship-feature skill for a story whose review gate passes
- Use the work-item-status skill for a detailed card on any story or epic

## Output Format

```
## Project Status
- Branch: <current branch>
- Recent activity: <summary of last 3–5 commits>
- <3–8 more status bullets>

## In Flight
- <story-id>: <status> · review <gate result or "not reviewed"> · epic <E-nn or none>

## Epics
- <E-nn> — <title>: <k>/<n> Done

## Active Run
- <run-id>: <status> · <k>/<n> stories done · current: <story-id> at <gate>   (or "none")

## Suggested Priorities
1. <story-id> — <justification> → next: <skill>
2. <story-id> — <justification> → next: <skill>
3. <story-id> — <justification> → next: <skill>
```
