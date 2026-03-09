#!/usr/bin/env bash
# install.sh - Manual installer for tmux-claude-status
# For TPM installation, see README.md
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/long-910/tmux-claude-status/main/install.sh | bash
#   bash install.sh  (from a local clone)
set -eu

GITHUB_RAW="https://raw.githubusercontent.com/long-910/tmux-claude-status/main"
BIN_DIR="${HOME}/.local/bin"
BIN="$BIN_DIR/claude-usage"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# tmux-claude-status"

echo "=== tmux-claude-status manual installer ==="

# 1. Install script
mkdir -p "$BIN_DIR"

# Detect local clone vs remote (curl | bash) execution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-}")" 2>/dev/null && pwd || echo "")"
LOCAL_SCRIPT="$SCRIPT_DIR/scripts/claude_usage.py"

if [ -f "$LOCAL_SCRIPT" ]; then
    \cp "$LOCAL_SCRIPT" "$BIN"
else
    echo "[info] Downloading claude_usage.py from GitHub..."
    curl -fsSL "$GITHUB_RAW/scripts/claude_usage.py" -o "$BIN"
fi

chmod +x "$BIN"
echo "[ok] Installed: $BIN"

if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "[warn] $BIN_DIR not in PATH — add to shell rc:"
    echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 2. Configure tmux.conf
if [ ! -f "$TMUX_CONF" ]; then touch "$TMUX_CONF"; fi

if grep -q "$MARKER" "$TMUX_CONF"; then
    echo "[skip] tmux config already has tmux-claude-status"
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
bind B display-popup -E -w 82 -h 90% "\"${BIN}\" dashboard"
EOF
    echo "[ok] Added to $TMUX_CONF"
fi

# 3. Claude Code Stop hook
python3 "$BIN" --install-hook

# 4. Default settings
SETTINGS="${HOME}/.claude/tmux-claude-status.json"
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
echo "  claude-usage dashboard    # full-screen dashboard"
echo "  claude-usage --version    # show version"
echo "  <prefix>+U                # toggle percent/cost in tmux"
echo "  <prefix>+B                # open dashboard popup in tmux (tmux 3.2+)"
