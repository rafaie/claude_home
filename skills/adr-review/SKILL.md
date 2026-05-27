---
name: adr-review
description: This skill should be used when the user asks to "review ADRs", "do we need an ADR", "document this architecture decision", "create an ADR for", or when significant design choices, new dependencies, or interface changes have been made that warrant formal documentation.
version: 1.0.0
---

# ADR Review

Identify whether architectural decisions were made and create Architecture Decision Records (ADRs) to document them.

## Decision Triggers

An ADR is warranted when any of the following occurred:
- A significant design choice was made between two or more viable alternatives
- A new external dependency was introduced
- An existing integration boundary was changed
- A new technology, framework, or pattern was adopted
- A performance, security, or scalability trade-off was accepted

If none of the above apply, skip ADR creation and note the reason.

## Setup

Identify the work item ID from user request or context.

Read:
1. `spec/features/<work-id>-<slug>/implementation.md` — key decisions section
2. `spec/features/<work-id>-<slug>/feature.md` — decisions section
3. `spec/decisions/` — existing ADRs (to determine the next ADR number)
4. Recent file diffs if available

## Process

### 1. Identify decision points

List candidate decisions from the implementation notes. For each, ask:
- Was there a real alternative?
- Does the choice constrain future work?
- Would a new contributor ask "why was this done this way?"

If yes to any, the decision warrants an ADR.

### 2. Create ADRs

For each warranted decision, create `spec/decisions/ADR-<nnnn>-<slug>.md`:

```markdown
# ADR-<nnnn>: <Title>

**Date:** <YYYY-MM-DD>
**Status:** Accepted
**Work Item:** <work-id>

## Context
<Why this decision needed to be made. What problem does it solve?>

## Decision
<What was decided. State it clearly in one or two sentences.>

## Alternatives Considered
- <Alternative 1> — rejected because <reason>
- <Alternative 2> — rejected because <reason>

## Consequences
- <Positive consequence>
- <Negative consequence or trade-off accepted>

## Links
- [feature.md](../features/<work-id>-<slug>/feature.md)
```

### 3. Link from feature.md

Add the ADR reference to the `## Decisions` section of `feature.md`:
```
- [ADR-<nnnn>: <Title>](../../../spec/decisions/ADR-<nnnn>-<slug>.md)
```

## Handoff

List ADRs created (or confirm none were needed). If ADRs were created that affect the system's components, data flow, or external dependencies, recommend the architecture-updater skill to keep `spec/architecture.md` in sync. Recommend the docs-index-refresh skill to keep `spec/index.md` current.
