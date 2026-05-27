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

## Available skills

This plugin provides 23 SDLC skills. Mention what you want to do and Claude
will invoke the appropriate skill:

- **session-start** — review project status and suggest priorities
- **project-intake** — bootstrap a new project with SDLC structure
- **qa-intake** — clarify and refine requirements for a work item
- **backlog-builder** — convert specs into a structured stream backlog
- **feature-kickoff** — create documentation folder for a work item
- **feature-slicer** — decompose a large feature into shippable slices
- **implementation-phase** — run the full test→implement→verify cycle
- **implement-feature** — implement a single work item end-to-end
- **test-plan** — generate a test strategy from acceptance criteria
- **write-tests** — write and execute tests for a work item
- **test-runner** — run quality checks in quick or full mode
- **smoke-test** — run smoke tests and capture artifacts
- **ship-feature** — validate and finalize a work item for shipping
- **debug-loop** — systematically resolve test or runtime failures
- **failure-triage** — triage and prioritize multiple simultaneous failures
- **adr-review** — identify and document architectural decisions
- **architecture-updater** — sync architecture docs with the codebase
- **docs-update** — update user-facing docs and changelog after shipping
- **docs-index-refresh** — refresh spec/index.md as a navigation hub
- **spec-linter** — review work item docs for completeness before implementation
- **flaky-test-hunter** — identify and stabilize flaky tests
- **feature-closeout** — verify a work item is fully done (deprecated)
- **release-prep** — run all checks and prepare release notes

## Guardrails

- Never edit or delete user project files unless asked to.
- When instructions conflict, this file is secondary to the project's
  `CLAUDE.md` and explicit user requests.
- Keep changes small, and document decisions in the project's spec logs.
