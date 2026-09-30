#!/usr/bin/env bash
# headless_review.sh — run the independent reviewer in a separate `claude -p` process.
#
# The reviewer shares nothing with the calling session: no conversation, no context window.
# It gets the same system prompt as the `independent-reviewer` agent and the same fixed task
# prompt the independent-review skill would send to the subagent.
#
# Usage:
#   headless_review.sh <prompt-file> [--test-command "<cmd>"] [--model <model>] [--dry-run]
#
# Run from the target repository root. Prints the reviewer's three-line reply
# (VERDICT / OPEN / FILES) and exits non-zero if the claude process fails.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FILE="$SCRIPT_DIR/../agents/independent-reviewer.md"

PROMPT_FILE=""
TEST_COMMAND="uv run pytest -q"
MODEL=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --test-command) TEST_COMMAND="$2"; shift 2 ;;
    --model)        MODEL="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    -*)             echo "unknown option: $1" >&2; exit 2 ;;
    *)              PROMPT_FILE="$1"; shift ;;
  esac
done

[[ -f "$PROMPT_FILE" ]] || { echo "prompt file not found: $PROMPT_FILE" >&2; exit 2; }
[[ -f "$AGENT_FILE" ]]  || { echo "agent file not found: $AGENT_FILE" >&2; exit 2; }
command -v claude >/dev/null || { echo "claude CLI not found on PATH" >&2; exit 2; }

# System prompt = agent body without its YAML frontmatter.
SYSTEM_PROMPT="$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$AGENT_FILE")"

# Read-only inspection + the project's test command + Write (instructed to touch only the two outputs).
ALLOWED_TOOLS=(
  "Read" "Grep" "Glob" "Write"
  "Bash(git diff *)" "Bash(git log *)" "Bash(git show *)" "Bash(git status *)"
  "Bash(git rev-parse *)" "Bash(git merge-base *)" "Bash(ls *)"
  "Bash(${TEST_COMMAND}*)"
)

CMD=(claude -p "$(cat "$PROMPT_FILE")"
  --append-system-prompt "$SYSTEM_PROMPT"
  --allowedTools "${ALLOWED_TOOLS[@]}"
  --disallowedTools "Edit" "NotebookEdit"
  --output-format text)
[[ -n "$MODEL" ]] && CMD+=(--model "$MODEL")

if [[ "$DRY_RUN" == true ]]; then
  printf 'would run: claude -p <prompt:%s> --allowedTools' "$PROMPT_FILE"
  printf ' "%s"' "${ALLOWED_TOOLS[@]}"
  [[ -n "$MODEL" ]] && printf ' --model %s' "$MODEL"
  printf '\n'
  exit 0
fi

"${CMD[@]}"
