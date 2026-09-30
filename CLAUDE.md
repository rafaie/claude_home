# Claude Home (Global) — Instructions

This repository is the claude_home plugin. It provides reusable skills for
Claude Code that apply to other project repositories. It is not a standalone project.

## How to use this home with any project

- Always treat the target repo as the source of truth for implementation.
- If the target repo has its own `CLAUDE.md`, follow it first.
- If the target repo's `CLAUDE.md` includes a `## Commands` section, use those overrides.
- If no local overrides exist, use the defaults described below.
- Do not add project artifacts here; those live in each project repo under `spec/`.

## Default command assumptions (override per project)

When skills mention tests or checks and no local override exists, use these defaults:

- Tests (quick): `uv run pytest -q`
- Tests (full): `uv run pytest -q`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format . --check`
- Types: `uv run mypy src`
- Docstrings (optional): run the `docstrings` command when configured by the target repo.
- Smoke: `uv run python scripts/smoke.py`

## Python docstring standard

- Use Google-style docstrings for public APIs, CLI entrypoints, data models/schemas,
  provider/client wrappers, integration boundaries, non-trivial private helpers,
  and shared test fixtures.
- Do not add docstrings that only restate the function name.
- Prefer project-local lint configuration for enforcement.

## Smoke mode

- Prefer live canary mode when provider credentials are present
  (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `SMOKE_LIVE=1`).
- Fall back to offline mode when live credentials are unavailable.

## Per-project command overrides

Add a `## Commands` section to the target repo's `CLAUDE.md` to override defaults:

```markdown
## Commands

- test_quick: uv run pytest -q
- test_full: uv run pytest -q
- lint: uv run ruff check .
- format: uv run ruff format . --check
- typecheck: uv run mypy src
- smoke: uv run python scripts/smoke.py
```

## Work hierarchy

Projects organize work as **Epic → Story → Task** (full model: `references/hierarchy.md` in this plugin):

- **Epic** (optional) `E-<nn>` — an outcome grouping stories: `spec/epics/E-<nn>-<slug>/epic.md`
- **Story** `S-<area>-<nnn>` — the unit that is tested, independently reviewed, and marked Done:
  `spec/stories/S-<area>-<nnn>-<slug>/story.md`
- **Task** — a checklist item in the story's `implementation.md`
- Story status: `Backlog → Ready → In Progress → In Review → Done`
- "Work item" means story. Legacy projects use `spec/features/<id>-<slug>/feature.md` — read them as
  stories, keep their layout when writing, and suggest `scripts/migrate_spec.py` to migrate.

A **run** (story-runner) is an execution batch of stories, tracked in `spec/runs/<run-id>/run.json` —
not a planning level.

An optional **knowledge graph** (graphify, `references/graphify.md`) gives implementers and reviewers a
map of the code via `scripts/graph.py`; it is never evidence and never blocks a gate unless the project
sets `graphify: required`.

A story is Done only when its independent review gate passes: 0 open high and 0 open medium findings,
checked by `scripts/gate_check.py`. Only the user can waive a finding.

## Available skills

This plugin provides 23 SDLC skills and two agents. Mention what you want to do and Claude
will invoke the appropriate skill:

- **session-start** — review project status and suggest priorities
- **work-item-status** — status card for a story, or rollup for an epic
- **project-intake** — bootstrap a new project with SDLC structure
- **qa-intake** — refine a story: statement, numbered Given/When/Then ACs
- **backlog-builder** — convert specs into a backlog of epics and stories
- **feature-kickoff** — create the documentation folder for a story or epic
- **feature-slicer** — split an epic or oversized story into stories
- **implementation-phase** — run one story through test→implement→commit→independent review
- **implement-feature** — implement a story's acceptance criteria
- **test-plan** — generate a test strategy from acceptance criteria
- **write-tests** — write and execute tests for a story (test-first)
- **test-runner** — run quality checks in quick or full mode
- **smoke-test** — run smoke tests and capture artifacts
- **ship-feature** — check the Definition of Done (incl. review gate) and mark a story Done
- **debug-loop** — systematically resolve test or runtime failures
- **failure-triage** — triage and prioritize multiple simultaneous failures
- **architecture-review** — document architectural decisions and sync architecture docs
- **docs-update** — update user-facing docs, changelog, and spec/index.md
- **spec-linter** — check a story's Definition of Ready and move it to Ready
- **flaky-test-hunter** — identify and stabilize flaky tests
- **release-prep** — run all checks and prepare release notes
- **independent-review** — review a story/epic with a fresh-context reviewer and apply the review gate
- **story-runner** — run several stories (a list, an epic, or the next N Ready) end to end with gates,
  then an integration review; resumable

Agents:

- **independent-reviewer** — read-only reviewer launched by independent-review; never sees the
  implementation conversation (also runs as `claude -p` or on OpenAI Codex via `scripts/codex_review.py`)
- **story-implementer** — builds or fixes one story in its own context; launched by story-runner

Plus a utility skill:

- **md-to-html** — render a Markdown file into a polished, self-contained HTML page (left-side menu, light theme, Mermaid diagrams)

## Guardrails

- Never edit or delete user project files unless asked to.
- When instructions conflict, this file is secondary to the project's
  `CLAUDE.md` and explicit user requests.
- Keep changes small, and document decisions in the project's spec logs.
