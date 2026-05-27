---
name: qa-intake
description: This skill should be used when the user asks to "clarify requirements for", "qa intake for", "refine this work item", "what are the acceptance criteria for", or wants to turn a rough feature request into a well-defined work item with clear acceptance criteria before implementation begins.
version: 1.0.0
---

# QA Intake

Clarify and refine requirements for a work item before implementation. Produces a structured brief with acceptance criteria that can drive the test-plan and implement-feature skills.

## Setup

Read in order:
1. Project `CLAUDE.md` — for command overrides and project constraints
2. `spec/backlog.md` — to locate the target work item and its stream
3. `spec/brief.md` or `spec/index.md` — for project context

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or from context.

## Intake Process

Restate the request in one or two sentences to confirm understanding. Then ask focused questions — a maximum of nine, grouped by category. Only ask questions whose answers are not already clear from existing specs.

**Goal and outcome:**
- What observable behavior changes when this is complete?
- Who benefits and how do they use the result?

**Inputs and outputs:**
- What data, events, or triggers does this consume?
- What does it produce — files, API responses, side effects?

**Constraints:**
- Are there performance, security, or compatibility constraints?
- Any external dependencies or integration points?

**Trade-offs:**
- Is there a simpler version that ships sooner?
- What is explicitly out of scope for this slice?

**Edge cases:**
- What happens with empty input, invalid data, or partial state?
- Are there known failure modes to handle?

**CLI / script specifics (when applicable):**
- What is the invocation command and key flags?
- Where do test fixtures live?
- What validation mode should smoke tests use?

## Output: Structured Brief

Write the brief directly into the work item folder if it exists (`spec/features/<work-id>-<slug>/feature.md`), or produce it inline if the folder has not been created yet.

```markdown
## Goal
<one paragraph>

## Acceptance Criteria
- [ ] <measurable, testable criterion>
- [ ] <measurable, testable criterion>
...

## Constraints
- <constraint>

## Out of Scope
- <exclusion>

## Open Questions
- <anything unresolved>
```

## Handoff

Recommend the appropriate next skill:
- Use the feature-kickoff skill to create the full documentation folder
- Use the implementation-phase skill if the item is already documented
