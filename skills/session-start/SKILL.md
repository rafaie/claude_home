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

Review `spec/backlog.md` when available. Note which streams are active and which work items are in progress, planned, or blocked.

### 4. Check live repo state

Augment the spec picture with actual git state:

```bash
git log --oneline -10          # recent activity
git status --short             # uncommitted changes
git branch --show-current      # active branch
```

Scan `spec/features/*/status.md` files to get per-work-item phase and blockers. The spec may lag behind the code — git state and status files are more reliable indicators of what is actually in progress.

Reconcile any discrepancies between `spec/backlog.md` status and `status.md` files. Note them in the summary.

### 5. Document current status

Produce a 5–10 point summary of the project landscape, drawing on both spec and git:
- What exists and is working (confirmed by commits, not just spec)
- What is actively in progress (branch, modified files, or status.md phase)
- What is blocked or has open questions
- Any recent completions (recent commits or status.md = Shipped)
- Any discrepancies between spec and actual state

### 6. Identify priorities

Suggest three focused work items as thin vertical slices. For each:
- Work item ID (or proposed ID)
- One-sentence justification
- Recommended first action

Prefer items that are unblocked, clearly scoped, have complete specs, and deliver observable value. Deprioritize items with open questions or missing documentation.

### 7. Recommend next step

Suggest the follow-up skill based on project state:
- Use the qa-intake skill to clarify requirements for an unrefined item
- Use the feature-kickoff skill to create documentation for a ready item
- Use the implement-feature skill if an item is fully specified and tests exist
- Use the implementation-phase skill to run the full cycle for a fully specified item

## Output Format

```
## Project Status
- Branch: <current branch>
- Recent activity: <summary of last 3–5 commits>
- <3–8 more status bullets>

## In Progress
- <work-id>: <phase from status.md>

## Suggested Priorities
1. <work-id> — <justification> → next: <skill>
2. <work-id> — <justification> → next: <skill>
3. <work-id> — <justification> → next: <skill>
```
