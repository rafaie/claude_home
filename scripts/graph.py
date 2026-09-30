#!/usr/bin/env python3
"""Optional graphify integration for claude_home.

Keeps a knowledge graph of the project (``graphify-out/``) current and turns it into review context.
Everything degrades gracefully: when graphify is off or not installed, commands say so and exit 0
(unless the project sets ``graphify: required``).

Usage:
    graph.py status [--json]                      # config, install state, freshness
    graph.py refresh                              # build or incrementally update the code graph
    graph.py mark-docs                            # record that a docs pass just ran (session mode)
    graph.py impact --base SHA [--head SHA] [--out FILE]   # blast radius of a commit range

Configuration — optional ``## Graph`` section in the project CLAUDE.md:
    - graphify: auto        # auto (use if installed) | required | off
    - graph_path: .         # folder to index; exclude paths with .graphifyignore
    - graph_docs: off       # off (code only) | session (graphify skill in Claude Code) | headless (API key)

Exit codes: 0 ok or skipped · 1 required but unavailable, or a graphify command failed · 2 usage error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = {"graphify": "auto", "graph_path": ".", "graph_docs": "off"}
DOC_SUFFIXES = (".md", ".mdx", ".html", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx")
API_KEY_VARS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY")
# Reverse-dependency relations, matching graphify's own `affected` command.
IMPACT_RELATIONS = {
    "calls", "indirect_call", "references", "imports", "imports_from", "dynamic_import", "re_exports",
    "inherits", "extends", "implements", "uses", "mixes_in", "embeds", "requires",
}
STATE_FILE = ".claude_home.json"
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")


# ── Config and state ─────────────────────────────────────────────────────────


def read_config(repo: Path) -> dict:
    """Read the ``## Graph`` section of the project CLAUDE.md, falling back to defaults."""
    cfg = dict(DEFAULTS)
    claude_md = repo / "CLAUDE.md"
    if not claude_md.is_file():
        return cfg
    section = re.search(r"^## Graph\s*$(.*?)(?=^## |\Z)", claude_md.read_text(), re.MULTILINE | re.DOTALL)
    if section:
        for key, value in re.findall(r"^\s*-\s*(\w+)\s*:\s*([^#\n]*)", section.group(1), re.MULTILINE):
            if key in cfg and value.strip():
                cfg[key] = value.strip()
    return cfg


def git(repo: Path, *args: str) -> str:
    """Run git and return stdout ('' on failure)."""
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return out.stdout.strip() if out.returncode == 0 else ""


def out_dir(repo: Path, cfg: dict) -> Path:
    return (repo / cfg["graph_path"]).resolve() / "graphify-out"


def load_state(repo: Path, cfg: dict) -> dict:
    """Our own bookkeeping next to the graph: which commit it was built at, when docs were last passed."""
    path = out_dir(repo, cfg) / STATE_FILE
    return json.loads(path.read_text()) if path.is_file() else {}


def save_state(repo: Path, cfg: dict, **updates: str) -> None:
    path = out_dir(repo, cfg) / STATE_FILE
    state = load_state(repo, cfg)
    state.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def status(repo: Path) -> dict:
    """Describe whether the graph can be used and whether it is current.

    Returns:
        Dict with ``state`` one of: ``off``, ``unavailable``, ``missing``, ``stale``, ``current``.
    """
    cfg = read_config(repo)
    out = out_dir(repo, cfg)
    state = load_state(repo, cfg)
    head = git(repo, "rev-parse", "HEAD")
    info = {
        "config": cfg,
        "installed": shutil.which("graphify") is not None,
        "skill_installed": (Path.home() / ".claude" / "skills" / "graphify" / "SKILL.md").is_file(),
        "api_key": any(os.environ.get(v) for v in API_KEY_VARS),
        "graph": str(out / "graph.json"),
        "report": str(out / "GRAPH_REPORT.md") if (out / "GRAPH_REPORT.md").is_file() else None,
        "built_commit": state.get("built_commit"),
        "docs_commit": state.get("docs_commit"),
        "head": head,
    }
    if cfg["graphify"] == "off":
        info["state"] = "off"
    elif not info["installed"]:
        info["state"] = "unavailable"
    elif not (out / "graph.json").is_file():
        info["state"] = "missing"
    else:
        dirty = git(repo, "status", "--porcelain", "--", cfg["graph_path"])
        dirty_code = [line for line in dirty.splitlines() if "graphify-out/" not in line and not line.endswith(DOC_SUFFIXES)]
        info["state"] = "current" if info["built_commit"] == head and not dirty_code else "stale"
    info["docs_pass_needed"] = docs_pass_needed(repo, cfg, info)
    return info


