#!/usr/bin/env python3
"""Plan and track story runs for the story-runner skill.

A run is an execution batch of stories — not a planning object. Its state lives in
``spec/runs/<run-id>/run.json`` so a run can be resumed in a later session.

Usage:
    run_state.py plan S-auth-004 S-auth-005        # explicit stories (ordered by dependencies)
    run_state.py plan --epic E-03                   # every unfinished story in an epic
    run_state.py plan --ready --priority P1 --limit 5   # next N Ready stories
    run_state.py new  <same selection args> --branch auto|<name> --base <sha>   # auto = run/<run-id>
    run_state.py show <run-id|latest> [--json]
    run_state.py set  <run-id> [--run-status S] [--story ID --gate G --state S --review TEXT
                               --commit SHA --blocked REASON] [--close-gate G --close-review TEXT]
                               [--note TEXT]
    run_state.py latest                             # most recent unfinished run id (exit 1 if none)

Exit codes: 0 ok · 1 plan has blocking problems / nothing found · 2 usage or data error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STORY_ID = re.compile(r"\bS-[a-z0-9]+-\d{3}\b")
EPIC_ID = re.compile(r"\bE-\d{2,}\b")
CANONICAL = ("Backlog", "Ready", "In Progress", "In Review", "Done", "Split")
# Free-form status text seen in real projects → canonical status. First match wins, so more specific
# phrases ("ready to ship") come before the words they contain ("ready", "ship").
STATUS_KEYWORDS = [
    (("superseded", "split", "not needed", "cancelled", "canceled", "dropped"), "Split"),
    (("ready to ship", "implementation complete", "in review", "implemented", "awaiting review"), "In Review"),
    (("done", "complete", "shipped", "closed", "merged"), "Done"),
    (("in progress", "test plan written", "tests written", "testing", "implementation", "blocked", "wip"),
     "In Progress"),
    (("ready",), "Ready"),
    (("backlog", "planning", "planned", "proposed", "draft", "todo", "to do", "not started"), "Backlog"),
]
STATUS_LINE = re.compile(r"^[ \t]*(?:[-*][ \t]+)?(?:\*\*)?(Status|Current phase)(?:\*\*)?[ \t]*:[ \t]*(?:\*\*)?[ \t]*(.+?)[ \t]*$",
                         re.MULTILINE | re.IGNORECASE)
FINISHED = {"Done", "Split"}
GATES = ["ready", "build", "review", "dod"]
STORY_STATES = {"pending", "active", "blocked", "escalated", "done", "skipped"}
RUN_STATUSES = {"planned", "running", "paused", "escalated", "closing", "done", "aborted"}
PRIORITY_RANK = {"P1": 1, "P2": 2, "P3": 3}


# ── Reading stories ──────────────────────────────────────────────────────────


def header_field(text: str, name: str) -> str | None:
    """Return a ``**Name:** value`` header field, stopping at a `·` separator or line end."""
    m = re.search(rf"\*\*{re.escape(name)}:\*\*\s*([^·\n]*)", text)
    return m.group(1).strip() if m else None


def read_status_value(status_text: str) -> str | None:
    """Return the raw status from ``status.md``: ``**Status:**``, plain ``Status:``, or legacy ``Current phase``.

    A ``Status`` line wins over ``Current phase``; within each, the first occurrence wins.
    """
    found = {m.group(1).lower(): m.group(2) for m in reversed(list(STATUS_LINE.finditer(status_text)))}
    return found.get("status") or found.get("current phase")


def normalize_status(raw: str) -> str:
    """Map a status value — canonical or free-form (``Ready to ship``, ``complete``) — to a canonical one.

    Unrecognized text maps to ``In Progress`` so it is never mistaken for finished work.
    """
    text = raw.strip().strip("*`").lower()
    for canonical in CANONICAL:
        if text == canonical.lower():
            return canonical
    for words, canonical in STATUS_KEYWORDS:
        if any(re.search(rf"\b{re.escape(w)}\b", text) for w in words):
            return canonical
    return "In Progress"


def read_story(repo: Path, story_id: str) -> dict:
    """Collect the facts the runner needs about one story.

    Args:
        repo: Project root.
        story_id: Story ID such as ``S-auth-005``.

    Returns:
        Dict with id, folder, title, status, priority, epic, depends_on, and whether it is known
        at all (has a folder, or is mentioned in ``spec/backlog.md``).
    """
    folder, story_file = None, None
    for parent, name in (("spec/stories", "story.md"), ("spec/features", "feature.md")):
        dirs = sorted(d for d in (repo / parent).glob(f"{story_id}-*") if d.is_dir())
        if dirs:
            folder, story_file = dirs[0], dirs[0] / name
            break
    info = {"id": story_id, "folder": None, "title": "", "status": "No folder", "priority": None,
            "epic": None, "depends_on": [], "known": False}
    if folder is None:
        backlog = repo / "spec" / "backlog.md"
        info["known"] = backlog.is_file() and story_id in backlog.read_text()
        return info

    info.update(folder=str(folder.relative_to(repo)), known=True)
    text = story_file.read_text() if story_file.is_file() else ""
    title = re.search(r"^#\s+\S+\s+—\s+(.+)$", text, re.MULTILINE)
    info["title"] = title.group(1).strip() if title else ""
    prio = header_field(text, "Priority")
    info["priority"] = prio if prio in PRIORITY_RANK else None
    epic = header_field(text, "Epic")
    info["epic"] = EPIC_ID.search(epic).group(0) if epic and EPIC_ID.search(epic) else None
    deps = header_field(text, "Depends on") or ""
    legacy_deps = re.search(r"^## Dependencies\n((?:- .*\n?)+)", text, re.MULTILINE)
    if legacy_deps:
        deps += " " + legacy_deps.group(1)
    info["depends_on"] = sorted(set(STORY_ID.findall(deps)) - {story_id})

    status_file = folder / "status.md"
    status_text = status_file.read_text() if status_file.is_file() else ""
    raw = read_status_value(status_text)
    info["status"] = normalize_status(raw) if raw else "Backlog"
    info["raw_status"] = raw
    return info


def all_story_ids(repo: Path) -> list[str]:
    """Every story ID that has a folder."""
    ids = set()
    for parent in ("spec/stories", "spec/features"):
        for d in (repo / parent).glob("S-*"):
            m = STORY_ID.match(d.name)
            if d.is_dir() and m:
                ids.add(m.group(0))
    return sorted(ids)


def epic_story_ids(repo: Path, epic_id: str) -> list[str]:
    """Stories listed in the epic's ``epic.md`` plus stories whose header names the epic."""
    ids: list[str] = []
    for d in sorted((repo / "spec" / "epics").glob(f"{epic_id}-*")):
        if (d / "epic.md").is_file():
            ids += STORY_ID.findall((d / "epic.md").read_text())
    ids += [s for s in all_story_ids(repo) if read_story(repo, s)["epic"] == epic_id]
    return list(dict.fromkeys(ids))


