---
name: story-runner
description: This skill should be used when the user asks to "run S-auth-004 S-auth-005 S-api-011", "run these stories", "run epic E-03", "run the next 5 ready stories", "run all ready P1 stories", "resume the run", "resume run R-2026-09-30-a", or wants several stories (work items) taken end to end — ready check, build, independent review, done — one after another with gates between them.
version: 1.0.0
---

# Story Runner

Run a batch of stories end to end, one at a time, each through the same gates:
**Definition of Ready → Build → Independent Review → Definition of Done**, then close the run with an
integration review of the combined change. A run is an execution batch, not a planning object — pick any
stories when you start it.

References:
- `${CLAUDE_PLUGIN_ROOT}/references/hierarchy.md` — stories, statuses, gates
- `${CLAUDE_PLUGIN_ROOT}/scripts/run_state.py` — plans the order and keeps `spec/runs/<run-id>/run.json`
- `${CLAUDE_PLUGIN_ROOT}/agents/story-implementer.md` — builds or fixes one story in its own context
- The independent-review skill — reviews each story; its integrity rules apply here unchanged
- `${CLAUDE_PLUGIN_ROOT}/references/graphify.md` — optional knowledge graph (`GR` = `scripts/graph.py`)

Below, `RS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_state.py"` and `GC` means
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gate_check.py"`.

## Roles

The runner (you, in the main session) orchestrates and never writes feature code itself when
`implementer: subagent`. It launches two kinds of agents that never talk to each other:

| Role | Does | Never |
|---|---|---|
| **story-implementer** (fresh per story, and per fix round) | test plan → tests → code → checks → commit | reviews, marks Done, touches `reviews/` |
| **independent-reviewer** (via the independent-review skill, fresh per round) | reviews base..head, writes `r<N>.json` | sees the implementer's replies or this conversation |

Nothing from an implementer's reply is ever passed to a reviewer.

## Configuration

Read the project `CLAUDE.md`: `## Commands`, `## Review` (see independent-review), and an optional:

```markdown
## Runner
- implementer: subagent          # subagent | inline (build in the main session)
- pause_between_stories: false   # true = ask before starting each next story
```

Use `inline` only for small runs or when subagents are unavailable; it fills the main context faster.

## Step 1: Resolve the selection

| User says | Command |
|---|---|
| "run S-a S-b S-c" | `RS plan S-a S-b S-c` |
| "run epic E-03" | `RS plan --epic E-03` |
| "run the next 5 ready P1 stories" | `RS plan --ready --priority P1 --limit 5` |
| "…including backlog stories" | add `--include-backlog` |
| "resume" / "resume run R-…" | go to **Resume** |

`plan` orders stories so dependencies come first and reports problems:
- **Dependency cycle / unknown stories** — stop and report.
- **Depends on an unfinished story outside the run** — ask the user: add that story to the run, drop
  the dependent story, or stop.
- **Excluded** stories (already Done/Split, or waiting on others in query mode) — list them.

## Step 2: Preconditions and approval

1. `git status --porcelain` must show no uncommitted changes outside `spec/`, `artifacts/`,
   `graphify-out/`, or Markdown.
   Otherwise stop and ask the user to commit or stash — the runner commits per story.
2. Graph (optional): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" refresh`. If it prints
   `DOCS_PASS: needed`, run the graphify skill here in the main session (`/graphify <graph_path> --update`),
   then `graph.py mark-docs`. If the graph is `off` or `unavailable`, continue without it (a
   `graphify: required` project stops here instead).
3. Baseline: run the quick test command once. If it fails, stop: a red baseline makes every review
   ambiguous. Offer the debug-loop or failure-triage skill.
4. Show the plan table, the branch it will use, the reviewer and implementer modes, the graph state,
   and the max review rounds, then **ask the user to approve the run** (they may reorder or drop stories — re-run `plan`
   with the explicit list). Do not start without approval.
5. On approval:
   - Create the run. On the default branch pass `--branch auto` (the run gets `run/<run-id>`);
     otherwise pass the current branch name and stay on it:
     ```bash
     RS new <same selection args> --branch auto --base "$(git rev-parse HEAD)" \
        --config implementer=<mode> reviewer=<mode> max_review_rounds=<n>
     git switch -c run/<run-id>        # only when --branch auto
     RS set <run-id> --run-status running
     ```
   - Commit `spec/runs/<run-id>/run.json` as `run <run-id>: start`.

Update `run.json` with `RS set` after **every** gate transition below, so the run can be resumed at any
point. Print `RS show <run-id>` after each story finishes.

## Step 3: For each story, in order

Skip a story whose `state` is `done` or `skipped`. If a story it depends on (inside the run) is
`blocked` or `escalated`, mark it `RS set … --state blocked --blocked "waits on <id>"` and move on.

Mark it active: `RS set <run-id> --story <id> --state active`.

### Gate 1 — Definition of Ready (`gate: ready`)
- No folder → the feature-kickoff skill.
- Status `Backlog` → the spec-linter skill.
- If it is still not Ready because answers are needed from the user (unclear ACs, open questions), do
  not guess: `--state blocked --blocked "not ready: <issue>"`, collect the questions for the run report,
  and continue with the next story.
- Ready → `RS set … --gate build`.

### Gate 2 — Build (`gate: build`)

**`implementer: subagent`** — launch the `story-implementer` agent (it may be listed as
`claude-home:story-implementer`; if unavailable, use a `general-purpose` agent with the full body of
`agents/story-implementer.md` prepended). Prompt with exactly:

