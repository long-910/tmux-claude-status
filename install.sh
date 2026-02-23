#!/usr/bin/env bash
# install.sh - Install claude-tmux-status
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# claude-tmux-status"

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
if [ ! -f "$TMUX_CONF" ]; then
    touch "$TMUX_CONF"
fi

if grep -q "$MARKER" "$TMUX_CONF"; then
    echo "[skip] tmux config already contains claude-tmux-status snippet"
else
    # Check if status-right is already set with tmux-mem-cpu-load
    if grep -q "tmux-mem-cpu-load" "$TMUX_CONF"; then
        # Integrate: append claude-usage to existing mem-cpu-load display
        TMUX_SNIPPET="${MARKER}
set -g status-right-length 200
set -g status-right \"#[fg=colour39]#(claude-usage short)#[default] | #[fg=green,bg=black]#(tmux-mem-cpu-load --colors --interval 2)#[default] | %H:%M %Y-%m-%d\""
    else
        # Fresh setup
        TMUX_SNIPPET="${MARKER}
set -g status-right-length 200
set -g status-interval 30
set -g status-right \"#[fg=colour39]#(claude-usage short)#[default] | %H:%M %Y-%m-%d\""
    fi

    printf '\n%s\n' "$TMUX_SNIPPET" >> "$TMUX_CONF"
    echo "[ok] Added claude-tmux-status to $TMUX_CONF"
fi

# 4. Reload tmux if running
if tmux info >/dev/null 2>&1; then
    tmux source-file "$TMUX_CONF" && echo "[ok] Reloaded tmux config"
else
    echo "[info] tmux is not running. Start tmux to see the status bar."
fi

echo ""
echo "=== Done! ==="
echo "Status bar will show:  🤖 in:26.3K out:63.0K \$0.42 | <cpu/mem> | 14:35 2026-02-23"
echo ""
echo "Manual usage:"
echo "  claude-usage short   # compact (for tmux)"
echo "  claude-usage long    # full breakdown"
echo "  claude-usage json    # JSON output"