# ── Planning ─────────────────────────────────────────────────────────────────


def topo_order(stories: list[dict]) -> tuple[list[dict], list[str]]:
    """Order stories so dependencies come first, keeping the given order otherwise.

    Returns:
        ``(ordered, cycle_ids)`` — cycle_ids is non-empty if the dependencies contain a cycle.
    """
    ids = {s["id"] for s in stories}
    pending = list(stories)
    done: set[str] = set()
    ordered: list[dict] = []
    while pending:
        nxt = next((s for s in pending if all(d in done or d not in ids for d in s["depends_on"])), None)
        if nxt is None:
            return ordered, [s["id"] for s in pending]
        ordered.append(nxt)
        done.add(nxt["id"])
        pending.remove(nxt)
    return ordered, []


def next_gate(status: str) -> str:
    """The first run gate a story still has to pass, given its status."""
    return {"No folder": "ready", "Backlog": "ready", "Ready": "build", "In Progress": "build",
            "In Review": "review", "Done": "done"}.get(status, "ready")


def plan(repo: Path, args: argparse.Namespace) -> dict:
    """Resolve a selection into an ordered, validated run plan."""
    notes: list[str] = []
    if args.epic:
        ids = epic_story_ids(repo, args.epic)
        selection = f"epic {args.epic}"
        if not ids:
            notes.append(f"no stories found for {args.epic}")
    elif args.ready:
        cands = [read_story(repo, s) for s in all_story_ids(repo)]
        cands = [s for s in cands if s["status"] == "Ready" or (args.include_backlog and s["status"] == "Backlog")]
        if args.priority:
            cands = [s for s in cands if s["priority"] == args.priority]
        cands.sort(key=lambda s: (PRIORITY_RANK.get(s["priority"] or "", 9), s["id"]))
        ids = [s["id"] for s in cands]
        selection = "ready" + (f" {args.priority}" if args.priority else "") + (f" limit {args.limit}" if args.limit else "")
    else:
        ids = list(dict.fromkeys(args.stories))
        selection = "stories " + " ".join(ids)
    if not ids and not notes:
        notes.append("selection is empty")

    stories = [read_story(repo, s) for s in ids]
    excluded = [{"id": s["id"], "reason": f"already {s['status']}"} for s in stories if s["status"] in FINISHED]
    unknown = [s["id"] for s in stories if not s["known"]]
    stories = [s for s in stories if s["status"] not in FINISHED and s["known"]]

    # Dependencies outside the run must already be Done; in query mode drop such stories instead.
    status_cache: dict[str, str] = {}
    def dep_status(d: str) -> str:
        if d not in status_cache:
            status_cache[d] = read_story(repo, d)["status"]
        return status_cache[d]

    in_run = {s["id"] for s in stories}
    external = []
    for s in list(stories):
        waiting = [d for d in s["depends_on"] if d not in in_run and dep_status(d) not in FINISHED]
        if waiting and args.ready:
            stories.remove(s)
            excluded.append({"id": s["id"], "reason": f"waits on {', '.join(waiting)}"})
        elif waiting:
            external.append({"id": s["id"], "waits_on": [{"id": d, "status": dep_status(d)} for d in waiting]})
    if args.ready and args.limit:
        stories = stories[: args.limit]
        # Keep the limited set closed under dependencies.
        kept = {s["id"] for s in stories}
        for s in list(stories):
            missing = [d for d in s["depends_on"] if d not in kept and dep_status(d) not in FINISHED]
            if missing:
                stories.remove(s)
                excluded.append({"id": s["id"], "reason": f"depends on {', '.join(missing)} (outside limit)"})

    ordered, cycle = ([], []) if not stories else topo_order(stories)
    for s in ordered:
        s["next_gate"] = next_gate(s["status"])
    problems = []
    if cycle:
        problems.append(f"dependency cycle among: {', '.join(cycle)}")
    if unknown:
        problems.append(f"unknown stories (no folder, not in backlog): {', '.join(unknown)}")
    if external:
        problems.append("stories depend on unfinished stories outside the run: "
                        + "; ".join(f"{e['id']} → " + ", ".join(f"{w['id']} ({w['status']})" for w in e["waits_on"]) for e in external))
    if not ordered and not problems:
        problems.append("nothing to run")
    return {"selection": selection, "stories": ordered, "excluded": excluded, "external": external,
            "unknown": unknown, "cycle": cycle, "problems": problems, "notes": notes}