def docs_pass_needed(repo: Path, cfg: dict, info: dict) -> bool:
    """True when the docs mode is on and documents changed since the last semantic pass."""
    if cfg["graph_docs"] == "off" or info["state"] in {"off", "unavailable"}:
        return False
    if not info["docs_commit"]:
        return True
    changed = git(repo, "diff", "--name-only", info["docs_commit"], "--", cfg["graph_path"]).splitlines()
    return any(f.endswith(DOC_SUFFIXES) and "graphify-out/" not in f for f in changed)


# ── Commands ─────────────────────────────────────────────────────────────────


def run_graphify(*args: str) -> bool:
    """Run a graphify command, streaming a short tail of its output."""
    proc = subprocess.run(["graphify", *args], capture_output=True, text=True, check=False)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
    for line in tail:
        print(f"  graphify: {line}")
    return proc.returncode == 0


def cmd_refresh(repo: Path) -> int:
    info = status(repo)
    cfg = info["config"]
    if info["state"] == "off":
        print("GRAPH: off (## Graph → graphify: off)")
        return 0
    if info["state"] == "unavailable":
        msg = "GRAPH: unavailable — graphify is not installed (uv tool install graphifyy)"
        print(msg)
        return 1 if cfg["graphify"] == "required" else 0

    path = str((repo / cfg["graph_path"]).resolve())
    if info["state"] == "missing":
        print("GRAPH: building code graph (local AST, no LLM)")
        ok = run_graphify("extract", path, "--code-only") and run_graphify("cluster-only", path, "--no-label")
    elif info["state"] == "stale":
        print("GRAPH: updating code graph (incremental, no LLM)")
        ok = run_graphify("update", path)
    else:
        print("GRAPH: current")
        ok = True
    if not ok:
        print("GRAPH: graphify command failed — continuing without the graph", file=sys.stderr)
        return 1 if cfg["graphify"] == "required" else 0
    save_state(repo, cfg, built_commit=info["head"], built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))

    if docs_pass_needed(repo, cfg, {**info, "state": "current"}):
        if cfg["graph_docs"] == "headless":
            if info["api_key"]:
                print("GRAPH: semantic pass over changed docs (headless, uses API key)")
                if run_graphify("extract", path):
                    save_state(repo, cfg, docs_commit=info["head"])
            else:
                print("GRAPH: docs pass skipped — graph_docs: headless needs an LLM API key in the environment")
        elif cfg["graph_docs"] == "session":
            if info["skill_installed"]:
                print(f"DOCS_PASS: needed — run the graphify skill: /graphify {cfg['graph_path']} --update, "
                      "then `graph.py mark-docs`")
            else:
                print("GRAPH: docs pass skipped — graph_docs: session needs the graphify skill (graphify install)")
    print(f"REPORT: {info['report'] or out_dir(repo, cfg) / 'GRAPH_REPORT.md'}")
    return 0


