#!/usr/bin/env python3
"""Run a project's quality checks and record the results — the only way check results get written.

Reads the commands from the project ``CLAUDE.md`` (``## Commands``; defaults otherwise), runs them in
order, stops at the first failure, validates smoke artifacts, and writes the outcome. Because the script
records results, "all checks pass" can never be written before the checks actually passed.

Modes:
    quick: format → lint → docstrings (if configured) → test_quick → smoke
    full:  format → lint → typecheck → docstrings (if configured) → test_full → smoke

A command set to ``skip`` (or ``none``/``off``) in ``## Commands`` is recorded as skipped.

Usage:
    run_checks.py [--mode quick|full] [--record <story|run|epic folder or ID>] [--keep-going] [--json]
    run_checks.py --verify <folder or ID> [--mode full]   # is the recorded run passing and still current?

With ``--record``, results go to ``<folder>/evidence/checks.json`` (machine-readable, used by
``story_state.py done`` and ``--verify``) and, for a story, a block appended to ``test-results.md``.
Per-step logs are written to ``artifacts/checks/<timestamp>/``.

Exit codes: 0 all checks passed (or verify OK) · 1 a check failed (or verify failed) · 2 usage/config error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_check

DEFAULT_COMMANDS = {
    "test_quick": "uv run pytest -q",
    "test_full": "uv run pytest -q",
    "lint": "uv run ruff check .",
    "format": "uv run ruff format . --check",
    "typecheck": "uv run mypy src",
    "smoke": "uv run python scripts/smoke.py",
}
SKIP_VALUES = {"skip", "none", "off", "n/a", "-"}
STEPS = {
    "quick": [("format", "format"), ("lint", "lint"), ("docstrings", "docstrings"), ("tests", "test_quick"),
              ("smoke", "smoke")],
    "full": [("format", "format"), ("lint", "lint"), ("types", "typecheck"), ("docstrings", "docstrings"),
             ("tests", "test_full"), ("smoke", "smoke")],
}
SMOKE_DIR = Path("artifacts/smoke")
# Pathspecs that leave only code in a tree snapshot (same notion of "code" as gate_check.is_code).
CODE_EXCLUDES = [
    ":(exclude)spec", ":(exclude)artifacts", ":(exclude)graphify-out", ":(exclude,glob)**/*.md",
    *[f":(exclude,glob)**/{d}/**" for d in sorted(gate_check.GENERATED_DIRS)],
    *[f":(exclude,glob)**/*{suffix}" for suffix in gate_check.GENERATED_SUFFIXES],
]
SMOKE_REQUIRED = ("summary.json", "stdout.txt", "stderr.txt", "timing.json")


def read_commands(repo: Path) -> dict[str, str | None]:
    """Commands from the project ``CLAUDE.md`` ``## Commands`` section, over the defaults.

    Returns:
        Command per key; ``None`` means skipped (explicitly, or ``docstrings`` when not configured).
    """
    cmds: dict[str, str | None] = dict(DEFAULT_COMMANDS)
    cmds["docstrings"] = None
    claude_md = repo / "CLAUDE.md"
    if claude_md.is_file():
        section = re.search(r"^## Commands\s*$(.*?)(?=^## |\Z)", claude_md.read_text(), re.MULTILINE | re.DOTALL)
        if section:
            for key, value in re.findall(r"^\s*-\s*(\w+)\s*:\s*(.+?)\s*$", section.group(1), re.MULTILINE):
                value = value.strip().strip("`").strip()
                cmds[key] = None if value.lower() in SKIP_VALUES else value
    return cmds


def head(repo: Path) -> str:
    return gate_check.git(repo, "rev-parse", "HEAD").stdout.strip()


def code_tree(repo: Path) -> str | None:
    """Git tree hash of the working tree's code (committed or not, specs/Markdown/caches excluded).

    Two states with the same code content have the same hash, so a check run stays valid when the code it
    tested is committed afterwards, and becomes invalid as soon as any code changes.
    """
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        add = subprocess.run(["git", "-C", str(repo), "add", "-A", "--", ".", *CODE_EXCLUDES], env=env,
                             capture_output=True, text=True, check=False)
        if add.returncode != 0:
            return None
        tree = subprocess.run(["git", "-C", str(repo), "write-tree"], env=env, capture_output=True, text=True,
                              check=False)
        return tree.stdout.strip() or None


def smoke_dirs(repo: Path) -> dict[Path, float]:
    root = repo / SMOKE_DIR
    return {d: d.stat().st_mtime for d in root.iterdir() if d.is_dir()} if root.is_dir() else {}


def validate_smoke(repo: Path, before: dict[Path, float], started: float) -> dict:
    """Find the artifact folder this smoke run produced and check the required files."""
    after = smoke_dirs(repo)
    new = [d for d in after if d not in before or after[d] >= started]
    if not new:
        return {"run_id": None, "dir": None, "ok": False, "missing": [f"no new folder under {SMOKE_DIR}/"]}
    d = max(new, key=lambda p: after[p])
    missing = [f for f in SMOKE_REQUIRED if not (d / f).is_file()]
    cases = [p for p in (d / "cases").iterdir() if p.is_file()] if (d / "cases").is_dir() else []
    if not cases:
        missing.append("cases/ (at least one file)")
    if (d / "summary.json").is_file():
        try:
            summary = json.loads((d / "summary.json").read_text())
            if isinstance(summary, dict) and summary.get("passed") is False:
                missing.append("summary.json reports passed: false")
        except json.JSONDecodeError:
            missing.append("summary.json is not valid JSON")
    return {"run_id": d.name, "dir": str(d.relative_to(repo)), "ok": not missing, "missing": missing,
            "cases": len(cases)}


def run(repo: Path, mode: str, keep_going: bool, timeout: int) -> dict:
    """Run the checks for ``mode`` and return the result record."""
    cmds = read_commands(repo)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = repo / "artifacts" / "checks" / stamp
    record = {
        "schema": 1, "mode": mode, "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "head": head(repo), "code_tree": code_tree(repo), "dirty_code": gate_check.code_changes_since(repo, "HEAD"),
        "steps": [], "smoke": None, "log_dir": str(log_dir.relative_to(repo)),
    }
    failed = False
    for name, key in STEPS[mode]:
        cmd = cmds.get(key)
        step = {"name": name, "key": key, "command": cmd, "result": None, "exit": None, "seconds": None, "log": None}
        record["steps"].append(step)
        if cmd is None:
            step["result"] = "skipped"
            continue
        if failed and not keep_going:
            step["result"] = "not_run"
            continue
        before, started = (smoke_dirs(repo), time.time()) if name == "smoke" else ({}, time.time())
        try:
            proc = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout,
                                  check=False)
            code, output = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            code, output = 124, f"timed out after {timeout}s"
        step["exit"], step["seconds"] = code, round(time.time() - started, 2)
        log_dir.mkdir(parents=True, exist_ok=True)
        log = log_dir / f"{name}.log"
        log.write_text(f"$ {cmd}\n{output}")
        step["log"] = str(log.relative_to(repo))
        step["tail"] = output.strip().splitlines()[-15:]
        step["result"] = "pass" if code == 0 else "fail"
        if name == "smoke" and code == 0:
            record["smoke"] = validate_smoke(repo, before, started)
            if not record["smoke"]["ok"]:
                step["result"] = "fail"
                step["tail"] = ["smoke exited 0 but its artifacts are incomplete: " + "; ".join(record["smoke"]["missing"])]
        failed = failed or step["result"] == "fail"
    record["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record["result"] = "FAIL" if failed else "PASS"
    return record


def render(record: dict) -> str:
    """Human-readable result."""
    mark = {"pass": "✓", "fail": "✗", "skipped": "–", "not_run": "·"}
    lines = [f"## Checks — {record['mode']} mode @ {record['head'][:7]}"
             + (f" (+ uncommitted code: {', '.join(record['dirty_code'][:5])})" if record["dirty_code"] else ""), ""]
    for s in record["steps"]:
        t = f" ({s['seconds']}s)" if s["seconds"] is not None else ""
        lines.append(f"{s['name']:<11} {mark[s['result']]} {s['result']}{t}" + (f"  `{s['command']}`" if s["command"] else ""))
    if record["smoke"]:
        sm = record["smoke"]
        lines.append(f"smoke run   {sm['run_id']} — artifacts {'complete' if sm['ok'] else 'INCOMPLETE: ' + '; '.join(sm['missing'])}")
    for s in record["steps"]:
        if s["result"] == "fail":
            lines += ["", f"--- {s['name']} failed (exit {s['exit']}), log {s['log']}:"] + [f"  {x}" for x in s.get("tail") or []]
    lines += ["", f"Overall: {record['result']}"]
    return "\n".join(lines)


def markdown_block(record: dict) -> str:
    """The block appended to a story's test-results.md."""
    title = "Full" if record["mode"] == "full" else "Quick"
    dirty = ", ".join(record["dirty_code"]) or "none"
    rows = "\n".join(
        f"| {s['name']} | {('`' + s['command'] + '`') if s['command'] else 'not configured'} | {s['result']} | "
        f"{(str(s['seconds']) + 's') if s['seconds'] is not None else '—'} |" for s in record["steps"])
    smoke = ""
    if record["smoke"]:
        sm = record["smoke"]
        smoke = (f"\nSmoke: `{sm['dir']}/` — artifacts complete ({sm['cases']} cases)\n" if sm["ok"]
                 else f"\nSmoke: artifacts incomplete — {'; '.join(sm['missing'])}\n")
    return (f"\n## {title} Check Run — {record['started_at']} (run_checks.py)\n"
            f"Commit: `{record['head'][:7]}` · uncommitted code: {dirty} · Result: **{record['result']}**\n\n"
            f"| Step | Command | Result | Time |\n|---|---|---|---|\n{rows}\n{smoke}"
            f"Logs: `{record['log_dir']}/`\n")


