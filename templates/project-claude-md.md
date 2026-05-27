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

## Notes
- {{any project-specific guidelines, constraints, or conventions}}
