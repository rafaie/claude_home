#!/usr/bin/env bash
# install.sh — sets up the claude-home plugin as a permanent shell alias
# and installs the global CLAUDE.md instructions.
#
# Usage:
#   ./install.sh          # symlink alias + append CLAUDE.md
#   ./install.sh --copy   # same but overwrites ~/.claude/CLAUDE.md

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME_DIR="$HOME/.claude"
CLAUDE_MD_TARGET="$CLAUDE_HOME_DIR/CLAUDE.md"
ALIAS_LINE="alias claude='claude --plugin-dir \"$PLUGIN_DIR\"'"
MARKER="# claude-home plugin"
COPY_MODE=false

for arg in "$@"; do
  [[ "$arg" == "--copy" ]] && COPY_MODE=true
done

# ── Detect shell profile ────────────────────────────────────────────────────
detect_profile() {
  if [[ -n "${ZDOTDIR:-}" && -f "$ZDOTDIR/.zshrc" ]]; then
    echo "$ZDOTDIR/.zshrc"
  elif [[ -f "$HOME/.zshrc" ]]; then
    echo "$HOME/.zshrc"
  elif [[ -f "$HOME/.bash_profile" ]]; then
    echo "$HOME/.bash_profile"
  elif [[ -f "$HOME/.bashrc" ]]; then
    echo "$HOME/.bashrc"
  else
    echo "$HOME/.profile"
  fi
}

PROFILE="$(detect_profile)"

# ── Install shell alias ─────────────────────────────────────────────────────
echo "→ Shell profile: $PROFILE"

if grep -qF "$MARKER" "$PROFILE" 2>/dev/null; then
  echo "  alias already installed, skipping."
else
  {
    echo ""
    echo "$MARKER"
    echo "$ALIAS_LINE"
  } >> "$PROFILE"
  echo "  added alias to $PROFILE"
fi

# ── Install CLAUDE.md ───────────────────────────────────────────────────────
mkdir -p "$CLAUDE_HOME_DIR"

SECTION_START="<!-- claude-home start -->"
SECTION_END="<!-- claude-home end -->"
CONTENT="$SECTION_START
$(cat "$PLUGIN_DIR/CLAUDE.md")
$SECTION_END"

echo "→ ~/.claude/CLAUDE.md"

if [[ "$COPY_MODE" == true ]]; then
  echo "$CONTENT" > "$CLAUDE_MD_TARGET"
  echo "  wrote (overwrite mode)"
elif [[ -f "$CLAUDE_MD_TARGET" ]] && grep -qF "$SECTION_START" "$CLAUDE_MD_TARGET"; then
  echo "  claude-home section already present, skipping."
elif [[ -f "$CLAUDE_MD_TARGET" ]]; then
  { echo ""; echo "$CONTENT"; } >> "$CLAUDE_MD_TARGET"
  echo "  appended to existing CLAUDE.md"
else
  echo "$CONTENT" > "$CLAUDE_MD_TARGET"
  echo "  created new CLAUDE.md"
fi

# ── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "Done! Reload your shell to activate the alias:"
echo "  source $PROFILE"
echo ""
echo "Then launch Claude with the plugin loaded:"
echo "  claude"
echo ""
echo "Or load the plugin without the alias:"
echo "  claude --plugin-dir \"$PLUGIN_DIR\""
