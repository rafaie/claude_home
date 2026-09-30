#!/usr/bin/env python3
"""Review gate check for claude_home stories, epics, and ranges.

Reads the latest ``reviews/r<N>.json`` in a target folder, applies user waivers from
``reviews/waivers.json``, and checks that the review still matches the code. The verdict is
recomputed from the findings; the reviewer's own ``verdict`` field is not trusted.

Usage:
    gate_check.py S-auth-005                 # resolve spec/stories|features|epics/<id>-*/
    gate_check.py spec/stories/S-auth-005-x  # or pass the folder
    gate_check.py S-auth-005 --json          # machine-readable result
    gate_check.py S-auth-005 --next          # next round number and input paths, as JSON
    gate_check.py S-auth-005 --skip-freshness  # historical check (e.g. release-prep on Done stories)

Exit codes:
    0  gate passes
    1  gate fails (open blocking findings, unmet ACs, or stale review)
    2  no review found, invalid review file, or target not found
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BLOCKING_SEVERITIES = {"high", "medium"}
BLOCKING_AC_STATUSES = {"not_met", "partial"}
# Paths that may change after a review without invalidating it (specs, evidence, graph, Markdown docs).
NON_CODE_PREFIXES = ("spec/", "artifacts/", "graphify-out/")
NON_CODE_SUFFIXES = (".md",)
# Untracked tool/test caches that running checks creates; never treated as code changes.
GENERATED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".venv",
                  "node_modules", "htmlcov", ".hypothesis", ".cache"}
GENERATED_SUFFIXES = (".pyc", ".pyo", ".coverage")
REVIEW_FILE = re.compile(r"^r(\d+)\.json$")


def resolve_target(target: str, repo: Path) -> Path | None:
    """Resolve a story/epic ID or folder path to its folder.

    Args:
        target: A folder path, or an ID such as ``S-auth-005`` or ``E-03``.
        repo: Repository root used to resolve IDs.

    Returns:
        The target folder, or None if nothing matches.
    """
    path = Path(target)
    if path.is_dir():
        return path.resolve()
    for parent in ("spec/stories", "spec/features", "spec/epics"):
        matches = sorted((repo / parent).glob(f"{target}-*"))
        matches += [repo / parent / target] if (repo / parent / target).is_dir() else []
        dirs = [m for m in matches if m.is_dir()]
        if dirs:
            return dirs[0].resolve()
    return None


def list_reviews(reviews_dir: Path) -> list[tuple[int, Path]]:
    """Return ``(round, path)`` pairs for every ``r<N>.json`` in ascending round order."""
    if not reviews_dir.is_dir():
        return []
    found = []
    for p in reviews_dir.iterdir():
        m = REVIEW_FILE.match(p.name)
        if m:
            found.append((int(m.group(1)), p))
    return sorted(found)


def load_waivers(reviews_dir: Path) -> set[str]:
    """Return the IDs (findings or ACs) waived by the user."""
    path = reviews_dir / "waivers.json"
    if not path.is_file():
        return set()
    data = json.loads(path.read_text())
    return {str(w["finding"]) for w in data if w.get("approved_by") == "user" and "finding" in w}


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo`` and capture its output."""
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def is_generated(path: str) -> bool:
    """True for untracked caches created by running tests or linters (e.g. ``__pycache__/``)."""
    return path.endswith(GENERATED_SUFFIXES) or path == ".coverage" or bool(GENERATED_DIRS & set(path.split("/")[:-1]))


def freshness(repo: Path, head: str) -> tuple[bool, list[str]]:
    """Check that no code changed since the reviewed commit.

    Args:
        repo: Repository root.
        head: The commit SHA the review was pinned to.

    Returns:
        ``(is_current, reasons)`` where reasons lists what made the review stale.
    """
    if git(repo, "cat-file", "-e", f"{head}^{{commit}}").returncode != 0:
        return False, [f"reviewed commit {head[:10]} not found in this repository"]
    if git(repo, "merge-base", "--is-ancestor", head, "HEAD").returncode != 0:
        return False, [f"reviewed commit {head[:10]} is not an ancestor of HEAD (history rewritten?)"]
    changed = set(git(repo, "diff", "--name-only", head).stdout.split())
    changed |= {f for f in git(repo, "ls-files", "--others", "--exclude-standard").stdout.split() if not is_generated(f)}
    code = sorted(f for f in changed if not f.startswith(NON_CODE_PREFIXES) and not f.endswith(NON_CODE_SUFFIXES))
    if code:
        shown = ", ".join(code[:5]) + (f" (+{len(code) - 5} more)" if len(code) > 5 else "")
        return False, [f"code changed since review: {shown}"]
    return True, []


