---
name: qa-intake
description: This skill should be used when the user asks to "clarify requirements for", "qa intake for", "refine this work item", "what are the acceptance criteria for", or wants to turn a rough feature request into a well-defined work item with clear acceptance criteria before implementation begins.
version: 1.1.0
---

# QA Intake

Clarify and refine requirements for a work item before implementation. Produces a structured brief with acceptance criteria and a definition of done that drive the test-plan and implement-feature skills.

## Setup

Identify the work item ID (format: `S-<stream>-<nnn>`) from the user's request or context.

Read in order:
1. Project `CLAUDE.md` — command overrides and project constraints
2. `spec/backlog.md` — target work item goal and stream
3. `spec/brief.md` or `spec/index.md` — project context
4. `spec/features/<work-id>-<slug>/feature.md` — **if it exists**, load it to update rather than overwrite

If `feature.md` already exists with content, summarize what is already known and only ask questions about the gaps. Do not discard prior work.

## Step 1: Restate and Gather

Restate the request in one or two sentences to confirm understanding.

Then **ask all clarifying questions in a single message** — do not ask one category, wait for a response, then ask another. Identify which questions are already answered by existing specs and skip those.

Organize questions into these categories. Only include a category if it has unanswered questions.

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

**AI / LLM specifics (include when the work item involves model calls, prompts, or AI output):**
- Is the output deterministic? If not, how is correctness verified?
- What is the acceptable latency and token budget?
- Are there prompt injection or hallucination risks to guard against?
- Should outputs be validated structurally (schema), semantically (content), or both?

**CLI / script specifics (include when the work item involves a CLI tool or script):**
- What is the invocation command and key flags?
- Where do test fixtures live?
- What validation mode should smoke tests use?

Cap the total question count at nine. Prioritize questions whose answers most constrain the acceptance criteria.

## Step 2: Draft Acceptance Criteria

Convert answers into acceptance criteria. Write each criterion in active voice with a clear subject and observable outcome:

> Given `<precondition>`, when `<action>`, then `<observable result>`.

or more concisely:

> `<system>` `<does what>` when `<condition>`.

## Step 3: Criteria Quality Gate

Before writing the brief, validate every criterion against all four rules. Rewrite any that fail.

| Rule | Check |
|---|---|
| **Observable** | The outcome is visible outside the system — not an internal state or log line |
| **Measurable** | There is a clear pass/fail condition; no "should work" or "be fast" |
| **Unambiguous** | Only one reasonable interpretation exists |
| **Error coverage** | At least one criterion covers invalid input, an error path, or a boundary condition |

If a criterion fails a rule, rewrite it until it passes. Do not include a criterion that cannot be machine-verified.

## Step 4: Define Definition of Done

Acceptance criteria describe *behavior*. The definition of done describes *process*. Keep them separate.

Standard DoD for this project:
- [ ] All acceptance criteria pass (automated)
- [ ] Full test suite passes (format, lint, types, tests)
- [ ] Smoke test passes with artifacts
- [ ] No regressions in related areas
- [ ] Docs updated if user-facing behavior changed

Add project-specific DoD items if the work item requires them (e.g. migration script tested, API contract versioned).

## Step 5: Write the Brief

Write to `spec/features/<work-id>-<slug>/feature.md` if the folder exists, or produce inline if not. If `feature.md` already existed, update it in place — preserve any sections that are still accurate.

```markdown
## Goal
<one paragraph — observable outcome and who benefits>

## Acceptance Criteria
- [ ] Given <precondition>, when <action>, then <observable result>
- [ ] <...>

## Definition of Done
- [ ] All acceptance criteria pass (automated)
- [ ] Full test suite passes
- [ ] Smoke test passes with artifacts
- [ ] Docs updated if user-facing behavior changed
- [ ] <any project-specific items>

## Constraints
- <constraint>

## Out of Scope
- <explicit exclusion>

## Dependencies
- <work item ID this depends on, or "none">

## Open Questions
- <anything unresolved — remove section if empty>
```

## Step 6: Sizing Check

Count the acceptance criteria. If there are seven or more, the item is likely too large for a single session. Flag this explicitly:

> This work item has N acceptance criteria and may be too large to implement in a single session. Consider using the feature-slicer skill to decompose it before proceeding.

If the item is well-sized (2–6 criteria), proceed to handoff.

## Handoff

Recommend the appropriate next skill:
- Use the feature-kickoff skill to create the full documentation folder (if not yet created)
- Use the spec-linter skill to validate the brief before implementation
- Use the implementation-phase skill if the folder already exists and the brief is complete
- Use the feature-slicer skill if the sizing check flagged too many criteria
