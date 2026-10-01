"""Tests for the claude_home gate scripts, run against throwaway git repositories.

Run with:  uv run --with pytest pytest -q tests
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import gate_check

SMOKE = """\
import json, pathlib, sys
d = pathlib.Path("artifacts/smoke/run1"); (d / "cases").mkdir(parents=True, exist_ok=True)
(d / "cases" / "a.json").write_text("{}")
for f in ("stdout.txt", "stderr.txt"): (d / f).write_text("")
(d / "timing.json").write_text("{}")
(d / "summary.json").write_text(json.dumps({"passed": True}))
"""


# ── helpers ──────────────────────────────────────────────────────────────────


def sh(repo: Path, *cmd: str) -> str:
    return subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def script(repo: Path, name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=repo, capture_output=True, text=True,
                          check=False)


def commit(repo: Path, msg: str) -> str:
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-qm", msg)
    return sh(repo, "git", "rev-parse", "HEAD")


def commands(repo: Path, **overrides: str) -> None:
    cmds = {"format": "true", "lint": "true", "typecheck": "true", "test_quick": "true", "test_full": "true",
            "smoke": f"{sys.executable} smoke.py"} | overrides
    (repo / "CLAUDE.md").write_text("# P\n\n## Commands\n\n" + "".join(f"- {k}: {v}\n" for k, v in cmds.items()))


def make_story(repo: Path, sid: str, status: str = "Backlog", deps: str = "none", epic: str = "none",
               acs: int = 2, ticked: bool = False) -> Path:
    d = repo / "spec" / "stories" / f"{sid}-x"
    (d / "evidence").mkdir(parents=True, exist_ok=True)
    box = "x" if ticked else " "
    ac_lines = "".join(f"- [{box}] **AC-{i}** — Given a, when b, then c.\n" for i in range(1, acs + 1))
    (d / "story.md").write_text(
        f"# {sid} — Title\n\n**Epic:** {epic} · **Area:** a · **Priority:** P1 · **Depends on:** {deps}\n\n"
        f"## Story\nAs a user, I want x, so that y.\n\n## Acceptance Criteria\n{ac_lines}\n"
        "## Definition of Ready\n- [ ] Ready item\n\n## Definition of Done\n- [ ] Done item\n")
    (d / "status.md").write_text(f"# Status — {sid}\n\n**Status:** {status}\n**Blockers:** none\n"
                                 "**Base commit:** not started\n**Review:** not started\n\n## History\n- created\n")
    (d / "implementation.md").write_text("# Impl\n\n## Tasks\n- [ ] task\n")
    (d / "test-results.md").write_text("# Test Results\n")
    return d


def write_review(folder: Path, n: int, head: str, findings: list[dict], acs: list[tuple[str, str]] | None = None,
                 target: str = "S-core-001") -> None:
    (folder / "reviews").mkdir(parents=True, exist_ok=True)
    review = {"schema": 1, "target": target, "scope": "story", "round": n, "reviewer": "subagent", "base": head,
              "head": head, "reviewed_at": "2026-10-01T00:00:00Z", "verdict": "PASS", "summary": "s",
              "ac_coverage": [{"ac": a, "status": s, "evidence": "e"} for a, s in (acs or [("AC-1", "met")])],
              "checks_run": [], "findings": findings}
    (folder / "reviews" / f"r{n}.json").write_text(json.dumps(review))


def finding(fid: str, severity: str, status: str = "open", note: str | None = None, file: str | None = "src/app.py",
            line: int | None = 3, title: str | None = None) -> dict:
    return {"id": fid, "severity": severity, "status": status, "severity_note": note, "file": file, "line": line,
            "title": title or f"problem {fid}", "category": "correctness", "ac": None, "failure_scenario": "x",
            "evidence": "y", "recommendation": "z", "first_seen_round": 1}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    sh(tmp_path, "git", "init", "-q")
    sh(tmp_path, "git", "config", "user.email", "t@example.com")
    sh(tmp_path, "git", "config", "user.name", "t")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / "smoke.py").write_text(SMOKE)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n")
    commands(tmp_path)
    (tmp_path / "spec").mkdir()
    (tmp_path / "spec" / "backlog.md").write_text(
        "# Backlog\n\n| ID | Title | Area | Priority | Status | Depends on |\n|---|---|---|---|---|---|\n"
        "| S-core-001 | One | core | P1 | Backlog | none |\n| S-core-002 | Two | core | P1 | Backlog | S-core-001 |\n")
    make_story(tmp_path, "S-core-001")
    commit(tmp_path, "base")
    return tmp_path


# ── fix 4: severity changes across rounds (gate_check) ───────────────────────


def gate(repo: Path, folder: Path) -> dict:
    return gate_check.evaluate(folder, repo, max_rounds=10)


def test_unexplained_downgrade_is_ignored(repo: Path) -> None:
    d, h = repo / "spec/stories/S-core-001-x", sh(repo, "git", "rev-parse", "HEAD")
    write_review(d, 1, h, [finding("F1", "medium")])
    write_review(d, 2, h, [finding("F1", "low")])
    result = gate(repo, d)
    assert result["gate"] == "FAIL"
    assert result["open"]["medium"] == 1
    assert result["severity_changes"][0] == {"id": "F1", "round": 2, "from": "medium", "to": "low", "note": None,
                                             "accepted": False}


def test_explained_downgrade_is_accepted(repo: Path) -> None:
    d, h = repo / "spec/stories/S-core-001-x", sh(repo, "git", "rev-parse", "HEAD")
    write_review(d, 1, h, [finding("F1", "medium")])
    write_review(d, 2, h, [finding("F1", "low", note="only reachable with a debug flag (cli.py:40)")])
    assert gate(repo, d)["gate"] == "PASS"


def test_upgrade_needs_no_note_and_downgrade_loophole_is_closed(repo: Path) -> None:
    d, h = repo / "spec/stories/S-core-001-x", sh(repo, "git", "rev-parse", "HEAD")
    write_review(d, 1, h, [finding("F1", "low")])
    write_review(d, 2, h, [finding("F1", "medium")])
    write_review(d, 3, h, [finding("F1", "low")])
    write_review(d, 4, h, [finding("F1", "low")])  # repeating the unexplained low does not launder it
    result = gate(repo, d)
    assert result["gate"] == "FAIL" and result["open"]["medium"] == 1
    # r2 raise accepted; r3 and r4 each report the unexplained low, and both are listed as ignored
    assert [(c["round"], c["accepted"]) for c in result["severity_changes"]] == [(2, True), (3, False), (4, False)]


def test_deferred_medium_counts_as_open(repo: Path) -> None:
    d, h = repo / "spec/stories/S-core-001-x", sh(repo, "git", "rev-parse", "HEAD")
    write_review(d, 1, h, [finding("F1", "medium", status="deferred")])
    result = gate(repo, d)
    assert result["gate"] == "FAIL" and "deferred" in result["reasons"][0]


# ── fix 2: run_checks ────────────────────────────────────────────────────────


def test_checks_pass_and_record(repo: Path) -> None:
    r = script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.loads((repo / "spec/stories/S-core-001-x/evidence/checks.json").read_text())
    assert rec["result"] == "PASS" and rec["mode"] == "full" and rec["smoke"]["ok"]
    assert [s["result"] for s in rec["steps"]] == ["pass", "pass", "pass", "skipped", "pass", "pass"]
    results = (repo / "spec/stories/S-core-001-x/test-results.md").read_text()
    assert "## Full Check Run" in results and "Result: **PASS**" in results


def test_checks_stop_at_first_failure_and_never_record_pass(repo: Path) -> None:
    commands(repo, lint="false")
    r = script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001")
    assert r.returncode == 1
    rec = json.loads((repo / "spec/stories/S-core-001-x/evidence/checks.json").read_text())
    assert rec["result"] == "FAIL"
    assert [s["result"] for s in rec["steps"]] == ["pass", "fail", "not_run", "skipped", "not_run", "not_run"]
    assert "Result: **FAIL**" in (repo / "spec/stories/S-core-001-x/test-results.md").read_text()


def test_smoke_without_artifacts_fails(repo: Path) -> None:
    commands(repo, smoke="true")
    r = script(repo, "run_checks.py", "--mode", "quick")
    assert r.returncode == 1 and "artifacts are incomplete" in r.stdout


def test_skip_value_and_verify_freshness(repo: Path) -> None:
    commands(repo, typecheck="skip")
    commit(repo, "config")
    assert script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001").returncode == 0
    assert script(repo, "run_checks.py", "--verify", "S-core-001").returncode == 0
    (repo / "src" / "app.py").write_text("x = 2\n")  # code changes after the checks ran
    r = script(repo, "run_checks.py", "--verify", "S-core-001")
    assert r.returncode == 1 and "code changed since the checks ran" in r.stdout


def test_checks_on_uncommitted_code_stay_valid_after_commit(repo: Path) -> None:
    (repo / "src" / "app.py").write_text("x = 5\n")  # checks run before the story is committed
    assert script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001").returncode == 0
    commit(repo, "S-core-001: build")
    (repo / "spec" / "stories" / "S-core-001-x" / "status.md").write_text("**Status:** In Review\n")  # spec edit
    (repo / "README.md").write_text("# docs\n")  # Markdown edit
    assert script(repo, "run_checks.py", "--verify", "S-core-001").returncode == 0
    (repo / "src" / "new.py").write_text("y = 1\n")  # any new code invalidates the run
    r = script(repo, "run_checks.py", "--verify", "S-core-001")
    assert r.returncode == 1 and "src/new.py" in r.stdout


def test_quick_run_does_not_satisfy_full(repo: Path) -> None:
    assert script(repo, "run_checks.py", "--mode", "quick", "--record", "S-core-001").returncode == 0
    r = script(repo, "run_checks.py", "--verify", "S-core-001", "--mode", "full")
    assert r.returncode == 1 and "full mode required" in r.stdout


# ── fix 3: story_state transitions ───────────────────────────────────────────


def test_ready_requires_numbered_acs_and_finished_dependencies(repo: Path) -> None:
    make_story(repo, "S-core-002", deps="S-core-001", acs=2)
    make_story(repo, "S-core-003", acs=1)
    r = script(repo, "story_state.py", "ready", "S-core-003")
    assert r.returncode == 1 and "at least 2 numbered" in r.stderr
    r = script(repo, "story_state.py", "ready", "S-core-002")
    assert r.returncode == 1 and "dependency S-core-001 is Backlog" in r.stderr
    assert "**Status:** Backlog" in (repo / "spec/stories/S-core-002-x/status.md").read_text()  # unchanged
    r = script(repo, "story_state.py", "ready", "S-core-002", "--allow-dep", "S-core-001")
    assert r.returncode == 0, r.stderr
    assert "| S-core-002 | Two | core | P1 | Ready |" in (repo / "spec/backlog.md").read_text()
    assert "- [x] Ready item" in (repo / "spec/stories/S-core-002-x/story.md").read_text()


def test_full_lifecycle_and_done_conditions(repo: Path) -> None:
    d = repo / "spec/stories/S-core-001-x"
    assert script(repo, "story_state.py", "ready", "S-core-001").returncode == 0
    base = sh(repo, "git", "rev-parse", "HEAD")
    assert script(repo, "story_state.py", "start", "S-core-001").returncode == 0
    assert f"**Base commit:** {base}" in (d / "status.md").read_text()

    (repo / "src" / "app.py").write_text("x = 3\n")
    (d / "story.md").write_text((d / "story.md").read_text().replace("- [ ] **AC", "- [x] **AC"))
    head = commit(repo, "S-core-001: build")
    write_review(d, 1, head, [finding("F1", "high")])
    assert script(repo, "story_state.py", "review", "S-core-001").returncode == 0
    assert "**Review:** r1 FAIL (1H/0M open)" in (d / "status.md").read_text()

    r = script(repo, "story_state.py", "done", "S-core-001")
    assert r.returncode == 1 and "review gate is not passing" in r.stderr and "no recorded check run" in r.stderr

    write_review(d, 2, head, [finding("F1", "high", status="fixed"), finding("F2", "low", line=9)])
    assert script(repo, "story_state.py", "review", "S-core-001").returncode == 0
    assert "**Status:** In Review" in (d / "status.md").read_text()
    assert "- S-core-001 F2 — problem F2 (`src/app.py:9`) — P3" in (repo / "spec/backlog.md").read_text()

    r = script(repo, "story_state.py", "done", "S-core-001")
    assert r.returncode == 1 and "full checks not valid" in r.stderr  # gate passes now, checks still missing

    assert script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001").returncode == 0
    r = script(repo, "story_state.py", "done", "S-core-001")
    assert r.returncode == 0, r.stderr
    status = (d / "status.md").read_text()
    assert "**Status:** Done" in status and "Definition of Done passed — review r2 PASS" in status
    assert "- [x] Done item" in (d / "story.md").read_text()
    assert "- [x] task" in (d / "implementation.md").read_text()
    assert "| S-core-001 | One | core | P1 | Done |" in (repo / "spec/backlog.md").read_text()


def test_done_refuses_unticked_acs(repo: Path) -> None:
    d = repo / "spec/stories/S-core-001-x"
    (d / "status.md").write_text((d / "status.md").read_text().replace("Backlog", "In Review"))
    head = commit(repo, "x")
    write_review(d, 1, head, [])
    script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-001")
    r = script(repo, "story_state.py", "done", "S-core-001")
    assert r.returncode == 1 and "acceptance criteria not ticked: AC-1, AC-2" in r.stderr


def test_legacy_folder_is_refused(repo: Path) -> None:
    d = repo / "spec" / "features" / "S-old-001-x"
    d.mkdir(parents=True)
    (d / "feature.md").write_text("# S-old-001\n")
    (d / "status.md").write_text("**Current phase:** Planning\n")
    r = script(repo, "story_state.py", "ready", "S-old-001")
    assert r.returncode == 2 and "migrate" in r.stderr


# ── fix 5: follow-up de-duplication ──────────────────────────────────────────


def test_followups_dedupe_by_location_and_mark_fixed(repo: Path) -> None:
    story = repo / "spec/stories/S-core-001-x"
    (story / "status.md").write_text((story / "status.md").read_text().replace("Backlog", "In Progress"))
    head = commit(repo, "x")
    write_review(story, 1, head, [finding("F1", "low", line=81, title="raw control characters")])
    assert script(repo, "story_state.py", "review", "S-core-001").returncode == 0

    run = repo / "spec" / "runs" / "R-2026-10-01-a"
    run.mkdir(parents=True)
    write_review(run, 1, head, [finding("F4", "low", line=81, title="control characters echoed"),
                                finding("F6", "low", line=12, title="docstring gap")], target="R-2026-10-01-a")
    assert script(repo, "story_state.py", "review", "R-2026-10-01-a").returncode == 0
    followups = (repo / "spec/backlog.md").read_text().split("## Follow-ups")[1]
    assert followups.count("src/app.py:81") == 1
    assert "also raised by R-2026-10-01-a F4" in followups
    assert "- R-2026-10-01-a F6 — docstring gap (`src/app.py:12`) — P3" in followups

    write_review(run, 2, head, [finding("F4", "low", status="fixed", line=81), finding("F6", "low", line=12)],
                 target="R-2026-10-01-a")
    assert script(repo, "story_state.py", "review", "R-2026-10-01-a").returncode == 0
    followups = (repo / "spec/backlog.md").read_text().split("## Follow-ups")[1]
    assert "— fixed (R-2026-10-01-a r2)" in followups
    assert followups.count("docstring gap") == 1  # re-recording does not duplicate


# ── epics: status propagation through story_state ─────────────────────────────


def test_epic_progress_and_completion(repo: Path) -> None:
    epic = repo / "spec" / "epics" / "E-01-core"
    epic.mkdir(parents=True)
    (epic / "epic.md").write_text(
        "# E-01 — Core\n\n**Status:** Backlog\n\n## Stories\n\n| ID | Title | Priority | Status | Depends on |\n"
        "|---|---|---|---|---|\n| S-core-009 | Nine | P1 | Ready | none |\n\n## Integration Review\n- not run\n")
    (repo / "spec" / "backlog.md").write_text(
        (repo / "spec" / "backlog.md").read_text()
        + "\n## E-01 — Core\n**Status:** Backlog · **Outcome:** core works\n\n| ID | Title | Area | Priority | Status | Depends on |\n"
        "|---|---|---|---|---|---|\n| S-core-009 | Nine | core | P1 | Ready | none |\n")
    story = make_story(repo, "S-core-009", status="Ready", epic="E-01", ticked=True)
    commit(repo, "epic")

    assert script(repo, "story_state.py", "start", "S-core-009").returncode == 0
    assert "**Status:** In Progress" in (epic / "epic.md").read_text()
    backlog = (repo / "spec" / "backlog.md").read_text()
    assert "**Status:** In Progress · **Outcome:** core works" in backlog
    assert "| S-core-009 | Nine | P1 | In Progress | none |" in (epic / "epic.md").read_text()

    head = commit(repo, "S-core-009: build")
    write_review(story, 1, head, [], target="S-core-009")
    assert script(repo, "story_state.py", "review", "S-core-009").returncode == 0
    assert script(repo, "run_checks.py", "--mode", "full", "--record", "S-core-009").returncode == 0
    assert script(repo, "story_state.py", "done", "S-core-009").returncode == 0
    assert "| S-core-009 | Nine | P1 | Done | none |" in (epic / "epic.md").read_text()

    write_review(epic, 1, head, [], target="E-01")
    r = script(repo, "story_state.py", "review", "E-01")
    assert r.returncode == 0 and "E-01: Done" in r.stdout
    text = (epic / "epic.md").read_text()
    assert "**Status:** Done" in text and "- r1 PASS @" in text and "- not run" not in text
    assert "**Status:** Done · **Outcome:** core works" in (repo / "spec" / "backlog.md").read_text()
