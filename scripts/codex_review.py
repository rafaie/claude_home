#!/usr/bin/env python3
"""Run the independent review with OpenAI Codex as a cross-model reviewer.

Codex runs in a **read-only sandbox** (enforced by Codex, not by instructions), with the same reviewer
instructions and the same fixed task prompt the other reviewer modes use. Because it cannot write files,
its final message is constrained to the review JSON schema; this script writes ``r<N>.json`` from that
message and renders ``r<N>.md`` from the JSON.

The test command is run by this script *outside* the sandbox first (tests usually need to write caches),
and its output is handed to Codex as ``r<N>-checks.txt``.

Usage:
    codex_review.py <prompt-file> [--model M] [--profile P] [--timeout SECONDS] [--dry-run]

The prompt file is the independent-review skill's Step 4 prompt. Run from anywhere; ``repo_root`` comes
from the prompt. Prints the reviewer's three-line reply (VERDICT / OPEN / FILES).

Exit codes: 0 review written · 1 codex failed or returned an invalid review · 2 usage error
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
AGENT_FILE = PLUGIN_ROOT / "agents" / "independent-reviewer.md"
SCHEMA_FILE = PLUGIN_ROOT / "references" / "review-schema.json"
REQUIRED = ("target", "scope", "round", "base", "head", "verdict", "summary", "ac_coverage", "checks_run", "findings")


def parse_prompt(text: str) -> dict:
    """Parse the fixed ``key: value`` review prompt (``spec_paths`` is a ``- item`` list)."""
    fields: dict = {"spec_paths": []}
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if in_list and line.lstrip().startswith("- "):
            fields["spec_paths"].append(line.lstrip()[2:].strip())
            continue
        in_list = False
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            key = key.strip()
            if key == "spec_paths":
                in_list = True
            elif key.isidentifier():
                fields[key] = value.strip()
    missing = [k for k in ("repo_root", "head", "round", "output_json", "output_md", "test_command") if not fields.get(k)]
    if missing:
        raise ValueError(f"prompt is missing: {', '.join(missing)}")
    return fields


def agent_body() -> str:
    """Reviewer instructions without YAML frontmatter."""
    text = AGENT_FILE.read_text()
    return text.split("---", 2)[2].strip() if text.startswith("---") else text


def run_checks(fields: dict, checks_file: Path, timeout: int) -> dict:
    """Run the project's quick test command outside the sandbox and save its output."""
    cmd = fields["test_command"]
    try:
        proc = subprocess.run(cmd, shell=True, cwd=fields["repo_root"], capture_output=True, text=True,
                              timeout=timeout, check=False)
        output = (proc.stdout + proc.stderr).splitlines()
        result = "pass" if proc.returncode == 0 else "fail"
        note = f"exit {proc.returncode}"
    except subprocess.TimeoutExpired:
        output, result, note = [], "fail", f"timed out after {timeout}s"
    checks_file.parent.mkdir(parents=True, exist_ok=True)
    checks_file.write_text(f"$ {cmd}\n" + "\n".join(output[-300:]) + "\n")
    return {"cmd": cmd, "result": result,
            "notes": f"run by codex_review.py outside the sandbox ({note}); output: {checks_file.name}"}


def build_prompt(task_prompt: str, checks_file: Path) -> str:
    """Reviewer instructions + Codex output-mode override + the fixed task prompt."""
    override = f"""
## Output mode for this run (overrides steps 8–9 "Write outputs" and "Reply" above)

You are running in a read-only sandbox and cannot write files. Do not try to write `output_json` or
`output_md`. Your final message must be only the review JSON object for `output_json`, matching the
provided output schema, with `"reviewer": "codex"`. Use `null` for `file`, `line`, or `ac` when a finding
has none.

The test command has already been run outside the sandbox; its output is in `{checks_file}`. Read it
instead of running the test command. Failures caused by the read-only sandbox are not findings. The
review rubric's rules, evidence requirements, and verdict rule apply unchanged.
"""
    return f"{agent_body()}\n{override}\n---\n\n{task_prompt.strip()}\n"


def validate(review: dict, fields: dict) -> None:
    """Reject a review that is structurally wrong or pinned to the wrong commit."""
    missing = [k for k in REQUIRED if k not in review]
    if missing:
        raise ValueError(f"review is missing: {', '.join(missing)}")
    if review["head"] != fields["head"]:
        raise ValueError(f"review head {review['head'][:10]} does not match requested head {fields['head'][:10]}")
    if int(review["round"]) != int(fields["round"]):
        raise ValueError(f"review round {review['round']} does not match requested round {fields['round']}")


