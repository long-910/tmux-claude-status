#!/usr/bin/env bash
# install.sh - Install claude-tmux-status
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
TMUX_CONF="${HOME}/.tmux.conf"
MARKER="# claude-tmux-status"

echo "=== claude-tmux-status installer ==="

# 1. スクリプトをインストール
mkdir -p "$BIN_DIR"
\cp "$SCRIPT_DIR/claude_usage.py" "$BIN_DIR/claude-usage"
chmod +x "$BIN_DIR/claude-usage"
echo "[ok] Installed: $BIN_DIR/claude-usage"

# PATH 確認
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "[warn] $BIN_DIR is not in PATH"
    echo "       Add to shell rc: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 2. tmux.conf 設定
if [ ! -f "$TMUX_CONF" ]; then touch "$TMUX_CONF"; fi

if grep -q "$MARKER" "$TMUX_CONF"; then
    echo "[skip] tmux config already has claude-tmux-status"
else
    if grep -q "tmux-mem-cpu-load" "$TMUX_CONF"; then
        STATUS_RIGHT="#(claude-usage short) | #[fg=green,bg=black]#(tmux-mem-cpu-load --colors --interval 2)#[default] | %H:%M %Y-%m-%d"
    else
        STATUS_RIGHT="#(claude-usage short) | %H:%M %Y-%m-%d"
    fi
    cat >> "$TMUX_CONF" << EOF

${MARKER}
set -g status-right-length 200
set -g status-right "${STATUS_RIGHT}"
# Prefix+U: toggle percent/cost display
bind U run-shell "claude-usage toggle && tmux refresh-client -S"
EOF
    echo "[ok] Added to $TMUX_CONF"
    echo "[ok] Keybinding: <prefix>+U toggles percent/cost"
fi

# 3. Claude Code Stop フックを設定
python3 "$BIN_DIR/claude-usage" --install-hook

# 4. デフォルト設定ファイルを作成（未存在時のみ）
SETTINGS="${HOME}/.claude/claude-tmux-status.json"
if [ ! -f "$SETTINGS" ]; then
    cat > "$SETTINGS" << 'EOF'
{
  "realtime": false,
  "cache_ttl": 300
}
EOF
    echo "[ok] Created settings: $SETTINGS"
    echo "     realtime: false (default - no API polling)"
    echo "     Set realtime: true to enable 5-min updates (costs ~\$0.001/day)"
fi

# 5. tmux リロード
if tmux info >/dev/null 2>&1; then
    tmux source-file "$TMUX_CONF" && echo "[ok] Reloaded tmux"
fi

echo ""
echo "=== Done! ==="
echo ""
echo "Display (default: percent mode):"
echo "  5h:78%(2h47m) 7d:84%!    <- fresh"
echo "  5h:78%(3h02m) 7d:84%! [15m before]  <- stale (Claude idle)"
echo "  [--] run: claude-usage --refresh     <- no cache yet"
echo ""
echo "Commands:"
echo "  claude-usage              short (percent or cost)"
echo "  claude-usage --refresh    force update (1 API call)"
echo "  claude-usage toggle       switch percent <-> cost"
echo "  claude-usage long         full breakdown"
echo "  claude-usage json         JSON output"
echo ""
echo "Tmux: <prefix>+U to toggle display mode"