def render_plan(p: dict) -> str:
    """Human-readable plan."""
    lines = [f"Run plan — {p['selection']}", "", " #  Story           Status        Next gate  Pri  Depends on",]
    for i, s in enumerate(p["stories"], 1):
        lines.append(f" {i:<2} {s['id']:<15} {s['status']:<13} {s['next_gate']:<10} {s['priority'] or '-':<4} "
                     f"{', '.join(s['depends_on']) or 'none'}")
    for e in p["excluded"]:
        lines.append(f"    excluded {e['id']}: {e['reason']}")
    for n in p["notes"]:
        lines.append(f"    note: {n}")
    lines.append("")
    lines += [f"PROBLEM: {x}" for x in p["problems"]] or ["OK — no blocking problems"]
    return "\n".join(lines)


# ── Run files ────────────────────────────────────────────────────────────────


def runs_dir(repo: Path) -> Path:
    return repo / "spec" / "runs"


def new_run_id(repo: Path) -> str:
    """Next free ``R-YYYY-MM-DD-<letter>`` id for today."""
    today = datetime.now().astimezone().date().isoformat()
    used = {d.name for d in runs_dir(repo).glob(f"R-{today}-*")}
    for c in "abcdefghijklmnopqrstuvwxyz":
        if f"R-{today}-{c}" not in used:
            return f"R-{today}-{c}"
    raise RuntimeError("more than 26 runs today")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_run(repo: Path, run_id: str) -> tuple[Path, dict]:
    """Load ``run.json`` for a run id (or ``latest``)."""
    if run_id == "latest":
        found = latest_run(repo)
        if found is None:
            raise FileNotFoundError("no unfinished run")
        run_id = found
    path = runs_dir(repo) / run_id / "run.json"
    return path, json.loads(path.read_text())


