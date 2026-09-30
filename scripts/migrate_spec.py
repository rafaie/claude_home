#!/usr/bin/env python3
"""Migrate a project's spec/ from the legacy work-item layout to the Epic → Story model.

Legacy:  spec/features/<id>-<slug>/feature.md, status.md with ``**Current phase:**``
New:     spec/stories/<id>-<slug>/story.md,    status.md with ``**Status:**``

Changes made (see references/hierarchy.md for the status mapping):
    - move each spec/features/<dir> to spec/stories/<dir> (``git mv`` when tracked)
    - rename feature.md -> story.md
    - rewrite status.md: Current phase -> Status, add Base commit and Review lines
    - rewrite links in every spec/**/*.md from features/<dir>/feature.md to stories/<dir>/story.md

Usage:
    migrate_spec.py [--repo PATH]          # dry run: print the plan
    migrate_spec.py [--repo PATH] --apply  # perform the migration
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PHASE_TO_STATUS = {
    "planning": "Backlog",
    "planned": "Backlog",
    "test plan written": "In Progress",
    "tests written": "In Progress",
    "implementation": "In Progress",
    "testing": "In Progress",
    "in progress": "In Progress",
    "implementation complete": "In Review",
    "shipped": "Done",
}
PHASE_LINE = re.compile(r"^\*\*Current phase:\*\*\s*(.+?)\s*$", re.MULTILINE)


def map_phase(phase: str) -> tuple[str, str | None]:
    """Map a legacy phase to a status.

    Returns:
        ``(status, note)`` where note explains a lossy or unknown mapping, else None.
    """
    key = phase.strip().lower()
    if key in PHASE_TO_STATUS:
        return PHASE_TO_STATUS[key], None
    if key.startswith("blocked"):
        return "In Progress", f"legacy phase '{phase}' — record the reason under Blockers"
    return "In Progress", f"unknown legacy phase '{phase}' — mapped to In Progress, check manually"


def rewrite_status(text: str) -> tuple[str, str | None]:
    """Convert a legacy status.md body to the new format."""
    m = PHASE_LINE.search(text)
    if not m:
        return text, None
    status, note = map_phase(m.group(1))
    text = PHASE_LINE.sub(f"**Status:** {status}", text, count=1)
    extra = ""
    if "**Base commit:**" not in text:
        extra += "**Base commit:** unknown (migrated)\n"
    if "**Review:**" not in text:
        extra += "**Review:** not started\n"
    if extra:
        blockers = re.search(r"^\*\*Blockers:\*\*.*$", text, re.MULTILINE)
        anchor = blockers or re.search(r"^\*\*Status:\*\*.*$", text, re.MULTILINE)
        assert anchor is not None
        text = text[: anchor.end()] + "\n" + extra.rstrip("\n") + text[anchor.end() :]
    return text, note


def rewrite_links(text: str, names: list[str]) -> str:
    """Point links at migrated story folders."""
    for name in names:
        text = text.replace(f"features/{name}/feature.md", f"stories/{name}/story.md")
        text = text.replace(f"features/{name}", f"stories/{name}")
    return text.replace("spec/features/", "spec/stories/")


def is_tracked(repo: Path, path: Path) -> bool:
    """Return True if git tracks any file under ``path``."""
    out = subprocess.run(["git", "-C", str(repo), "ls-files", str(path)], capture_output=True, text=True, check=False)
    return out.returncode == 0 and bool(out.stdout.strip())


def move(repo: Path, src: Path, dst: Path) -> None:
    """Move a path, using ``git mv`` when the source is tracked."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if is_tracked(repo, src):
        subprocess.run(["git", "-C", str(repo), "mv", str(src), str(dst)], check=True)
    else:
        shutil.move(str(src), str(dst))


def main() -> int:
    """CLI entrypoint. See the module docstring for usage."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="project root (default: .)")
    parser.add_argument("--apply", action="store_true", help="perform the migration (default: dry run)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    legacy = repo / "spec" / "features"
    stories = repo / "spec" / "stories"
    if not legacy.is_dir():
        print("Nothing to migrate: spec/features/ not found.")
        return 0

    dirs = sorted(d for d in legacy.iterdir() if d.is_dir())
    plan, conflicts, notes = [], [], []
    for d in dirs:
        if (stories / d.name).exists():
            conflicts.append(d.name)
        else:
            plan.append(d.name)

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"Spec migration ({mode}) — {repo}")
    for name in plan:
        print(f"  move   spec/features/{name}/ → spec/stories/{name}/ (feature.md → story.md, status.md rewritten)")
    for name in conflicts:
        print(f"  SKIP   spec/features/{name}/ — spec/stories/{name}/ already exists")
    md_files = [p for p in (repo / "spec").rglob("*.md") if legacy not in p.parents]
    print(f"  links  rewrite in up to {len(md_files) + len(plan) * 6} spec/**/*.md files")

    if not args.apply:
        for name in plan:
            status = legacy / name / "status.md"
            if status.is_file():
                _, note = rewrite_status(status.read_text())
                if note:
                    print(f"  note   {name}: {note}")
        print("\nRe-run with --apply to perform these changes.")
        return 0

    for name in plan:
        dst = stories / name
        move(repo, legacy / name, dst)
        if (dst / "feature.md").is_file() and not (dst / "story.md").exists():
            move(repo, dst / "feature.md", dst / "story.md")
        status = dst / "status.md"
        if status.is_file():
            new, note = rewrite_status(status.read_text())
            status.write_text(new)
            if note:
                notes.append(f"{name}: {note}")

    changed = 0
    for p in (repo / "spec").rglob("*.md"):
        text = p.read_text()
        new = rewrite_links(text, plan)
        if new != text:
            p.write_text(new)
            changed += 1

    if legacy.is_dir() and not any(legacy.iterdir()):
        legacy.rmdir()

    print(f"\nMigrated {len(plan)} stories; rewrote links in {changed} files.")
    for n in notes:
        print(f"  note   {n}")
    if conflicts:
        print(f"  {len(conflicts)} folder(s) skipped due to conflicts — resolve manually.")
    print("Review the diff (git diff --stat) before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
