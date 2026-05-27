---
name: project-intake
description: This skill should be used when the user asks to "bootstrap this project", "set up SDLC for this repo", "initialize the spec folder", "run project intake", or wants to transform a rough idea into structured project documentation with SDLC infrastructure.
version: 1.0.0
---

# Project Intake

Bootstrap a new project repository and transform a rough idea into structured SDLC documentation.

## Safety Check

Verify the current directory is the target project, not the claude_home plugin directory. If `CLAUDE.md` already exists in the target repo, read it first and follow its instructions.

## Phase 1: Bootstrap

Create missing SDLC infrastructure. Do not overwrite existing files.

**Directories to create (if absent):**
- `spec/`
- `spec/templates/`
- `spec/decisions/`
- `spec/features/`
- `scripts/`

**Files to create (if absent):**
- `CLAUDE.md` — minimal project instructions with `## Commands` section
- `spec/index.md` — navigation hub (stub)
- `spec/backlog.md` — backlog (stub)
- `spec/changelog.md` — with initial entry
- `spec/smoke.md` — smoke testing plan (stub)

**Smoke infrastructure (if absent):**
- `spec/smoke_registry.yaml` — registry of smoke scenarios
- `scripts/smoke.py` — minimal smoke harness stub

## Phase 2: Discovery

Read the project idea from available sources: README, existing code, any brief the user has provided. Ask up to five focused questions — only for essential missing information:
- What is the primary goal?
- Who are the users or consumers?
- What are the key constraints (language, runtime, external dependencies)?
- What does success look like at first milestone?
- Are there known non-goals or out-of-scope areas?

Do not ask questions that can be reasonably inferred from existing files.

## Phase 3: Documentation

Create two key artifacts:

**`spec/brief.md`** (1–2 pages):
- Goal and problem statement
- Users / consumers
- Scope and explicit non-scope
- Constraints and risks
- Initial milestones

**`spec/index.md`** (navigation hub):
- Links to brief, architecture (when it exists), decisions, backlog
- One-line status for each linked artifact

## Phase 4: Workflow Initialization

- Ensure `spec/changelog.md` has an entry for this intake session.
- Ensure `spec/decisions/` is ready to receive ADRs.

## Handoff

List all files created and preserved. Note any `## Commands` customizations needed in `CLAUDE.md`. Suggest three initial work items. Recommend the backlog-builder skill as the next step.