def save_run(path: Path, run: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run, indent=2) + "\n")


def latest_run(repo: Path) -> str | None:
    """Most recent run whose status is not done or aborted."""
    for d in sorted(runs_dir(repo).glob("R-*"), reverse=True):
        f = d / "run.json"
        if f.is_file() and json.loads(f.read_text()).get("status") not in {"done", "aborted"}:
            return d.name
    return None


def render_run(run: dict) -> str:
    """Progress table: ✓ passed · ● current · ✗ blocked/escalated here · · not reached."""
    head = (f"Run {run['run']} · {run['status']} · branch {run.get('branch') or '-'} · "
            f"base {(run.get('base') or '-')[:7]}")
    lines = [head, "", " #  Story           DoR  Build  Review  DoD   Review state          Commits  Notes"]
    for i, s in enumerate(run["stories"], 1):
        cur = GATES.index(s["gate"]) if s["gate"] in GATES else len(GATES)
        marks = []
        for g_i, _ in enumerate(GATES):
            if s["state"] == "skipped":
                marks.append("-")
            elif g_i < cur:
                marks.append("✓")
            elif g_i == cur:
                marks.append("✗" if s["state"] in {"blocked", "escalated"} else ("●" if s["state"] == "active" else "·"))
            else:
                marks.append("·")
        note = s.get("blocked") or ""
        lines.append(f" {i:<2} {s['id']:<15} {marks[0]:<4} {marks[1]:<6} {marks[2]:<7} {marks[3]:<5} "
                     f"{(s.get('review') or '-'):<21} {len(s.get('commits', [])):<8} {note}")
    c = run["close"]
    lines += ["", f"Close: {c['gate']}" + (f" · {c['review']}" if c.get("review") else "")]
    return "\n".join(lines)


def cmd_new(repo: Path, args: argparse.Namespace) -> int:
    p = plan(repo, args)
    if p["problems"]:
        print(render_plan(p))
        print("\nRun not created — resolve the problems above first.", file=sys.stderr)
        return 1
    run_id = new_run_id(repo)
    run = {
        "schema": 1, "run": run_id, "created": now(), "selection": p["selection"],
        "status": "planned", "branch": f"run/{run_id}" if args.branch == "auto" else args.branch,
        "base": args.base,
        "config": dict(kv.split("=", 1) for kv in args.config),
        "stories": [{"id": s["id"], "title": s["title"], "gate": s["next_gate"], "state": "pending",
                     "review": None, "commits": [], "blocked": None} for s in p["stories"]],
        "close": {"gate": "pending", "review": None},
        "log": [{"at": now(), "event": f"run created: {p['selection']}"}],
    }
    save_run(runs_dir(repo) / run_id / "run.json", run)
    print(run_id)
    return 0


