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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_state import CANONICAL, STATUS_LINE, normalize_status


def rewrite_status(text: str) -> tuple[str, str | None]:
    """Convert a status.md body to the new format.

    Handles ``**Current phase:**``, ``**Status:**``, and plain or bulleted ``Status:`` lines with
    free-form values. The first ``Status`` line wins over ``Current phase``. A non-canonical value is
    normalized, and the original wording is kept on a ``**Legacy status:**`` line.

    Returns:
        ``(new_text, note)`` where note describes a non-trivial mapping, else None.
    """
    matches = list(STATUS_LINE.finditer(text))
    m = next((x for x in matches if x.group(1).lower() == "status"), matches[0] if matches else None)
    if m is None:
        title_end = text.find("\n") + 1 if text.startswith("#") else 0
        text = text[:title_end] + "\n**Status:** Backlog\n" + text[title_end:]
        block_end, note = text.index("**Status:** Backlog") + len("**Status:** Backlog"), "no status line — set to Backlog"
    else:
        raw = m.group(2).strip().strip("*`").strip()
        status = normalize_status(raw)
        block = f"**Status:** {status}"
        note = None
        if raw not in CANONICAL:
            block += f"\n**Legacy status:** {raw}"
            note = f"status '{raw}' → {status}"
        text = text[: m.start()] + block + text[m.end() :]
        block_end = m.start() + len(block)
    extra = ""
    if "**Blockers:**" not in text and not re.search(r"^[ \t]*(?:[-*][ \t]+)?Blockers:", text, re.MULTILINE | re.IGNORECASE):
        extra += "\n**Blockers:** none"
    if "**Base commit:**" not in text:
        extra += "\n**Base commit:** unknown (migrated)"
    if "**Review:**" not in text:
        extra += "\n**Review:** not started"
    return text[:block_end] + extra + text[block_end:], note


def rewrite_links(text: str, names: list[str], generic: bool = True) -> str:
    """Point links at migrated story folders.

    Args:
        text: Markdown to rewrite.
        names: Folder names that were moved to ``spec/stories/``.
        generic: Also rewrite remaining generic ``spec/features/`` mentions. Only safe when no folder stays
            behind in ``spec/features/`` (no conflicts); otherwise links to the skipped folders would break.
    """
    for name in names:
        text = text.replace(f"features/{name}/feature.md", f"stories/{name}/story.md")
        text = text.replace(f"features/{name}", f"stories/{name}")
    return text.replace("spec/features/", "spec/stories/") if generic else text


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
        new = rewrite_links(text, plan, generic=not conflicts)
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
