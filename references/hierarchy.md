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

| Status | Entered when | Set by |
|---|---|---|
| Backlog | Story folder created | feature-kickoff |
| Ready | Definition of Ready passes | spec-linter |
| In Progress | Work starts; `Base commit` recorded | implementation-phase / test-plan / implement-feature |
| In Review | Code committed; independent review requested or in fix loop | independent-review |
| Done | Definition of Done passes (incl. review gate) | ship-feature |

`Split` is a terminal status outside the workflow: the story was replaced by the stories listed in its
`Superseded by:` line (set by feature-slicer).

Blocking is a flag, not a status: `**Blockers:**` in `status.md` is `none` or a list of reasons.
Steps such as "test plan written" or "tests written" are progress *within* In Progress, recorded in
`status.md` History — not statuses.

Epic status is derived: `Backlog` (no story started) → `In Progress` (any story started) → `Done`
(all stories Done and the epic integration review passed).

## Gates

| Gate | Checks | Enforced by |
|---|---|---|
| **Definition of Ready** | Story statement clear; every AC has an ID and is testable; dependencies Done or non-blocking; out-of-scope listed; no blocking open questions; sized for one focused session | spec-linter |
| **Review gate** | Latest independent review has 0 open high and 0 open medium findings (after user waivers), no AC `not_met`/`partial`, and the review is pinned to the current code | `scripts/gate_check.py` |
| **Definition of Done** | All ACs pass (tests reference AC IDs); full checks pass; smoke passes; review gate passes; docs updated if user-facing | ship-feature |

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

When writing to a legacy folder, keep its layout — do not partially migrate. To migrate a project in one
step, run (dry run by default):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py"          # show planned changes
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/migrate_spec.py" --apply  # perform them
```