def cmd_set(repo: Path, args: argparse.Namespace) -> int:
    path, run = load_run(repo, args.run)
    events = []
    if args.run_status:
        if args.run_status not in RUN_STATUSES:
            raise ValueError(f"run status must be one of {sorted(RUN_STATUSES)}")
        run["status"] = args.run_status
        events.append(f"run → {args.run_status}")
    if args.story:
        s = next((x for x in run["stories"] if x["id"] == args.story), None)
        if s is None:
            raise ValueError(f"{args.story} is not in {run['run']}")
        if args.gate:
            if args.gate not in GATES + ["done"]:
                raise ValueError(f"gate must be one of {GATES + ['done']}")
            s["gate"] = args.gate
        if args.state:
            if args.state not in STORY_STATES:
                raise ValueError(f"state must be one of {sorted(STORY_STATES)}")
            s["state"] = args.state
        if args.review:
            s["review"] = args.review
        if args.commit and args.commit not in s["commits"]:
            s["commits"].append(args.commit)
        if args.blocked is not None:
            s["blocked"] = args.blocked or None
        events.append(f"{args.story}: " + ", ".join(
            f"{k}={v}" for k, v in (("gate", args.gate), ("state", args.state), ("review", args.review),
                                    ("commit", args.commit and args.commit[:10]), ("blocked", args.blocked)) if v))
    if args.close_gate:
        run["close"]["gate"] = args.close_gate
        events.append(f"close → {args.close_gate}")
    if args.close_review:
        run["close"]["review"] = args.close_review
    if args.note:
        events.append(args.note)
    run["log"].append({"at": now(), "event": "; ".join(events) or "update"})
    save_run(path, run)
    print(render_run(run))
    return 0


def add_selection_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("stories", nargs="*", help="story IDs (explicit selection)")
    p.add_argument("--epic", help="select every unfinished story in this epic")
    p.add_argument("--ready", action="store_true", help="select Ready stories")
    p.add_argument("--include-backlog", action="store_true", help="with --ready, also include Backlog stories")
    p.add_argument("--priority", choices=sorted(PRIORITY_RANK), help="with --ready, filter by priority")
    p.add_argument("--limit", type=int, help="with --ready, at most N stories")


def main() -> int:
    """CLI entrypoint. See the module docstring for usage."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="project root (default: .)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="resolve and order a selection")
    add_selection_args(p_plan)
    p_plan.add_argument("--json", action="store_true")

    p_new = sub.add_parser("new", help="create a run from a selection")
    add_selection_args(p_new)
    p_new.add_argument("--branch", required=True, help="branch name, or 'auto' for run/<run-id>")
    p_new.add_argument("--base", required=True)
    p_new.add_argument("--config", nargs="*", default=[], metavar="KEY=VALUE")

    p_show = sub.add_parser("show", help="show a run")
    p_show.add_argument("run")
    p_show.add_argument("--json", action="store_true")

    p_set = sub.add_parser("set", help="update a run")
    p_set.add_argument("run")
    p_set.add_argument("--run-status")
    p_set.add_argument("--story")
    p_set.add_argument("--gate")
    p_set.add_argument("--state")
    p_set.add_argument("--review")
    p_set.add_argument("--commit")
    p_set.add_argument("--blocked", help="reason, or empty string to clear")
    p_set.add_argument("--close-gate")
    p_set.add_argument("--close-review")
    p_set.add_argument("--note")

    sub.add_parser("latest", help="print the most recent unfinished run id")

    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        if args.cmd == "plan":
            if sum(bool(x) for x in (args.stories, args.epic, args.ready)) != 1:
                parser.error("give exactly one of: story IDs, --epic, --ready")
            p = plan(repo, args)
            print(json.dumps(p, indent=2) if args.json else render_plan(p))
            return 1 if p["problems"] else 0
        if args.cmd == "new":
            if sum(bool(x) for x in (args.stories, args.epic, args.ready)) != 1:
                parser.error("give exactly one of: story IDs, --epic, --ready")
            return cmd_new(repo, args)
        if args.cmd == "show":
            _, run = load_run(repo, args.run)
            print(json.dumps(run, indent=2) if args.json else render_run(run))
            return 0
        if args.cmd == "set":
            return cmd_set(repo, args)
        if args.cmd == "latest":
            found = latest_run(repo)
            print(found or "none")
            return 0 if found else 1
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
