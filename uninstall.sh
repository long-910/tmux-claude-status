#!/usr/bin/env bash
# uninstall.sh - Manual uninstaller for tmux-claude-status
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/scripts/claude_usage.py"
BIN="${HOME}/.local/bin/claude-usage"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# tmux-claude-status"
SETTINGS="${HOME}/.claude/tmux-claude-status.json"
CACHE="${HOME}/.claude/tmux-rate-limit-cache.json"

echo "=== tmux-claude-status uninstaller ==="

# 1. Remove Stop hook from ~/.claude/settings.json
# Use the repo script directly so it always has --uninstall-hook support
if [ -f "$SCRIPT" ]; then
    python3 "$SCRIPT" --uninstall-hook || true
else
    echo "[skip] $SCRIPT not found — skipping hook removal"
fi

# 2. Remove binary
if [ -f "$BIN" ]; then
    rm "$BIN"
    echo "[ok] Removed: $BIN"
else
    echo "[skip] $BIN not found"
fi

# 3. Remove the tmux-claude-status block from tmux.conf
if [ -f "$TMUX_CONF" ] && grep -q "$MARKER" "$TMUX_CONF"; then
    python3 - <<'PYEOF'
import re, os, pathlib
path = pathlib.Path(os.path.expanduser("~/.tmux.conf"))
content = path.read_text()
# Remove optional blank lines before marker + marker + all non-empty lines that follow
content = re.sub(r'\n+# tmux-claude-status\n(?:[^\n]+\n)*', '\n', content)
path.write_text(content)
PYEOF
    echo "[ok] Removed tmux-claude-status block from $TMUX_CONF"
else
    echo "[skip] No tmux-claude-status block found in $TMUX_CONF"
fi

# 4. Remove settings file
if [ -f "$SETTINGS" ]; then
    rm "$SETTINGS"
    echo "[ok] Removed: $SETTINGS"
fi

# 5. Remove cache file
if [ -f "$CACHE" ]; then
    rm "$CACHE"
    echo "[ok] Removed: $CACHE"
fi

# 6. Reload tmux if running
if tmux info >/dev/null 2>&1; then
    if tmux source-file "$TMUX_CONF" 2>/dev/null; then echo "[ok] Reloaded tmux"; fi
fi

echo ""
echo "Done! tmux-claude-status has been removed."
echo "Note: the cloned git repository was not deleted."
