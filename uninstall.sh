#!/usr/bin/env bash
# uninstall.sh - Manual uninstaller for claude-tmux-status
set -eu

BIN="${HOME}/.local/bin/claude-usage"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# claude-tmux-status"
SETTINGS="${HOME}/.claude/claude-tmux-status.json"
CACHE="${HOME}/.claude/tmux-rate-limit-cache.json"

echo "=== claude-tmux-status uninstaller ==="

# 1. Remove Stop hook from ~/.claude/settings.json
if [ -x "$BIN" ]; then
    python3 "$BIN" --uninstall-hook || true
else
    echo "[skip] $BIN not found — skipping hook removal"
fi

# 2. Remove binary
if [ -f "$BIN" ]; then
    rm "$BIN"
    echo "[ok] Removed: $BIN"
else
    echo "[skip] $BIN not found"
fi

# 3. Remove the claude-tmux-status block from tmux.conf
if [ -f "$TMUX_CONF" ] && grep -q "$MARKER" "$TMUX_CONF"; then
    python3 - <<'PYEOF'
import re, os, pathlib
path = pathlib.Path(os.path.expanduser("~/.tmux.conf"))
content = path.read_text()
# Remove optional blank line before marker + marker + up to 4 following lines
content = re.sub(r'\n+# claude-tmux-status\n(?:[^\n]*\n){1,4}', '\n', content)
path.write_text(content)
PYEOF
    echo "[ok] Removed claude-tmux-status block from $TMUX_CONF"
else
    echo "[skip] No claude-tmux-status block found in $TMUX_CONF"
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
    tmux source-file "$TMUX_CONF" 2>/dev/null && echo "[ok] Reloaded tmux" || true
fi

echo ""
echo "Done! claude-tmux-status has been removed."
echo "Note: the cloned git repository was not deleted."
