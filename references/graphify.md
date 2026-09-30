# Knowledge Graph (optional) — graphify

claude_home can use [graphify](https://github.com/Graphify-Labs/graphify) to keep a knowledge graph of
the project in `graphify-out/`. The implementer uses it to see what a change touches; the reviewer uses
it to find callers and code paths outside the diff. Everything works without it.

All graph operations go through `${CLAUDE_PLUGIN_ROOT}/scripts/graph.py` (below: `GR`), which reads the
project configuration, degrades gracefully, and records which commit the graph reflects.

## Configuration

Optional `## Graph` section in the project `CLAUDE.md`:

```markdown
## Graph
- graphify: auto        # auto (use if installed) | required (fail if missing) | off
- graph_path: .         # folder to index; exclude paths with .graphifyignore (gitignore syntax)
- graph_docs: off       # off | session | headless
```

| `graph_docs` | What is in the graph | Cost |
|---|---|---|
| `off` (default) | Code only: local tree-sitter AST, deterministic, no LLM | Free, seconds |
| `session` | Code + docs/specs/reviews, docs extracted by the graphify skill inside Claude Code | Session tokens on each docs pass |
| `headless` | Code + docs, docs extracted by `graphify extract` with an API key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, …) | API tokens on each docs pass |

Only changed documents are re-extracted (graphify caches by content hash).

## Setup (once per machine / project)

```bash
uv tool install graphifyy     # CLI; the package name has two y's
graphify install              # only for graph_docs: session — installs the /graphify skill
```

Add `graphify-out/` to the project `.gitignore` — the graph is machine-local and rebuilt on demand.

Optional, and only with the user's approval because it edits the project `CLAUDE.md` and hooks:
`graphify claude install` adds a PreToolUse hook that nudges every Claude Code session toward
`graphify query` before raw file searches.

## Commands

| Command | When | What it does |
|---|---|---|
| `GR status` | session-start, before a run | `off` · `unavailable` · `missing` · `stale` · `current`, plus whether a docs pass is due |
| `GR refresh` | run start, after each story is Done, run close, before a review | Builds the code graph if missing (`extract --code-only` + `cluster-only`), otherwise `graphify update` (incremental, no LLM). Runs the headless docs pass if configured. Prints `DOCS_PASS: needed` when `graph_docs: session` and docs changed |
| `GR mark-docs` | after running the graphify skill for a docs pass | Records the commit the docs pass covered |
| `GR impact --base B --head H --out F` | before each independent review | Writes changed symbols, their dependents outside the diff (depth 2), and changed symbols with no direct test edge |

When `refresh` prints `DOCS_PASS: needed`, run the graphify skill in the **main session** —
`/graphify <graph_path> --update` — then `GR mark-docs`. Subagents never run a docs pass.

Read-only graph queries any agent may run (all read `graphify-out/graph.json`):

```bash
graphify query "<question>" --budget 1500   # BFS over the graph for a question
graphify affected "<symbol>"                # what depends on a symbol (reverse traversal)
graphify explain "<symbol>"                 # a node, its source line, and its connections
graphify path "<A>" "<B>"                   # shortest connection between two nodes
```

## Rules

1. **The graph is a map, never evidence.** Every claim — a finding, a "no callers" conclusion, an AC
   check — must be verified in source and cite `file:line`. Edges marked `INFERRED` are guesses.
2. **A stale graph is still a useful map, never a gate input.** No gate passes or fails because of the
   graph.
3. **Graph problems never block work** unless the project sets `graphify: required`. If a graphify
   command fails, continue without the graph and mention it once.
4. `graphify-out/` changes never make a review stale (`gate_check.py` ignores that folder).