def render_md(r: dict) -> str:
    """Render the Markdown review report (templates/review.md layout) from review JSON."""
    open_ = [f for f in r["findings"] if f["status"] == "open"]
    count = {s: sum(1 for f in open_ if f["severity"] == s) for s in ("high", "medium", "low")}
    lines = [
        f"# Review r{r['round']} — {r['target']}",
        "",
        f"**Verdict:** {r['verdict']}",
        f"**Scope:** {r['scope']} · **Reviewer:** {r.get('reviewer', 'codex')} · **Date:** {r.get('reviewed_at', '')[:10]}",
        f"**Range:** `{r['base'][:7]}..{r['head'][:7]}`",
        f"**Open:** {count['high']} high · {count['medium']} medium · {count['low']} low",
        "", "## Summary", r["summary"], "",
        "## Acceptance Criteria", "", "| AC | Status | Evidence |", "|---|---|---|",
        *[f"| {a['ac']} | {a['status']} | {a['evidence']} |" for a in r["ac_coverage"]],
        "", "## Findings", "",
    ]
    current = [f for f in r["findings"] if f.get("first_seen_round", r["round"]) == r["round"] or f["status"] == "open"]
    for f in current or []:
        where = f"`{f['file']}:{f['line']}`" if f.get("file") and f.get("line") else (f"`{f['file']}`" if f.get("file") else "n/a")
        lines += [
            f"### {f['id']} — {f['title']} ({f['severity']}, {f['category']}, {f['status']})",
            f"- **Where:** {where} · **AC:** {f.get('ac') or 'none'}",
            f"- **Failure scenario:** {f['failure_scenario']}",
            f"- **Evidence:** {f['evidence']}",
            f"- **Recommendation:** {f['recommendation']}",
            "",
        ]
    if not current:
        lines += ["No findings.", ""]
    prior = [f for f in r["findings"] if f.get("first_seen_round", r["round"]) < r["round"]]
    lines += ["## Previous Findings", ""]
    if prior:
        lines += ["| ID | Severity | Status |", "|---|---|---|", *[f"| {f['id']} | {f['severity']} | {f['status']} |" for f in prior]]
    else:
        lines.append("n/a (round 1)" if r["round"] == 1 else "none")
    lines += ["", "## Checks Run", "", "| Command | Result | Notes |", "|---|---|---|",
              *[f"| `{c['cmd']}` | {c['result']} | {c['notes']} |" for c in r["checks_run"]]]
    return "\n".join(lines) + "\n"


def main() -> int:
    """CLI entrypoint. See the module docstring for usage and exit codes."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt_file", type=Path)
    parser.add_argument("--model", help="Codex model (default: your Codex config)")
    parser.add_argument("--profile", help="Codex config profile")
    parser.add_argument("--timeout", type=int, default=3600, help="seconds for the codex run (default 3600)")
    parser.add_argument("--dry-run", action="store_true", help="print the codex command and exit")
    args = parser.parse_args()

    try:
        task_prompt = args.prompt_file.read_text()
        fields = parse_prompt(task_prompt)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if shutil.which("codex") is None:
        print("error: codex CLI not found on PATH (npm i -g @openai/codex, then `codex login`)", file=sys.stderr)
        return 2

    out_json, out_md = Path(fields["output_json"]), Path(fields["output_md"])
    checks_file = out_json.with_name(f"r{fields['round']}-checks.txt")
    with tempfile.TemporaryDirectory() as tmp:
        last_msg = Path(tmp) / "last-message.json"
        cmd = ["codex", "exec", "--sandbox", "read-only", "--cd", fields["repo_root"], "--ephemeral",
               "--color", "never", "--output-schema", str(SCHEMA_FILE), "--output-last-message", str(last_msg)]
        if args.model:
            cmd += ["--model", args.model]
        if args.profile:
            cmd += ["--profile", args.profile]
        cmd.append("-")  # prompt from stdin

        if args.dry_run:
            print("would run tests: " + fields["test_command"])
            print("would run: " + " ".join(cmd) + " < <reviewer instructions + prompt>")
            return 0

        ours = run_checks(fields, checks_file, timeout=args.timeout)
        try:
            proc = subprocess.run(cmd, input=build_prompt(task_prompt, checks_file), capture_output=True,
                                  text=True, timeout=args.timeout, check=False)
        except subprocess.TimeoutExpired:
            print(f"error: codex timed out after {args.timeout}s", file=sys.stderr)
            return 1
        if proc.returncode != 0 or not last_msg.is_file():
            errors = ([ln for ln in proc.stderr.splitlines() if ln.lstrip().upper().startswith("ERROR")]
                      or proc.stderr.splitlines()[-5:])
            print(f"error: codex exited {proc.returncode}", *errors[-5:], sep="\n  ", file=sys.stderr)
            if any("model is not supported" in ln or "model metadata" in ln.lower() for ln in errors):
                print("hint: pass a supported model with --model (reviewer_model in the project's ## Review)",
                      file=sys.stderr)
            return 1
        try:
            review = json.loads(last_msg.read_text())
            validate(review, fields)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            print(f"error: invalid review from codex: {exc}", file=sys.stderr)
            return 1

    review["reviewer"] = "codex"
    review.setdefault("reviewed_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    review["checks_run"] = [ours] + [c for c in review["checks_run"] if c.get("cmd") != ours["cmd"]]
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(review, indent=2) + "\n")
    out_md.write_text(render_md(review))

    open_ = [f for f in review["findings"] if f["status"] == "open"]
    count = {s: sum(1 for f in open_ if f["severity"] == s) for s in ("high", "medium", "low")}
    print(f"VERDICT: {review['verdict']}")
    print(f"OPEN: {count['high']} high · {count['medium']} medium · {count['low']} low")
    print(f"FILES: {out_json} {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
