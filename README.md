# claude_home

SDLC skill pack for Claude Code — a port of [codex_home](https://github.com/rafaie/codex_home) to the Claude Code plugin system.

Provides 23 model-invoked skills that implement a work-item-centric development workflow. Skills trigger automatically based on what you ask; no `/` prefix needed.

## Install

```bash
git clone https://github.com/rafaie/claude_home ~/git/claude_home
cd ~/git/claude_home
chmod +x install.sh
./install.sh
source ~/.zshrc   # or ~/.bash_profile
```

`install.sh` does two things:
1. Adds a shell alias so `claude` always loads this plugin
2. Installs the global `CLAUDE.md` instructions to `~/.claude/CLAUDE.md`

To overwrite an existing `~/.claude/CLAUDE.md` instead of appending:
```bash
./install.sh --copy
```

To load the plugin without installing:
```bash
claude --plugin-dir /path/to/claude_home
```

## Skills

All skills are **model-invoked** — Claude triggers them based on context.
Just describe what you want to do.

### Intake & Planning

| Skill | Trigger by saying... |
|---|---|
| session-start | "what should we work on?", "what's the project status?" |
| project-intake | "bootstrap this project", "set up SDLC for this repo" |
| qa-intake | "clarify requirements for S-core-001", "qa intake for this feature" |
| backlog-builder | "build the backlog", "organize work items into streams" |
| feature-kickoff | "kick off feature S-core-001", "create work item docs" |
| feature-slicer | "slice this feature", "break down into smaller pieces" |

### Implementation

| Skill | Trigger by saying... |
|---|---|
| implementation-phase | "run implementation phase for S-core-001", "full implementation cycle" |
| implement-feature | "implement feature S-core-001", "code this feature" |

### Testing

| Skill | Trigger by saying... |
|---|---|
| test-plan | "create test plan for S-core-001", "write test strategy" |
| write-tests | "write tests for S-core-001", "generate tests" |
| test-runner | "run tests", "run the test suite", "check test status" |
| smoke-test | "run smoke tests for S-core-001", "validate with smoke" |

### Shipping

| Skill | Trigger by saying... |
|---|---|
| ship-feature | "ship feature S-core-001", "finalize and ship" |
| debug-loop | "debug this failure", "tests are failing", "fix this error" |
| failure-triage | "triage failures", "multiple tests failing" |

### Maintenance & Quality

| Skill | Trigger by saying... |
|---|---|
| adr-review | "review ADRs", "do we need an ADR for this?" |
| architecture-updater | "update architecture doc", "sync architecture with code" |
| docs-update | "update docs after shipping", "add changelog entry" |
| docs-index-refresh | "refresh the spec index", "update spec/index.md" |
| spec-linter | "review this spec", "is the spec ready?" |
| flaky-test-hunter | "find flaky tests", "stabilize this flaky test" |
| feature-closeout | "close out feature S-core-001" *(deprecated)* |
| release-prep | "prepare release", "run release checks" |

## Work Item ID Format

Work items use the format `S-<stream>-<nnn>` (e.g. `S-core-001`, `S-api-002`).
Documentation lives at `spec/features/<work-id>-<slug>/`.

## Per-Project Configuration

Add a `## Commands` section to your project's `CLAUDE.md` to override defaults:

```markdown
## Commands

- test_quick: uv run pytest -q
- test_full: uv run pytest -q
- lint: uv run ruff check .
- format: uv run ruff format . --check
- typecheck: uv run mypy src
- smoke: uv run python scripts/smoke.py
```

## License

Apache-2.0