def evaluate(target_dir: Path, repo: Path, max_rounds: int, check_freshness: bool = True) -> dict:
    """Evaluate the review gate for a target folder.

    Args:
        target_dir: Story, epic, or range folder containing ``reviews/``.
        repo: Repository root.
        max_rounds: Round limit after which a failing gate escalates to the user.
        check_freshness: Whether code changes since the reviewed commit fail the gate.

    Returns:
        A result dict; ``gate`` is ``PASS``, ``FAIL``, or ``NO_REVIEW``.
    """
    reviews_dir = target_dir / "reviews"
    reviews = list_reviews(reviews_dir)
    if not reviews:
        return {"gate": "NO_REVIEW", "target_dir": str(target_dir), "reasons": ["no reviews/r<N>.json found"]}

    round_no, path = reviews[-1]
    review = json.loads(path.read_text())
    for key in ("head", "findings", "ac_coverage"):
        if key not in review:
            raise ValueError(f"{path}: missing required field '{key}'")

    waived = load_waivers(reviews_dir)
    findings = review["findings"]
    open_findings = [f for f in findings if f.get("status") == "open"]
    blocking = [f for f in open_findings if f.get("severity") in BLOCKING_SEVERITIES and f.get("id") not in waived]
    waived_blocking = [f for f in open_findings if f.get("severity") in BLOCKING_SEVERITIES and f.get("id") in waived]
    waived_acs = [a["ac"] for a in review["ac_coverage"] if a.get("status") in BLOCKING_AC_STATUSES and a.get("ac") in waived]
    unmet_acs = [
        a for a in review["ac_coverage"] if a.get("status") in BLOCKING_AC_STATUSES and a.get("ac") not in waived
    ]
    current, stale_reasons = freshness(repo, review["head"]) if check_freshness else (None, [])

    reasons = [f"{f['id']} ({f['severity']}): {f.get('title', '')}" for f in blocking]
    reasons += [f"{a['ac']} is {a['status']}" for a in unmet_acs]
    reasons += stale_reasons
    gate = "PASS" if not reasons else "FAIL"

    def count(sev: str) -> int:
        return sum(1 for f in open_findings if f.get("severity") == sev and f.get("id") not in waived)

    return {
        "gate": gate,
        "target": review.get("target", target_dir.name),
        "target_dir": str(target_dir),
        "round": round_no,
        "review_file": str(path),
        "reviewed_head": review["head"],
        "reviewer_verdict": review.get("verdict"),
        "open": {"high": count("high"), "medium": count("medium"), "low": count("low")},
        "waived": [f["id"] for f in waived_blocking] + waived_acs,
        "unmet_acs": [a["ac"] for a in unmet_acs],
        "ac_total": len(review["ac_coverage"]),
        "current": current,
        "reasons": reasons,
        "escalate": gate == "FAIL" and round_no >= max_rounds,
    }


def next_round(target_dir: Path) -> dict:
    """Describe the inputs for the next review round of a target folder."""
    reviews_dir = target_dir / "reviews"
    reviews = list_reviews(reviews_dir)
    n = reviews[-1][0] + 1 if reviews else 1
    story_file = next((target_dir / f for f in ("story.md", "feature.md", "epic.md") if (target_dir / f).is_file()), None)
    return {
        "target_dir": str(target_dir),
        "next_round": n,
        "previous_review": str(reviews[-1][1]) if reviews else "none",
        "waivers": str(reviews_dir / "waivers.json") if (reviews_dir / "waivers.json").is_file() else "none",
        "output_json": str(reviews_dir / f"r{n}.json"),
        "output_md": str(reviews_dir / f"r{n}.md"),
        "spec_file": str(story_file) if story_file else "none",
    }


def render(result: dict) -> str:
    """Format a gate result for humans."""
    if result["gate"] == "NO_REVIEW":
        return f"Review gate — {result['target_dir']}\nGATE: NO_REVIEW — run the independent-review skill first"
    o = result["open"]
    lines = [
        f"Review gate — {result['target']} (r{result['round']}, reviewed {result['reviewed_head'][:10]})",
        f"Open findings: {o['high']} high · {o['medium']} medium · {o['low']} low"
        + (f"   (waived by user: {', '.join(result['waived'])})" if result["waived"] else ""),
        f"ACs: {result['ac_total'] - len(result['unmet_acs'])}/{result['ac_total']} met, unverifiable, or waived",
        {True: "Freshness: current", False: "Freshness: STALE", None: "Freshness: not checked"}[result["current"]],
    ]
    lines += [f"  ✗ {r}" for r in result["reasons"]]
    lines.append(f"GATE: {result['gate']}")
    if result["escalate"]:
        lines.append("ESCALATE: maximum review rounds reached — ask the user how to proceed")
    return "\n".join(lines)


def main() -> int:
    """CLI entrypoint. See the module docstring for usage and exit codes."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="story/epic ID or folder path")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    parser.add_argument("--next", action="store_true", help="print next-round inputs as JSON and exit")
    parser.add_argument("--max-rounds", type=int, default=3, help="rounds before escalation (default: 3)")
    parser.add_argument("--skip-freshness", action="store_true", help="do not fail on code changed since the review")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    target_dir = resolve_target(args.target, repo)
    if target_dir is None:
        print(f"target not found: {args.target}", file=sys.stderr)
        return 2
    if args.next:
        print(json.dumps(next_round(target_dir), indent=2))
        return 0
    try:
        result = evaluate(target_dir, repo, args.max_rounds, check_freshness=not args.skip_freshness)
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"invalid review data: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else render(result))
    return {"PASS": 0, "FAIL": 1}.get(result["gate"], 2)


if __name__ == "__main__":
    sys.exit(main())
