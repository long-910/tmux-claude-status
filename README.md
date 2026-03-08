# claude-tmux-status

[![CI](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml/badge.svg)](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![tmux 3.0+](https://img.shields.io/badge/tmux-3.0%2B-1BB91F?logo=tmux&logoColor=white)](https://github.com/tmux/tmux)
[![Sponsor](https://img.shields.io/badge/Sponsor-GitHub-pink?logo=github)](https://github.com/sponsors/long-910)


Display Claude Code **usage** in your tmux status bar — with zero token consumption by default.
Supports **Claude.ai subscription** (rate-limit %) and **AWS Bedrock / API key** (cost from local JSONL).

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

**Claude.ai Pro / Max / Team / Enterprise** (rate-limit % from Anthropic API):
```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

**5h-only plan** (no weekly limit):
```
5h:78%(2h47m)  |  [CPU/MEM]  |  11:23 2026-02-23
```

**AWS Bedrock / API key** (cost from local JSONL, no API call):
```
[cost] 5h:$14.21 day:$14.21 7d:$53.17  |  [CPU/MEM]  |  11:23 2026-02-23
```

| Token | Meaning |
|-------|---------|
| `5h:78%` | 5-hour window utilization (from Anthropic API, same as Claude.ai settings) |
| `(2h47m)` | Time until 5h window resets |
| `7d:84%` | Weekly utilization (hidden when plan has no weekly limit) |
| `!` | `allowed_warning` — over 75% threshold |
| `X` | `denied` — limit reached |
| `[15m ago]` | Cache age — shown only when Claude has been idle |
| `[cost]` | Cost mode — active for Bedrock/API key or when toggled manually |

**No cache yet:**
```
[--] run: claude-usage --refresh
```

> **Note:** Rate-limit % display has been tested with **Claude.ai Pro plan only**.
> If the display is incorrect for your plan (Max, Team, Enterprise, Bedrock, etc.),
> please [file an issue](https://github.com/long-910/claude-tmux-status/issues).

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
set -g @claude-tmux-toggle-key    "U"      # <prefix>+U toggles percent/cost
set -g @claude-tmux-dashboard-key "B"      # <prefix>+B opens dashboard popup (tmux 3.2+)
set -g @claude-tmux-install-hook  "true"   # auto-install Claude Code Stop hook
set -g @claude-tmux-auto-status   "true"   # auto-configure status-right
set -g @claude-tmux-realtime      "false"  # enable 5-min API polling
set -g @claude-tmux-cache-ttl    "300"    # cache TTL in seconds
```

### Install from GitHub Release

Download the latest `claude-usage` binary directly — no `git clone` required:

```bash
mkdir -p ~/.local/bin
curl -fsSL https://github.com/long-910/claude-tmux-status/releases/latest/download/claude-usage \
  -o ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage
```

Then configure tmux manually. Add to `~/.tmux.conf`:

```tmux
# claude-tmux-status
set -g status-right-length 200
set -g status-right "#(claude-usage short) | %H:%M %Y-%m-%d"
bind U run-shell "claude-usage toggle && tmux refresh-client -S"
bind B display-popup -E -w 82 -h 40 "claude-usage dashboard"
```

Reload tmux and set up the Stop hook:

```bash
tmux source-file ~/.tmux.conf
claude-usage --install-hook
```

First run — populate the cache:

```bash
claude-usage --refresh
```

### Manual install

One-liner (no git required):

```bash
curl -fsSL https://raw.githubusercontent.com/long-910/claude-tmux-status/main/install.sh | bash
```

Or from a local clone:

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
- Claude Code
  - Claude.ai subscription: `~/.claude/.credentials.json` required for rate-limit % display
  - AWS Bedrock / API key: no credentials file needed — cost display from local JSONL

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
| `claude-usage dashboard` | Interactive full-screen dashboard | Only if Claude was active |
| `claude-usage --version` | Show version and exit | No |
| `claude-usage --help` | Show help and exit | No |
| `claude-usage --install-hook` | Add Stop hook to Claude Code | No |
| `claude-usage --uninstall-hook` | Remove Stop hook from Claude Code | No |

### Cost mode

Press `<prefix> + U` (or run `claude-usage toggle`) to switch to cost display:

```
5h:$14.21 day:$14.21 7d:$53.17
```

### Dashboard

Press `<prefix> + B` (or run `claude-usage dashboard`) to open a full-screen dashboard.
Requires **tmux 3.2+** for the popup window. Runs in any terminal otherwise.

```
+==============================================================================+
|                            Claude Usage Dashboard                            |
+==============================================================================+
|   Rate Limits                                                     [just now] |
|                                                                              |
|   5h:  78%  [###############.....]  reset 2h47m       (allowed_warning)      |
|   7d:  84%  [################....]  reset 5.1d        (allowed_warning)      |
|                                                                              |
+------------------------------------------------------------------------------+
|   Token Usage & Cost                                                         |
|                                                                              |
|               Input     Output    CacheRd    CacheWr       Cost              |
|       5h      38.5K     127.8K      24.6M       1.3M     $14.21              |
|    Today      38.5K     127.8K      24.6M       1.3M     $14.21              |
|       7d      80.0K     468.9K      89.5M       5.1M     $53.17              |
|                                                                              |
+------------------------------------------------------------------------------+
|   Top Projects  (7-day cost)                                                 |
|                                                                              |
|   my-app                    $28.34  [##########........]  53%                |
|   claude-plugin             $14.12  [#####.............]  27%                |
|   dotfiles                  $10.71  [####..............]  20%                |
|                                                                              |
+------------------------------------------------------------------------------+
|   Provider: anthropic(auto)  |  Mode: default(no API)  |  Display: percent   |
+==============================================================================+

  [r] refresh    [w] toggle watch(30s)    [q] quit
```

| Key | Action |
|-----|--------|
| `r` | Refresh data immediately |
| `w` | Toggle 30-second auto-watch mode |
| `q` / `Esc` | Quit |

### `long` mode output

Claude.ai subscription (Pro plan example):
```
-- Rate Limit [default(no API)] provider:auto(anthropic) ------------------
  5h:  78% [XXXXXX..] reset:2h47m  (allowed)
  7d:  84% [XXXXXXX.] reset:4.3d   (allowed_warning)
  last updated: just now
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

AWS Bedrock / API key:
```
-- Rate Limit [default(no API)] provider:auto(other) ------------------
  [not available] AWS Bedrock / API key — showing cost from local JSONL
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

---

## Update behavior

By default, the API is called only when Claude is actively running. When idle, stale cached data is shown with a `[Xm ago]` indicator — no tokens consumed.

### Settings file

Edit `~/.claude/claude-tmux-status.json`:

```json
{
  "realtime": false,
  "cache_ttl": 300,
  "provider": "auto"
}
```

| Key | Values | Default | Description |
|-----|--------|---------|-------------|
| `realtime` | `true` / `false` | `false` | Poll API every `cache_ttl` seconds regardless of Claude activity |
| `cache_ttl` | integer (seconds) | `300` | Cache TTL |
| `provider` | `"auto"` / `"anthropic"` / `"bedrock"` / `"other"` | `"auto"` | Override provider detection. `"auto"` checks `~/.claude/.credentials.json` |

### Realtime mode (opt-in)

Set `"realtime": true` in the settings file above.

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
