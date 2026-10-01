#!/usr/bin/env python3
"""Story status bookkeeping for claude_home — every status transition, done the same way every time.

Each command updates the story's ``status.md`` (status, fields, History), its row in ``spec/backlog.md``,
and its row in the epic's ``epic.md``. Transitions that have entry conditions check them first and change
nothing when a condition fails:

    ready <story> [--allow-dep ID ...]   Backlog → Ready. Needs ≥ 2 numbered ACs (``**AC-n**``) and every
                                         dependency Done or Split (``--allow-dep`` = user-approved non-blocking).
                                         Ticks the Definition of Ready.
    start <story> [--base SHA]           Ready → In Progress. Records the base commit (HEAD by default).
    review <target> [--round N]          After an independent review of a story, epic, or run: records the
                                         gate result; logs open low findings as backlog follow-ups on PASS
                                         (deduplicated by file:line) and marks follow-ups fixed by later rounds.
    done <story> [--note TEXT]           In Review → Done. Needs a PASSing, current review gate, a passing full
                                         check run on the current code (run_checks.py), and every AC ticked.
                                         Ticks the Definition of Done and the Tasks.
    block <story> --reason TEXT          Records a blocker.        unblock <story>   Clears blockers.
    split <story> --into ID [ID ...]     Marks a story Split (terminal) and records what superseded it.
    note <story> TEXT                    Adds a History line.

Stories are given by ID (``S-auth-005``) or folder. Legacy folders (``spec/features/``, ``Current phase``)
are refused — migrate them first with ``migrate_spec.py``.

Exit codes: 0 done · 1 an entry condition failed (nothing changed) · 2 usage error or unsupported folder
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_check
import run_checks
import run_state


def today() -> str:
    """Local calendar date, as written in History lines."""
    return datetime.now().astimezone().date().isoformat()


STORY_ID = re.compile(r"S-[a-z0-9]+-\d{3}")
FINISHED = {"Done", "Split"}
UNSET_BASE = {"", "not started", "unknown", "unknown (migrated)", "none"}


class ConditionError(Exception):
    """An entry condition for a transition is not met; nothing was changed."""


class UsageError(Exception):
    """The target cannot be handled (not found, or a legacy/non-standard folder)."""


# ── Markdown helpers ─────────────────────────────────────────────────────────


def get_field(text: str, name: str) -> str | None:
    """Value of a ``**Name:** value`` line (up to a ``·`` separator), or None."""
    m = re.search(rf"^\*\*{re.escape(name)}:\*\*[ \t]*([^·\n]*)", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def set_field(text: str, name: str, value: str) -> str:
    """Set a ``**Name:** value`` line; insert it after the Status line if missing."""
    line = f"**{name}:** {value}"
    pattern = re.compile(rf"^\*\*{re.escape(name)}:\*\*[^\n]*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda _: line, text, count=1)
    status = re.search(r"^\*\*Status:\*\*[^\n]*$", text, re.MULTILINE)
    at = status.end() if status else 0
    return text[:at] + ("\n" if at else "") + line + ("" if at else "\n") + text[at:]


def add_history(text: str, entry: str) -> str:
    """Append ``- <today> — entry`` at the end of the History section (creating it if missing)."""
    line = f"- {today()} — {entry}"
    m = re.search(r"^## History[ \t]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return text.rstrip("\n") + f"\n\n## History\n{line}\n"
    body = m.group(1).rstrip("\n")
    return text[: m.start(1)] + (body + "\n" if body else "") + line + "\n" + ("\n" if m.end(1) < len(text) else "") + text[m.end(1):].lstrip("\n")


def tick_section(text: str, heading: str) -> str:
    """Tick every checkbox in the ``## <heading>`` section."""
    m = re.search(rf"^## {re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return text
    return text[: m.start(1)] + m.group(1).replace("- [ ]", "- [x]") + text[m.end(1):]


def set_row_status(text: str, item_id: str, value: str) -> str:
    """Set the Status of ``item_id`` in Markdown tables (Status column) and in ``### <id> …`` blocks."""
    lines, col = text.splitlines(), None
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            col = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if "Status" in cells:
            col = cells.index("Status")
        elif col is not None and cells and col < len(cells):
            first = re.sub(r"[`*\[\]]", "", cells[0]).strip()
            if first == item_id or first.startswith((item_id + " ", item_id + "—")):
                cells[col] = value
                lines[i] = "| " + " | ".join(cells) + " |"
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # Block form: a heading containing the ID followed by a **Status:** line before the next heading.
    m = re.search(rf"^#+[^\n]*\b{re.escape(item_id)}\b[^\n]*\n(.*?)(?=^#|\Z)", text, re.MULTILINE | re.DOTALL)
    if m and "**Status:**" in m.group(1):
        block = re.sub(r"(\*\*Status:\*\*[ \t]*)[^·\n]*?([ \t]*(?:·|$))", lambda x: x.group(1) + value + x.group(2),
                       m.group(1), count=1, flags=re.MULTILINE)
        text = text[: m.start(1)] + block + text[m.end(1):]
    return text


# ── Story context ────────────────────────────────────────────────────────────


class Story:
    """A story folder in the current (non-legacy) layout."""

    def __init__(self, repo: Path, folder: Path):
        self.repo, self.folder = repo, folder
        self.status_md, self.story_md = folder / "status.md", folder / "story.md"
        if not self.story_md.is_file():
            raise UsageError(f"{folder} has no story.md — legacy folders must be migrated first "
                             f"(scripts/migrate_spec.py)")
        if not self.status_md.is_file() or get_field(self.status_md.read_text(), "Status") is None:
            raise UsageError(f"{self.status_md} has no **Status:** line — migrate it first "
                             f"(scripts/migrate_spec.py) or fix it by hand")
        self.id = STORY_ID.match(folder.name).group(0)
        self.status_text, self.story_text = self.status_md.read_text(), self.story_md.read_text()

    @property
    def status(self) -> str:
        return get_field(self.status_text, "Status") or ""

    def epic_file(self) -> Path | None:
        epic = get_field(self.story_text, "Epic") or ""
        m = re.search(r"E-\d{2,}", epic)
        if not m:
            return None
        found = sorted((self.repo / "spec" / "epics").glob(f"{m.group(0)}-*/epic.md"))
        return found[0] if found else None

    def set_status(self, value: str, history: str) -> None:
        """Set status in status.md (with a History line), the backlog, and the epic."""
        self.status_text = add_history(set_field(self.status_text, "Status", value), history)
        for path in (self.repo / "spec" / "backlog.md", self.epic_file()):
            if path and path.is_file():
                path.write_text(set_row_status(path.read_text(), self.id, value))

    def save(self) -> None:
        self.status_md.write_text(self.status_text)
        self.story_md.write_text(self.story_text)


def resolve(repo: Path, target: str) -> Path:
    folder = gate_check.resolve_target(target, repo)
    if folder is None:
        raise UsageError(f"target not found: {target}")
    return folder


def epic_id_of(folder: Path) -> str:
    m = re.match(r"E-\d{2,}", folder.name)
    return m.group(0) if m else folder.name


def head(repo: Path) -> str:
    return gate_check.git(repo, "rev-parse", "HEAD").stdout.strip()


# ── Follow-ups ───────────────────────────────────────────────────────────────

FOLLOWUP = re.compile(r"^- (?P<target>\S+) (?P<fid>F\d+) — (?P<rest>.*)$")
LOCATION = re.compile(r"\(`([^`]+:\d+)`\)")


def finding_key(file: str | None, line: int | None, title: str) -> str:
    """Identity of a defect across reviews: file:line when known, else the normalized title."""
    if file and line:
        return f"{file}:{line}"
    return re.sub(r"\W+", " ", title.lower()).strip()


def update_followups(backlog: Path, target: str, round_no: int, findings: list[dict], gate_pass: bool) -> list[str]:
    """Add open low findings (on PASS) and mark fixed ones; dedupe by file:line. Returns change notes."""
    if not backlog.is_file():
        return []
    text = backlog.read_text()
    if "## Follow-ups" not in text:
        text = text.rstrip("\n") + "\n\n## Follow-ups\n"
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "## Follow-ups")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    items = lines[start + 1 : end]
    notes = []

    def key_of(item: str) -> str | None:
        m = FOLLOWUP.match(item)
        if not m:
            return None
        loc = LOCATION.search(item)
        if loc:
            return loc.group(1)
        return finding_key(None, None, re.sub(r" \(`[^`]*`\).*$| — P\d.*$", "", m.group("rest")))

    def is_marked_fixed(item: str) -> bool:
        return " — fixed (" in item or "**fixed**" in item

    for f in findings:
        ref = f"{target} {f['id']}"
        key = finding_key(f.get("file"), f.get("line"), f.get("title", ""))
        match = next((i for i, it in enumerate(items) if it.startswith(f"- {ref} ") or key_of(it) == key), None)
        if f.get("status") == "fixed" and match is not None and not is_marked_fixed(items[match]):
            items[match] += f" — fixed ({target} r{round_no})"
            notes.append(f"follow-up {items[match].split(' — ')[0][2:]} marked fixed")
        elif gate_pass and f.get("status") == "open" and f.get("severity") == "low":
            if match is None:
                loc = f" (`{f['file']}:{f['line']}`)" if f.get("file") and f.get("line") else ""
                items.append(f"- {ref} — {f.get('title', '')}{loc} — P3")
                notes.append(f"follow-up added: {ref}")
            elif not items[match].startswith(f"- {ref} ") and ref not in items[match]:
                items[match] += f" — also raised by {ref}"
                notes.append(f"follow-up merged: {ref} duplicates {items[match].split(' — ')[0][2:]}")
    lines[start + 1 : end] = [it for it in items if it.strip()] + ([""] if end < len(lines) else [])
    backlog.write_text("\n".join(lines).rstrip("\n") + "\n")
    return notes