def save(record: dict, folder: Path) -> Path:
    """Write evidence/checks.json and, for a story, append to test-results.md."""
    evidence = folder / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    out = evidence / "checks.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    results = folder / "test-results.md"
    if results.is_file():
        results.write_text(results.read_text().rstrip("\n") + "\n" + markdown_block(record))
    return out


def verify(folder: Path, repo: Path, mode: str = "full") -> tuple[bool, list[str]]:
    """Is the recorded check run for ``folder`` passing, in ``mode``, and still valid for the current code?"""
    path = folder / "evidence" / "checks.json"
    if not path.is_file():
        return False, [f"no recorded check run ({path.relative_to(repo) if path.is_relative_to(repo) else path})"]
    rec = json.loads(path.read_text())
    reasons = []
    if rec.get("result") != "PASS":
        failed = [s["name"] for s in rec.get("steps", []) if s.get("result") == "fail"]
        reasons.append(f"recorded check run failed ({', '.join(failed) or 'unknown step'})")
    if mode == "full" and rec.get("mode") != "full":
        reasons.append(f"recorded check run is {rec.get('mode')} mode; full mode required")
    now = code_tree(repo)
    if rec.get("code_tree") and now:
        if rec["code_tree"] != now:
            diff = gate_check.git(repo, "diff", "--name-only", rec["code_tree"], now).stdout.split()
            shown = ", ".join(diff[:5]) + (f" (+{len(diff) - 5} more)" if len(diff) > 5 else "")
            reasons.append("code changed since the checks ran" + (f": {shown}" if shown else ""))
    else:  # older record without a code snapshot: require a clean tree at a commit with no code changes since
        if rec.get("dirty_code"):
            reasons.append("checks ran with uncommitted code changes: " + ", ".join(rec["dirty_code"][:5]))
        current, stale = gate_check.freshness(repo, rec.get("head", ""))
        if not current:
            reasons += [s.replace("since review", "since the checks ran") for s in stale]
    return not reasons, reasons


