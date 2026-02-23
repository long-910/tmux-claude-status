#!/usr/bin/env bash
# install.sh - Install claude-tmux-status
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
TMUX_CONF="${HOME}/.tmux.conf"

echo "=== claude-tmux-status installer ==="

# 1. Install the script
mkdir -p "$BIN_DIR"
cp "$SCRIPT_DIR/claude_usage.py" "$BIN_DIR/claude-usage"
chmod +x "$BIN_DIR/claude-usage"
echo "[ok] Installed to $BIN_DIR/claude-usage"

# 2. Verify PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "[warn] $BIN_DIR is not in PATH."
    echo "       Add to your shell rc:  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 3. Configure tmux
TMUX_SNIPPET='# claude-tmux-status: refresh every 30s, show usage on right
set -g status-right-length 120
set -g status-interval 30
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | %H:%M %Y-%m-%d"'

if [ ! -f "$TMUX_CONF" ]; then
    echo "" > "$TMUX_CONF"
fi

if grep -q "claude-tmux-status" "$TMUX_CONF"; then
    echo "[skip] tmux config already contains claude-tmux-status snippet"
else
    echo "" >> "$TMUX_CONF"
    echo "$TMUX_SNIPPET" >> "$TMUX_CONF"
    echo "[ok] Added claude-tmux-status to $TMUX_CONF"
fi

# 4. Reload tmux if running
if tmux info &>/dev/null 2>&1; then
    tmux source-file "$TMUX_CONF" && echo "[ok] Reloaded tmux config"
fi

echo ""
echo "=== Done! ==="
echo "Status bar will show:  🤖 in:26.3K out:63.0K \$0.42"
echo ""
echo "Manual usage:"
echo "  claude-usage short   # compact (for tmux)"
echo "  claude-usage long    # full breakdown"
echo "  claude-usage json    # JSON output"