# ── Commands ─────────────────────────────────────────────────────────────────


def cmd_ready(repo: Path, s: Story, allow_deps: list[str]) -> str:
    if s.status == "Ready":
        return f"{s.id} is already Ready"
    if s.status != "Backlog":
        raise ConditionError(f"{s.id} is {s.status}; only a Backlog story can become Ready")
    problems = []
    acs = re.findall(r"\*\*AC-\d+\*\*", s.story_text)
    if len(acs) < 2:
        problems.append(f"needs at least 2 numbered acceptance criteria (**AC-n**), found {len(acs)}")
    for dep in run_state.read_story(repo, s.id)["depends_on"]:
        status = run_state.read_story(repo, dep)["status"]
        if status not in FINISHED and dep not in allow_deps:
            problems.append(f"dependency {dep} is {status} (pass --allow-dep {dep} only if the user approved it as non-blocking)")
    if problems:
        raise ConditionError("; ".join(problems))
    s.story_text = tick_section(s.story_text, "Definition of Ready")
    s.set_status("Ready", "Definition of Ready passed (spec-linter)"
                 + (f"; non-blocking dependencies: {', '.join(allow_deps)}" if allow_deps else ""))
    return f"{s.id}: Backlog → Ready"


def cmd_start(repo: Path, s: Story, base: str | None) -> str:
    if s.status == "In Progress":
        return f"{s.id} is already In Progress (base {get_field(s.status_text, 'Base commit')})"
    if s.status != "Ready":
        raise ConditionError(f"{s.id} is {s.status}; only a Ready story can start (run spec-linter first)")
    current_base = (get_field(s.status_text, "Base commit") or "").strip("`")
    sha = current_base if current_base.lower() not in UNSET_BASE else (base or head(repo))
    s.status_text = set_field(s.status_text, "Base commit", sha)
    s.set_status("In Progress", f"work started; base commit {sha[:7]}")
    epic = s.epic_file()
    if epic and get_field(epic.read_text(), "Status") in (None, "Backlog"):
        epic.write_text(set_field(epic.read_text(), "Status", "In Progress"))
        backlog = repo / "spec" / "backlog.md"
        if backlog.is_file():
            backlog.write_text(set_row_status(backlog.read_text(), epic_id_of(epic.parent), "In Progress"))
    return f"{s.id}: Ready → In Progress (base {sha[:7]})"


