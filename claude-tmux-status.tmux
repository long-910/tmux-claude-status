#!/usr/bin/env bash
# claude-tmux-status.tmux — compatibility shim for v0.8.0 rename
#
# This file exists for backward compatibility with TPM users who still have:
#   set -g @plugin 'long-910/claude-tmux-status'
#
# Please update to the new name:
#   set -g @plugin 'long-910/tmux-claude-status'

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$CURRENT_DIR/tmux-claude-status.tmux" "$@"
