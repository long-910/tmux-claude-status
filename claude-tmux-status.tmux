#!/usr/bin/env bash
# claude-tmux-status.tmux
# TPM (Tmux Plugin Manager) entry point
#
# Add to ~/.tmux.conf:
#   set -g @plugin 'long-910/claude-tmux-status'
#
# Optional settings (set before the @plugin line):
#   set -g @claude-tmux-toggle-key   "U"      # keybinding to toggle percent/cost (default: U)
#   set -g @claude-tmux-install-hook "true"   # auto-install Claude Code Stop hook (default: true)
#   set -g @claude-tmux-auto-status  "true"   # auto-configure status-right (default: true)
#   set -g @claude-tmux-realtime     "false"  # enable 5-min API polling (default: false)
#   set -g @claude-tmux-cache-ttl   "300"    # cache TTL in seconds (default: 300)

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$CURRENT_DIR/scripts"
SCRIPT="$SCRIPTS_DIR/claude_usage.py"
BIN_DIR="$HOME/.local/bin"
BIN="$BIN_DIR/claude-usage"

# ── Helper: read plugin option with default ───────────────────────────────────
get_opt() {
    local option="$1" default="$2"
    local value
    value=$(tmux show-option -gqv "@claude-tmux-${option}" 2>/dev/null)
    printf '%s' "${value:-$default}"
}

# ── 1. Install Python script ──────────────────────────────────────────────────
install_script() {
    mkdir -p "$BIN_DIR"
    cp "$SCRIPT" "$BIN"
    chmod +x "$BIN"
}

# ── 2. Create default settings file ───────────────────────────────────────────
configure_settings() {
    local settings_file="$HOME/.claude/claude-tmux-status.json"
    if [ ! -f "$settings_file" ] && [ -d "$HOME/.claude" ]; then
        local realtime cache_ttl
        realtime=$(get_opt "realtime" "false")
        cache_ttl=$(get_opt "cache-ttl" "300")
        printf '{\n  "realtime": %s,\n  "cache_ttl": %s\n}\n' \
            "$realtime" "$cache_ttl" > "$settings_file"
    fi
}

# ── 3. Configure status-right ─────────────────────────────────────────────────
configure_status() {
    local auto_status
    auto_status=$(get_opt "auto-status" "true")
    [ "$auto_status" = "true" ] || return 0

    local current_right
    current_right=$(tmux show-option -gv status-right 2>/dev/null || true)

    # Skip if already configured
    echo "$current_right" | grep -q "claude-usage" && return 0

    tmux set-option -g status-right-length 200

    if echo "$current_right" | grep -q "tmux-mem-cpu-load"; then
        tmux set-option -g status-right "#($BIN short) | $current_right"
    elif [ -z "$current_right" ] || [ "$current_right" = '""' ]; then
        tmux set-option -g status-right "#($BIN short) | %H:%M %Y-%m-%d"
    else
        tmux set-option -g status-right "#($BIN short) | $current_right"
    fi
}

# ── 4. Set up toggle keybinding ───────────────────────────────────────────────
configure_keybinding() {
    local key
    key=$(get_opt "toggle-key" "U")
    [ "$key" = "none" ] && return 0
    tmux bind-key "$key" run-shell "\"$BIN\" toggle && tmux refresh-client -S"
}

# ── 5. Install Claude Code Stop hook ─────────────────────────────────────────
configure_hook() {
    local install_hook
    install_hook=$(get_opt "install-hook" "true")
    [ "$install_hook" = "true" ] || return 0
    python3 "$BIN" --install-hook 2>/dev/null || true
}

# ── Main ──────────────────────────────────────────────────────────────────────
install_script
configure_settings
configure_keybinding
configure_status
configure_hook