def cmd_impact(repo: Path, base: str, head: str, out: Path | None, limit: int = 40) -> int:
    """Write the blast radius of base..head: changed symbols, their dependents, and test reach."""
    info = status(repo)
    if info["state"] not in {"current", "stale"}:
        print(f"IMPACT: skipped — graph {info['state']}")
        return 0
    graph = json.loads(Path(info["graph"]).read_text())
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = graph.get("links") or graph.get("edges") or []
    prefix = str((repo / info["config"]["graph_path"]).resolve().relative_to(repo.resolve()))
    prefix = "" if prefix == "." else prefix.rstrip("/") + "/"
    changed_files = {f.removeprefix(prefix)
                     for f in git(repo, "diff", "--name-only", f"{base}..{head}").splitlines()}
    changed = {nid for nid, n in nodes.items() if n.get("source_file") in changed_files}
    if not changed:
        print("IMPACT: no graph nodes in the changed files")
        return 0

    reverse: dict[str, list[dict]] = {}
    for e in edges:
        if e.get("relation") in IMPACT_RELATIONS:
            reverse.setdefault(e["target"], []).append(e)

    # Depth-2 reverse traversal from changed symbols to code outside the diff.
    dependents: dict[str, tuple[str, str, int]] = {}
    frontier = set(changed)
    for depth in (1, 2):
        nxt = set()
        for tgt in frontier:
            for e in reverse.get(tgt, []):
                src = e["source"]
                n = nodes.get(src)
                if n is None or src in changed or src in dependents or n.get("source_file") in changed_files:
                    continue
                dependents[src] = (e["relation"], nodes[tgt]["label"], depth)
                nxt.add(src)
        frontier = nxt

    tested = {e["target"] for e in edges
              if nodes.get(e["source"], {}).get("file_type") == "code"
              and TEST_PATH.search(nodes[e["source"]].get("source_file") or "")}
    changed_symbols = [nodes[c] for c in sorted(changed) if nodes[c].get("_callable") or nodes[c].get("_callable_class")]
    untested = [n for n in changed_symbols if n["id"] not in tested and not TEST_PATH.search(n.get("source_file", ""))]

    def loc(n: dict) -> str:
        return f"{n.get('source_file', '?')}:{n.get('source_location', '')}".rstrip(":")

    lines = [
        f"# Graph impact — {base[:7]}..{head[:7]}",
        "",
        "Navigation aid generated from graphify's code graph. Not evidence: verify every item in source.",
        f"Graph built at {(info['built_commit'] or 'unknown')[:7]}; state: {info['state']}.",
        "",
        f"## Changed symbols ({len(changed_symbols)})",
        *[f"- `{n['label']}` — {loc(n)}" for n in changed_symbols[:limit]],
        "",
        f"## Dependents outside the diff ({len(dependents)})",
    ]
    ranked = sorted(dependents.items(), key=lambda kv: (kv[1][2], nodes[kv[0]].get("source_file", "")))
    lines += [f"- `{nodes[d]['label']}` — {loc(nodes[d])} — {rel} → `{via}`" + (" (indirect)" if depth == 2 else "")
              for d, (rel, via, depth) in ranked[:limit]]
    if len(dependents) > limit:
        lines.append(f"- … {len(dependents) - limit} more")
    lines += ["", f"## Changed symbols with no direct test edge ({len(untested)})",
              *[f"- `{n['label']}` — {loc(n)}" for n in untested[:limit]]]
    text = "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"IMPACT: {out} ({len(changed_symbols)} changed, {len(dependents)} dependents, {len(untested)} untested)")
    else:
        print(text)
    return 0


def main() -> int:
    """CLI entrypoint. See the module docstring for usage."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="project root (default: .)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")
    sub.add_parser("refresh")
    sub.add_parser("mark-docs")
    p_impact = sub.add_parser("impact")
    p_impact.add_argument("--base", required=True)
    p_impact.add_argument("--head", default="HEAD")
    p_impact.add_argument("--out", type=Path)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    if args.cmd == "status":
        info = status(repo)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            c = info["config"]
            print(f"GRAPH: {info['state']} · mode {c['graphify']} · docs {c['graph_docs']} · path {c['graph_path']}"
                  + (f" · built {info['built_commit'][:7]}" if info["built_commit"] else "")
                  + (" · docs pass needed" if info["docs_pass_needed"] else ""))
            if info["report"]:
                print(f"REPORT: {info['report']}")
        return 1 if info["state"] == "unavailable" and info["config"]["graphify"] == "required" else 0
    if args.cmd == "refresh":
        return cmd_refresh(repo)
    if args.cmd == "mark-docs":
        cfg = read_config(repo)
        save_state(repo, cfg, docs_commit=git(repo, "rev-parse", "HEAD"))
        print("GRAPH: docs pass recorded")
        return 0
    if args.cmd == "impact":
        head = git(repo, "rev-parse", args.head) or args.head
        return cmd_impact(repo, args.base, head, args.out)
    return 2


if __name__ == "__main__":
    sys.exit(main())
