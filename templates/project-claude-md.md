# {{PROJECT_NAME}} — Claude Instructions

This is the project-level Claude configuration. It takes precedence over the global claude_home instructions.

## Project Overview
{{one paragraph describing the project goal and key constraints}}

## Commands

- test_quick: uv run pytest -q
- test_full: uv run pytest -q
- lint: uv run ruff check .
- format: uv run ruff format . --check
- typecheck: uv run mypy src
- smoke: uv run python scripts/smoke.py

## Review

- reviewer: subagent        # subagent | headless (separate `claude -p` process)
- reviewer_model: inherit   # inherit, or a model name/alias for the reviewer
- max_review_rounds: 3

## Runner

- implementer: subagent          # subagent | inline (build in the main session)
- pause_between_stories: false   # true = ask before starting each next story

## Notes
- {{any project-specific guidelines, constraints, or conventions}}
