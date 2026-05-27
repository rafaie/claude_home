---
name: session-start
description: This skill should be used when the user asks "what should we work on", "start a session", "what's the project status", "current priorities", "where did we leave off", or wants an overview of the project state before diving in.
version: 1.0.0
---

# Session Start

Establish project context and surface the most valuable next actions before any implementation begins.

## Process

Follow these six steps in order:

### 1. Review configuration

Read `CLAUDE.md` and the project's own `CLAUDE.md` (if present) for setup details, command overrides, and any active constraints.

### 2. Read the specification

Check `spec/index.md` first. Fall back to `spec/brief.md` if `index.md` is absent or empty.

### 3. Consult the backlog

Review `spec/backlog.md` when available. Note which streams are active and which work items are in progress, planned, or blocked.

### 4. Document current status

Produce a 5–10 point summary of the project landscape:
- What exists and is working
- What is in progress
- What is blocked or has open questions
- Any recent completions worth noting

### 5. Identify priorities

Suggest three focused work items as thin vertical slices. For each, provide:
- The work item ID or a proposed ID if none exists
- A one-sentence justification
- The recommended first action

Prefer items that are unblocked, clearly scoped, and deliver observable value.

### 6. Recommend next step

Suggest the appropriate follow-up skill based on the project state:
- Use the qa-intake skill to clarify requirements for an unrefined item
- Use the feature-kickoff skill to create documentation for a ready item
- Use the implement-feature skill if an item is already fully specified

## Output Format

```
## Project Status
<5–10 bullet points>

## Suggested Priorities
1. <work-id> — <justification> → next: <skill>
2. <work-id> — <justification> → next: <skill>
3. <work-id> — <justification> → next: <skill>
```
