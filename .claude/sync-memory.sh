#!/usr/bin/env bash
# Point this machine's Claude Code memory directory at the copy stored in this repo,
# so memories written on any machine travel with a git push/pull.
#
#   bash .claude/sync-memory.sh            # link memory only (recommended)
#   bash .claude/sync-memory.sh --sessions # also sync full session transcripts
#
# Safe to re-run. If a real (non-symlink) memory dir already exists with files in it,
# they are copied into the repo before the directory is replaced by the symlink.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# Claude Code derives a project folder name from the absolute path,
# replacing every non-alphanumeric character with '-'.
SLUG="$(printf '%s' "$REPO" | sed 's/[^a-zA-Z0-9]/-/g')"
PROJDIR="$CLAUDE_HOME/projects/$SLUG"

link_one() {
  local target="$1" link="$2" label="$3"
  mkdir -p "$target" "$(dirname "$link")"
  if [ -L "$link" ]; then
    rm "$link"
  elif [ -d "$link" ]; then
    if [ -n "$(ls -A "$link" 2>/dev/null)" ]; then
      echo "  preserving existing $label into repo..."
      cp -rn "$link/." "$target/" 2>/dev/null || true
    fi
    rm -rf "$link"
  fi
  ln -sfn "$target" "$link"
  echo "  $label: $link -> $target"
}

echo "repo:    $REPO"
echo "profile: $PROJDIR"
link_one "$REPO/.claude/memory" "$PROJDIR/memory" "memory"

if [ "${1:-}" = "--sessions" ]; then
  # Transcripts are large and rewritten constantly; opt-in only.
  link_one "$REPO/.claude/sessions" "$PROJDIR/sessions" "sessions"
  echo "  NOTE: transcripts live as *.jsonl directly in $PROJDIR;"
  echo "        copy the ones you want into .claude/sessions/ by hand."
fi

echo "done. Commit .claude/ and push to share across machines."
