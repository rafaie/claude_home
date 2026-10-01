# Work Hierarchy — Epic → Story → Task

The single source of truth for how work is organized in projects that use claude_home.
Skills refer to this file instead of redefining the model.

## Levels

| Level | What it is | Where it lives | Gated & independently reviewed? |
|---|---|---|---|
| **Epic** (optional) | An outcome that groups related stories (e.g. "Auth hardening") | `spec/epics/E-<nn>-<slug>/epic.md` | Integration review once all its stories are Done |
| **Story** | **The unit of delivery.** One vertical slice with acceptance criteria, tests, one reviewed commit range, and one Done. | `spec/stories/S-<area>-<nnn>-<slug>/` | Yes — every gate |
| **Task** | An implementation step inside a story | Checklist in the story's `implementation.md` | No |

A story may exist without an epic. Epics never contain code directly — only stories do.

### Attributes (not levels)

| Attribute | Meaning | Recorded in |
|---|---|---|
| **Area** | Domain or layer label (`core`, `api`, `cli`, …). Formerly "stream". | `story.md` header; the `<area>` part of the ID |
| **Priority** | `P1` must-have · `P2` should-have · `P3` nice-to-have | `story.md` header, `spec/backlog.md` |
| **Depends on** | Story IDs that must be Done first | `story.md` header |
| **Milestone** | Optional release/timing label | `story.md` header |

## IDs

- Story: `S-<area>-<nnn>` — e.g. `S-auth-005`. The area prefix is fixed at creation; if the story later
  moves to another area, keep the ID and change only the Area attribute.
- Epic: `E-<nn>` — e.g. `E-03`. Folder: `E-03-auth-hardening`.
- Acceptance criteria: `AC-<n>` — numbered within a story, never renumbered once tests reference them.
- Review findings: `F<n>` — numbered within a story, stable across review rounds.

## Story status workflow

```
Backlog → Ready → In Progress → In Review → Done
```

| Status | Entered when | Set by (skill → `scripts/story_state.py`) |
|---|---|---|
| Backlog | Story folder created | feature-kickoff (from the template) |
| Ready | Definition of Ready passes | spec-linter → `story_state.py ready` |
| In Progress | Work starts; `Base commit` recorded | implementation-phase → `story_state.py start` |
| In Review | Code committed; independent review recorded (incl. fix loop) | independent-review → `story_state.py review` |
| Done | Definition of Done passes (incl. review gate and recorded checks) | ship-feature → `story_state.py done` |

`Split` is a terminal status outside the workflow: the story was replaced by the stories listed in its
`Superseded by:` line (feature-slicer → `story_state.py split`).

Status changes are made by `scripts/story_state.py`, never by editing `status.md` by hand: it updates
`status.md` (fields and History), the story's row in `spec/backlog.md`, and its row in the epic, and it
refuses a transition whose entry conditions are not met.

Blocking is a flag, not a status: `**Blockers:**` in `status.md` is `none` or a list of reasons.
Steps such as "test plan written" or "tests written" are progress *within* In Progress, recorded in
`status.md` History — not statuses.

Epic status is derived: `Backlog` (no story started) → `In Progress` (any story started) → `Done`
(all stories Done and the epic integration review passed).

## Gates

| Gate | Checks | Enforced by |
|---|---|---|
| **Definition of Ready** | Story statement clear; every AC has an ID and is testable; dependencies Done or non-blocking; out-of-scope listed; no blocking open questions; sized for one focused session | spec-linter (judgment) + `story_state.py ready` (≥ 2 numbered ACs, dependencies Done) |
| **Review gate** | Latest independent review has 0 open high and 0 open medium findings (after user waivers and the severity-change rules), no AC `not_met`/`partial`, and the review is pinned to the current code | `scripts/gate_check.py` |
| **Checks** | Format, lint, typecheck, docstrings (if configured), full tests, and smoke — with complete smoke artifacts — pass on the current code | `scripts/run_checks.py` (records and verifies results) |
| **Definition of Done** | All ACs ticked; review gate passes; recorded full checks pass on the current code; docs updated if user-facing | ship-feature + `story_state.py done` |

## Runs

A **run** is an execution batch — any set of stories taken end to end by the story-runner skill, in
dependency order, each through Definition of Ready → Build → Independent Review → Definition of Done,
then an integration review of the combined change. A run is not a planning level: choose its stories
when you start it (explicit IDs, an epic, or "the next N Ready stories").

Run state lives in `spec/runs/R-<yyyy-mm-dd>-<letter>/run.json`, managed by `scripts/run_state.py`, so a
run can be resumed in a later session. Run status: `planned → running → (paused | escalated) → closing →
done`, or `aborted`.

## Folder layout

```
spec/
├── brief.md
├── index.md
├── backlog.md                          # epics and stories with status, area, priority, dependencies
├── changelog.md
├── epics/E-03-auth-hardening/
│   ├── epic.md
│   └── reviews/                        # epic integration reviews
├── stories/S-auth-005-token-expiry/
│   ├── story.md                        # user story, AC-1..n, DoR, DoD
│   ├── implementation.md               # tasks checklist, approach, files changed, decisions
│   ├── test-plan.md
│   ├── test-results.md
│   ├── status.md
│   ├── evidence/README.md
│   └── reviews/                        # r1.json, r1.md, r2.json, … and waivers.json
├── runs/R-2026-09-30-a/
│   ├── run.json                        # order, current gate per story, commits, log
│   ├── reviews/                        # integration review of the run's combined diff
│   └── run-report.md
└── decisions/ADR-*.md
```

## Resolving a story folder (legacy compatibility)

Projects created before this model use `spec/features/<id>-<slug>/feature.md` and a
`**Current phase:**` line in `status.md`. Every skill resolves a story like this:

1. `spec/stories/<story-id>-*/` → story file `story.md`
2. otherwise `spec/features/<story-id>-*/` → story file `feature.md` (legacy)

Legacy status values map as follows when read:

| Legacy `Current phase` | Status |
|---|---|
| Planning | Backlog |
| Test Plan Written, Tests Written, Implementation, Testing | In Progress |
| Implementation Complete | In Review |
| Shipped | Done |
| Blocked | keep the prior status; record the reason under Blockers |

Free-form status text from older projects is read by keyword (`scripts/run_state.py`,
`normalize_status`): "superseded / not needed" → Split; "ready to ship / implemented / implementation
complete" → In Review; "done / complete / shipped / merged" → Done; "in progress / testing / blocked" →
In Progress; "ready" → Ready; "planned / proposed / draft" → Backlog. Anything unrecognized is treated as
In Progress, never as finished. Plain `Status:` lines (without bold) are accepted.

**Reading works everywhere; status transitions need the current layout.** Every skill can read and report
on a legacy folder (status cards, planning, session start, review gate checks). Recording a transition —
Ready, start, review result, Done, split — goes through `scripts/story_state.py`, which refuses legacy
folders rather than half-migrating them. So before a legacy story is marked Ready, reviewed, or shipped,
migrate the project — with the user's OK, dry run first — in one step:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py"          # show planned changes
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py" --apply  # perform them
```