```
mode: build
story_id: <id>
story_folder: <absolute path>
repo_root: <absolute path>
plugin_root: <absolute path of ${CLAUDE_PLUGIN_ROOT}>
commands: <test_quick / test_full / lint / format / typecheck / smoke from CLAUDE.md>
graph_report: <absolute path to GRAPH_REPORT.md if the graph is enabled; otherwise none>
```

**`implementer: inline`** — run the implementation-phase skill yourself, steps 1–4 only.

Then verify for yourself — do not rely on the reply alone:
- `git log -1 --format=%H` is a new commit and `git status --porcelain` is clean outside spec/Markdown.
- Every AC in `story.md` is checked.

On success: `RS set … --gate review --commit <sha>`.
On `BLOCKED`: `--state blocked --blocked "<reason>"`; for "needs split", recommend feature-slicer in the
report. Continue with the next story.

### Gate 3 — Independent Review (`gate: review`)

Run the independent-review skill for the story (scope `story`). Record the result:
`RS set … --review "r<N> PASS @ <sha>"` or `"r<N> FAIL (<h>H/<m>M)"`.

**Gate FAIL → fix loop:**
1. Launch a **new** story-implementer with `mode: fix`, the same fields, plus
   `review_file: <reviews/r<N>.json>` and `waivers: <path or none>`. (Inline mode: apply the
   implementation-phase fix loop yourself.)
2. If the reply lists `DISPUTED` findings, ask the user about each: accept the finding (fix it), or waive
   it with their reason (recorded per the independent-review Waivers section). Never decide a dispute
   yourself.
3. Verify the new commit, `RS set … --commit <sha>`, then run the independent-review skill again (new
   round, fresh reviewer).

**Gate ESCALATE (round limit reached)** → `RS set … --state escalated` and
`RS set <run-id> --run-status escalated`, then ask the user now:
- allow one more round,
- waive specific findings (with their reason),
- block this story and continue with the others,
- or stop the run (it can be resumed later).

Resume according to the answer (`--run-status running`).

**Gate PASS** → `RS set … --gate dod`.

### Gate 4 — Definition of Done (`gate: dod`)

Run the ship-feature skill for the story. It re-checks the review gate, runs full checks, updates docs,
sets the story `Done`, and commits `<id>: done`.

On success: `RS set … --gate done --state done --commit <sha>`, then refresh the code graph so the next
story sees this one (`graph.py refresh`; defer any `DOCS_PASS` to the run close). If ship-feature
reports a stale gate (code changed after the review), return to Gate 3.

If `pause_between_stories` is true, ask before starting the next story.

## Step 4: Close the run

When every story is `done`, `blocked`, `escalated`, or `skipped`:

1. `RS set <run-id> --run-status closing --close-gate checks`. Refresh the graph, including a docs pass
   if `DOCS_PASS: needed` (main session), so the integration reviewer sees specs and reviews too. Run the test-runner skill in full mode on
   the run branch. Fix regressions between stories with the debug-loop skill; commit as
   `run <run-id>: fix integration`.
2. **Integration review** — if two or more stories reached `done`:
   - If every story in the run belongs to one epic and that epic is now fully Done, use the
     independent-review skill with scope `epic` (it reviews into the epic folder).
   - Otherwise use scope `range`: target folder `spec/runs/<run-id>/`, base = the run's `base`,
     head = `HEAD`, `spec_paths` = the `story.md` of every done story in the run.
   - `RS set <run-id> --close-gate review --close-review "r<N> PASS|FAIL …"`. A failing integration
     review uses the same fix loop — implementer `mode: fix` with `story_id: <run-id>`,
     `story_folder: spec/runs/<run-id>/`, the run's review file, and `spec_paths` — which commits as
     `<run-id>: address review r<N> (…)`. The same escalation rule applies.
3. For each epic that became fully Done but was not reviewed in step 2, recommend the independent-review
   skill with scope `epic`.
4. Write `spec/runs/<run-id>/run-report.md` (template below), then
   `RS set <run-id> --run-status done --close-gate done` and commit as `run <run-id>: done`.
5. Do not push, merge, or open a PR unless the user asks. Suggest it.

## Resume

1. `RS latest` (or the run id the user gave), then `RS show <run-id>`.
2. Check out the run's `branch` if not already on it.
3. Trust the repository over `run.json`: for the story in progress, use the implementation-phase
   **Partial Completion Detection** table and `GC <story-id>` to find the real gate, and correct
   `run.json` with `RS set` if it lags.
4. If the run was `escalated`, repeat the escalation question first. Then continue at Step 3.

## Stop conditions

Stop the whole run and ask the user when:
- the baseline or the closing full checks fail and debug-loop cannot fix them,
- a reviewer violates its rules (writes outside its two files),
- the working tree contains changes the runner did not make,
- or the user asks. Always `RS set <run-id> --run-status paused` first so the run can resume.

## Run report

```markdown
# Run <run-id>

**Selection:** <selection> · **Branch:** <branch> · **Base:** <sha> · **Dates:** <start> → <end>
**Result:** <k>/<n> stories Done · integration review <PASS/FAIL/n/a>

## Stories
<`RS show <run-id>` table>

## Review Summary
| Story | Rounds | Fixed (H/M) | Waived | Low → follow-ups |
|---|---|---|---|---|

## Blocked or Escalated
- <id> — <reason> — <recommended next step>

## Questions for the User
- <id>: <question collected at the Definition of Ready gate>

## Commits
<git log --oneline base..HEAD>

## Next Steps
- <e.g. open a PR from run/<run-id>; slice S-…; epic review for E-…>
```

## Final message

```
## Run <run-id> — <done | paused | escalated>
<RS show table>
Integration review: <result>
Blocked: <ids with one-line reasons, or none>
Report: spec/runs/<run-id>/run-report.md
Next: <one line>
```
