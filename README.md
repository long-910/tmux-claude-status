# claude-tmux-status

[![CI](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml/badge.svg)](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![tmux 3.0+](https://img.shields.io/badge/tmux-3.0%2B-1BB91F?logo=tmux&logoColor=white)](https://github.com/tmux/tmux)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/long-910?label=Sponsor&logo=GitHub&color=EA4AAA)](https://github.com/sponsors/long-910)

Display Claude Code **usage percentage** in your tmux status bar — with zero token consumption by default.

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

---

## How it works

**No API calls by default.**
The script watches `~/.claude/projects/**/*.jsonl` for changes.
An API call is made only when Claude Code has been recently active.

```
Claude is running  →  JSONL updated  →  1 API call  →  cache  →  display
Claude is idle     →  read cache only (no API calls)  →  show age of data
```

## Display example

```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

| Token | Meaning |
|-------|---------|
| `5h:78%` | 5-hour window utilization (from Anthropic API, same as Claude.ai settings) |
| `(2h47m)` | Time until 5h window resets |
| `7d:84%` | Weekly utilization |
| `!` | `allowed_warning` — over 75% threshold |
| `X` | `denied` — limit reached |
| `[15m ago]` | Cache age — shown only when Claude has been idle |

**No cache yet:**
```
[--] run: claude-usage --refresh
```

---

## Installation

### Via TPM (Tmux Plugin Manager) — recommended

Add to `~/.tmux.conf`:

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

Then press `<prefix> + I` to install.

#### TPM options

```tmux
# All options are optional — shown with their defaults:
set -g @claude-tmux-toggle-key   "U"      # <prefix>+U toggles percent/cost
set -g @claude-tmux-install-hook "true"   # auto-install Claude Code Stop hook
set -g @claude-tmux-auto-status  "true"   # auto-configure status-right
set -g @claude-tmux-realtime     "false"  # enable 5-min API polling
set -g @claude-tmux-cache-ttl   "300"    # cache TTL in seconds
```

### Manual install

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

---

## Uninstallation

### Via TPM

Remove the plugin line from `~/.tmux.conf`:

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

Then press `<prefix> + alt + u` to uninstall via TPM.

### Manual uninstall

```bash
cd claude-tmux-status
bash uninstall.sh
```

This removes:
- `~/.local/bin/claude-usage`
- The `claude-tmux-status` block from `~/.tmux.conf`
- The Stop hook from `~/.claude/settings.json`
- `~/.claude/claude-tmux-status.json` (settings)
- `~/.claude/tmux-rate-limit-cache.json` (cache)

---

## Requirements

- Python 3.10+
- tmux 3.0+
- Claude Code with `~/.claude/.credentials.json`

---

## Command reference

| Command | Description | API call? |
|---------|-------------|-----------|
| `claude-usage` | Display (current mode) | Only if Claude was active |
| `claude-usage --refresh` | Force API update | Yes (1 call) |
| `claude-usage toggle` | Switch percent ↔ cost | No |
| `claude-usage cost` | Show cost (one-time) | No |
| `claude-usage long` | Full breakdown | Only if Claude was active |
| `claude-usage json` | JSON output | Only if Claude was active |
| `claude-usage --install-hook` | Add Stop hook to Claude Code | No |
| `claude-usage --uninstall-hook` | Remove Stop hook from Claude Code | No |

### Cost mode

Press `<prefix> + U` (or run `claude-usage toggle`) to switch to cost display:

```
5h:$14.21 day:$14.21 7d:$53.17
```

### `long` mode output

```
-- Rate Limit [default(no API)] ------------------------------
  5h:  78% [XXXXXX..] reset:2h47m  (allowed)
  7d:  84% [XXXXXXX.] reset:4.3d   (allowed_warning)
  last updated: just now
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

---

## Update behavior

By default, the API is called only when Claude is actively running. When idle, stale cached data is shown with a `[Xm ago]` indicator — no tokens consumed.

### Realtime mode (opt-in)

Edit `~/.claude/claude-tmux-status.json`:

```json
{
  "realtime": true,
  "cache_ttl": 300
}
```

**Cost estimate for realtime mode** (claude-haiku-4-5, ~9 tokens/call):

| Period | API calls | Cost |
|--------|-----------|------|
| 1 day | 288 | ~$0.001 |
| 1 week | 2,016 | ~$0.009 |
| 1 month | 8,640 | ~$0.040 |

---

## License

MIT

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture details, data sources, and development guide.
