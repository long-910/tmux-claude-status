#!/usr/bin/env bash
# install.sh - Manual installer for claude-tmux-status
# For TPM installation, see README.md
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/scripts/claude_usage.py"
BIN_DIR="${HOME}/.local/bin"
BIN="$BIN_DIR/claude-usage"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# claude-tmux-status"

echo "=== claude-tmux-status manual installer ==="

# 1. Install script
mkdir -p "$BIN_DIR"
\cp "$SCRIPT" "$BIN"
chmod +x "$BIN"
echo "[ok] Installed: $BIN"

if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "[warn] $BIN_DIR not in PATH — add to shell rc:"
    echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 2. Configure tmux.conf
if [ ! -f "$TMUX_CONF" ]; then touch "$TMUX_CONF"; fi

if grep -q "$MARKER" "$TMUX_CONF"; then
    echo "[skip] tmux config already has claude-tmux-status"
else
    if grep -q "tmux-mem-cpu-load" "$TMUX_CONF"; then
        STATUS_RIGHT="#($BIN short) | #[fg=green,bg=black]#(tmux-mem-cpu-load --colors --interval 2)#[default] | %H:%M %Y-%m-%d"
    else
        STATUS_RIGHT="#($BIN short) | %H:%M %Y-%m-%d"
    fi
    cat >> "$TMUX_CONF" << EOF

${MARKER}
set -g status-right-length 200
set -g status-right "${STATUS_RIGHT}"
bind U run-shell "\"${BIN}\" toggle && tmux refresh-client -S"
EOF
    echo "[ok] Added to $TMUX_CONF"
fi

# 3. Claude Code Stop hook
python3 "$BIN" --install-hook

# 4. Default settings
SETTINGS="${HOME}/.claude/claude-tmux-status.json"
if [ ! -f "$SETTINGS" ] && [ -d "${HOME}/.claude" ]; then
    printf '{\n  "realtime": false,\n  "cache_ttl": 300\n}\n' > "$SETTINGS"
    echo "[ok] Created: $SETTINGS"
fi

# 5. Reload tmux
if tmux info >/dev/null 2>&1; then
    tmux source-file "$TMUX_CONF" && echo "[ok] Reloaded tmux"
fi

echo ""
echo "Done! Usage:"
echo "  claude-usage              # status display"
echo "  claude-usage --refresh    # force API update"
echo "  claude-usage toggle       # switch percent/cost"
echo "  claude-usage long         # full breakdown"
echo "  <prefix>+U                # toggle in tmux"
