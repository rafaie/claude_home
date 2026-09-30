# claude_home

SDLC skill pack for Claude Code — a port of [codex_home](https://github.com/rafaie/codex_home) to the Claude Code plugin system.

Provides 23 model-invoked SDLC skills (plus a utility skill) and two agents that implement a story-centric development workflow: **Epic → Story → Task**, with every story gated by an independent review. Skills trigger automatically based on what you ask; no `/` prefix needed.

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
| backlog-builder | "build the backlog", "create epics and stories" |
| feature-kickoff | "kick off story S-core-001", "create epic E-01" |
| feature-slicer | "split this epic into stories", "this story is too big" |

### Implementation

| Skill | Trigger by saying... |
|---|---|
| implementation-phase | "run implementation phase for S-core-001", "take this story through review" |
| implement-feature | "implement feature S-core-001", "code this feature" |

### Review

| Skill | Trigger by saying... |
|---|---|
| independent-review | "review S-core-001 independently", "re-review this story", "review epic E-01", "waive finding F3" |

### Running several stories

| Skill | Trigger by saying... |
|---|---|
| story-runner | "run S-core-001 S-core-002 S-api-004", "run epic E-01", "run the next 5 ready P1 stories", "resume the run" |

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
| ship-feature | "ship S-core-001", "mark this story done" |
| debug-loop | "debug this failure", "tests are failing", "fix this error" |
| failure-triage | "triage failures", "multiple tests failing" |
| work-item-status | "what's the status of S-core-001", "status of epic E-01" |

### Maintenance & Quality

| Skill | Trigger by saying... |
|---|---|
| architecture-review | "review ADRs", "document this decision", "update architecture doc" |
| docs-update | "update docs after shipping", "add changelog entry", "refresh the spec index" |
| spec-linter | "is this story ready?", "check the definition of ready" |
| flaky-test-hunter | "find flaky tests", "stabilize this flaky test" |
| release-prep | "prepare release", "run release checks" |

### Utilities

| Skill | Trigger by saying... |
|---|---|
| md-to-html | "convert this markdown to html", "make a nice html page from this md file" |

## Work Hierarchy

Work is organized as **Epic → Story → Task** — the same shape as Jira, Linear, or GitHub issues with
sub-issues. The full model is in [references/hierarchy.md](references/hierarchy.md).

| Level | ID | Lives at | Notes |
|---|---|---|---|
| Epic (optional) | `E-<nn>` | `spec/epics/E-<nn>-<slug>/epic.md` | An outcome that groups stories |
| Story | `S-<area>-<nnn>` | `spec/stories/S-<area>-<nnn>-<slug>/` | The unit that is tested, reviewed, and marked Done |
| Task | — | checklist in the story's `implementation.md` | Implementation steps |

Area (`core`, `api`, …), priority, dependencies, and milestone are attributes, not levels.

Story status: `Backlog → Ready → In Progress → In Review → Done`

- **Ready** — the Definition of Ready passed (spec-linter)
- **In Review** — code is committed and the independent review is running or in its fix loop
- **Done** — the Definition of Done passed, including the review gate (ship-feature)

### Independent review

Every story is reviewed by a reviewer that has **never seen the implementation conversation**: either a
fresh-context subagent (`agents/independent-reviewer.md`) or a separate `claude -p` process
(`scripts/headless_review.sh`). The reviewer is read-only, gets a fixed prompt (ACs, diff range, rubric),
and writes `reviews/r<N>.json` + `r<N>.md` in the story folder.

The gate is checked by `scripts/gate_check.py`, not by the model: **0 open high and 0 open medium
findings, every AC met, and the review pinned to the current code**. Failing findings go through a
fix → commit → re-review loop, with a fresh reviewer each round and at most 3 rounds before it asks you. Only
you can waive a finding. Low findings become backlog follow-ups.

Severity rules and the JSON format are in [references/review-rubric.md](references/review-rubric.md).

### Story runs

The story-runner skill takes any set of stories — explicit IDs, an epic, or "the next N Ready stories" —
orders them by dependency, asks you to approve the plan, then takes each one through:

```
Definition of Ready → Build → Independent Review (fix loop) → Definition of Done
```

Each story is built by a fresh `story-implementer` agent and reviewed by a fresh `independent-reviewer`;
the two never see each other's context. After the last story, the run gets full checks and an
integration review of the combined diff, and a report in `spec/runs/<run-id>/run-report.md`.

It works on a `run/<run-id>` branch with one commit per story step, never pushes, and pauses to ask you
only when something escalates (review round limit, disputed finding, missing requirements). State is
kept in `spec/runs/<run-id>/run.json` by `scripts/run_state.py`, so "resume the run" continues where it
stopped:

```
Run R-2026-09-30-a · running · branch run/R-2026-09-30-a · base a1b2c3d

 #  Story        DoR  Build  Review  DoD   Review state          Commits  Notes
 1  S-auth-004   ✓    ✓      ✓       ✓     r1 PASS @ 9f8e7d6     2
 2  S-auth-005   ✓    ✓      ●       ·     r1 FAIL (1H)          2
 3  S-api-011    ·    ·      ·       ·     -                     0

Close: pending
```

### Migrating existing projects

Projects created with the earlier layout (`spec/features/<id>/feature.md`) keep working — skills read
them as stories. To migrate in one step (dry run first):

```bash
python3 ~/git/claude_home/scripts/migrate_spec.py
python3 ~/git/claude_home/scripts/migrate_spec.py --apply
```

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

Optionally configure the reviewer with a `## Review` section:

```markdown
## Review

- reviewer: subagent        # subagent | headless (separate `claude -p` process)
- reviewer_model: inherit   # or a model name/alias for the reviewer
- max_review_rounds: 3
```

and the story runner with a `## Runner` section:

```markdown
## Runner

- implementer: subagent          # subagent | inline (build in the main session)
- pause_between_stories: false   # true = ask before starting each next story
```

## License

Apache-2.0