def cmd_review(repo: Path, folder: Path, round_no: int | None) -> str:
    result = gate_check.evaluate(folder, repo, max_rounds=10**6)
    if result["gate"] == "NO_REVIEW":
        raise ConditionError(f"no review found in {folder}/reviews")
    reviews = dict(gate_check.list_reviews(folder / "reviews"))
    n = round_no or max(reviews)
    if n not in reviews:
        raise ConditionError(f"round r{n} not found")
    if n != result["round"]:
        raise ConditionError(f"r{n} is not the latest round (r{result['round']}); record the latest round")
    review = json.loads(reviews[n].read_text())
    o, gate, sha = result["open"], result["gate"], result["reviewed_head"][:7]
    counts = f"{o['high']}H/{o['medium']}M/{o['low']}L open"
    changes = [f"{c['id']} {c['from']}→{c['to']}" + ("" if c["accepted"] else " (ignored)")
               for c in result["severity_changes"] if c["round"] == n]
    summary = (f"independent review r{n} ({review.get('reviewer', '?')}): {gate}, {counts}"
               + (f"; severity changes: {', '.join(changes)}" if changes else ""))
    target = review.get("target") or folder.name
    out = [summary]

    if (folder / "story.md").is_file():
        s = Story(repo, folder)
        line = f"r{n} PASS @ {sha}" if gate == "PASS" else f"r{n} FAIL ({o['high']}H/{o['medium']}M open)" + (
            " — stale" if result["current"] is False else "")
        s.status_text = set_field(s.status_text, "Review", line)
        if s.status == "Done":
            s.status_text = add_history(s.status_text, summary)
        else:
            s.set_status("In Review", summary)
        s.save()
        target = s.id
    elif (folder / "epic.md").is_file():
        epic = folder / "epic.md"
        text = epic.read_text()
        entry = f"- r{n} {gate} @ {sha} ({today()}) — {counts}"
        m = re.search(r"^## Integration Review[ \t]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        if m:
            body = "\n".join(ln for ln in m.group(1).rstrip("\n").splitlines() if not ln.startswith("- not run"))
            text = text[: m.start(1)] + (body + "\n" if body else "") + entry + "\n" + text[m.end(1):]
        else:
            text = text.rstrip("\n") + f"\n\n## Integration Review\n{entry}\n"
        epic_id = epic_id_of(folder)
        members = run_state.epic_story_ids(repo, epic_id)
        all_done = members and all(run_state.read_story(repo, m_)["status"] in FINISHED for m_ in members)
        if gate == "PASS" and all_done:
            text = set_field(text, "Status", "Done")
            backlog = repo / "spec" / "backlog.md"
            if backlog.is_file():
                backlog.write_text(set_row_status(backlog.read_text(), epic_id, "Done"))
            out.append(f"{epic_id}: Done (all stories Done, integration review passed)")
        epic.write_text(text)
        target = epic_id

    out += update_followups(repo / "spec" / "backlog.md", target, n, review.get("findings", []), gate == "PASS")
    return "\n".join(out)


def cmd_done(repo: Path, s: Story, note: str | None) -> str:
    if s.status == "Done":
        return f"{s.id} is already Done"
    problems = []
    if s.status != "In Review":
        problems.append(f"{s.id} is {s.status}; it must be In Review (run the independent-review skill)")
    gate = gate_check.evaluate(s.folder, repo, max_rounds=10**6)
    if gate["gate"] != "PASS":
        problems.append("review gate is not passing: " + ("; ".join(gate.get("reasons", [])) or gate["gate"]))
    ok, reasons = run_checks.verify(s.folder, repo, "full")
    if not ok:
        problems.append("full checks not valid for the current code (run_checks.py --mode full --record "
                        f"{s.id}): " + "; ".join(reasons))
    unchecked = re.findall(r"^- \[ \] \*\*(AC-\d+)\*\*", s.story_text, re.MULTILINE)
    if unchecked:
        problems.append(f"acceptance criteria not ticked: {', '.join(unchecked)}")
    if problems:
        raise ConditionError("\n  ✗ ".join([""] + problems).strip())
    checks = json.loads((s.folder / "evidence" / "checks.json").read_text())
    smoke = (checks.get("smoke") or {}).get("run_id")
    s.story_text = tick_section(s.story_text, "Definition of Done")
    impl = s.folder / "implementation.md"
    if impl.is_file():
        impl.write_text(tick_section(impl.read_text(), "Tasks"))
    s.status_text = set_field(s.status_text, "Blockers", "none")
    s.set_status("Done", f"Definition of Done passed — review r{gate['round']} PASS @ {gate['reviewed_head'][:7]}; "
                         f"full checks PASS @ {checks['head'][:7]}" + (f" (smoke {smoke})" if smoke else "")
                         + (f"; {note}" if note else ""))
    return f"{s.id}: In Review → Done"


def main() -> int:
    """CLI entrypoint. See the module docstring for usage and exit codes."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="project root (default: .)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ready")
    p.add_argument("story")
    p.add_argument("--allow-dep", action="append", default=[])
    p = sub.add_parser("start")
    p.add_argument("story")
    p.add_argument("--base")
    p = sub.add_parser("review")
    p.add_argument("target")
    p.add_argument("--round", type=int)
    p = sub.add_parser("done")
    p.add_argument("story")
    p.add_argument("--note")
    p = sub.add_parser("block")
    p.add_argument("story")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("unblock")
    p.add_argument("story")
    p = sub.add_parser("split")
    p.add_argument("story")
    p.add_argument("--into", nargs="+", required=True)
    p = sub.add_parser("note")
    p.add_argument("story")
    p.add_argument("text")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    try:
        if args.cmd == "review":
            print(cmd_review(repo, resolve(repo, args.target), args.round))
            return 0
        s = Story(repo, resolve(repo, args.story))
        if args.cmd == "ready":
            msg = cmd_ready(repo, s, args.allow_dep)
        elif args.cmd == "start":
            msg = cmd_start(repo, s, args.base)
        elif args.cmd == "done":
            msg = cmd_done(repo, s, args.note)
        elif args.cmd == "block":
            s.status_text = add_history(set_field(s.status_text, "Blockers", args.reason), f"blocked: {args.reason}")
            msg = f"{s.id}: blocked — {args.reason}"
        elif args.cmd == "unblock":
            s.status_text = add_history(set_field(s.status_text, "Blockers", "none"), "blockers cleared")
            msg = f"{s.id}: blockers cleared"
        elif args.cmd == "split":
            if s.status in FINISHED:
                raise ConditionError(f"{s.id} is already {s.status}")
            s.status_text = set_field(s.status_text, "Superseded by", ", ".join(args.into))
            s.set_status("Split", f"split into {', '.join(args.into)} (feature-slicer)")
            msg = f"{s.id}: Split → {', '.join(args.into)}"
        else:
            s.status_text = add_history(s.status_text, args.text)
            msg = f"{s.id}: history updated"
        s.save()
        print(msg)
        return 0
    except ConditionError as exc:
        print(f"NOT CHANGED — {exc}", file=sys.stderr)
        return 1
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