def main() -> int:
    """CLI entrypoint. See the module docstring for usage and exit codes."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="project root (default: .)")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--record", help="story/run/epic folder or ID to record the results in")
    parser.add_argument("--verify", help="check the recorded run of this folder or ID instead of running checks")
    parser.add_argument("--keep-going", action="store_true", help="run every step even after a failure")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per step (default 1800)")
    parser.add_argument("--json", action="store_true", help="print the result record as JSON")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    if args.verify:
        folder = gate_check.resolve_target(args.verify, repo)
        if folder is None:
            print(f"target not found: {args.verify}", file=sys.stderr)
            return 2
        ok, reasons = verify(folder, repo, args.mode)
        print("CHECKS: current and passing" if ok else "CHECKS: NOT VALID\n" + "\n".join(f"  ✗ {r}" for r in reasons))
        return 0 if ok else 1

    folder = None
    if args.record:
        folder = gate_check.resolve_target(args.record, repo)
        if folder is None:
            print(f"target not found: {args.record}", file=sys.stderr)
            return 2
    record = run(repo, args.mode, args.keep_going, args.timeout)
    print(json.dumps(record, indent=2) if args.json else render(record))
    if folder is not None:
        out = save(record, folder)
        if not args.json:
            print(f"Recorded: {out.relative_to(repo) if out.is_relative_to(repo) else out}")
    return 0 if record["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
