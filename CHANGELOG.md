# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.5.0] - 2026-02-23

### Added
- **TPM support**: Install via Tmux Plugin Manager with `@plugin 'long-910/claude-tmux-status'`
- Configurable tmux options: `@claude-tmux-toggle-key`, `@claude-tmux-install-hook`, `@claude-tmux-auto-status`, `@claude-tmux-realtime`, `@claude-tmux-cache-ttl`
- `claude-tmux-status.tmux` entry point (auto-installs script, configures status-right, keybinding, Stop hook)
- Multilingual README: English (default), Japanese (`README.ja.md`), Chinese (`README.zh.md`)
- `CHANGELOG.md` (this file)

### Changed
- Moved `claude_usage.py` to `scripts/claude_usage.py`
- `install.sh` updated to use `scripts/` path

---

## [0.4.0] - 2026-02-23

### Added
- **Zero-consumption default mode**: API is called only when both:
  1. Cache is older than `cache_ttl` (5 min)
  2. `~/.claude/projects/**/*.jsonl` was updated within the last `cache_ttl` seconds
- Staleness indicator: `[15m ago]` shown when Claude is idle and cache is stale
- `--install-hook` command: adds Claude Code `Stop` hook to `~/.claude/settings.json` for auto-refresh at session end
- `--refresh` command: forced single API update (for hooks / manual use)
- Settings file: `~/.claude/claude-tmux-status.json` (`realtime`, `cache_ttl`)
- No-cache message: `[--] run: claude-usage --refresh` on first run

### Changed
- Default mode no longer polls API on a timer — zero token consumption when Claude is idle
- Realtime mode (5-min poll) now opt-in via `"realtime": true` in settings

### Fixed
- `sed -i` on WSL2 silently emptying files — replaced with direct `Write` operations

---

## [0.3.0] - 2026-02-23

### Added
- **Percentage display** from Anthropic API rate-limit response headers:
  - `anthropic-ratelimit-unified-5h-utilization` — 5-hour window
  - `anthropic-ratelimit-unified-7d-utilization` — 7-day window
  - Reset countdown (e.g. `(2h47m)`)
  - Status indicators: `!` for `allowed_warning`, `X` for `denied`
- 5-minute cache (`/tmp/claude-usage-ratelimit.json`) to minimize API calls
- `toggle` command and `<prefix>+U` keybinding to switch percent / cost display
- `--` prefix removed from output; mode label added to `long` output

### Changed
- Default short output: percentage-first (`5h:78%(2h47m) 7d:84%!`)
- Cost display now accessible via `toggle` or `cost` subcommand

---

## [0.2.0] - 2026-02-23

### Added
- Multi-window cost aggregation: 5h rolling, today, 7d rolling
- `long` mode: per-window token breakdown with `in / out / cache_r / cache_w`
- `json` mode: structured JSON with all windows and timestamps

### Changed
- `short` output redesigned: `5h:$2.31 | day:$13.74 | 7d:$45.20`
- Refactored data loading to single `load_all_records()` pass

### Fixed
- CRLF line endings on WSL causing `set: pipefail: invalid option` error
- Added `.gitattributes` to enforce LF

---

## [0.1.0] - 2026-02-23

### Added
- Initial release
- Reads `~/.claude/projects/**/*.jsonl` to aggregate today's token usage
- Approximate USD cost calculation (Claude Sonnet 4.x pricing)
- Three output modes: `short` (tmux), `long` (detailed), `json`
- `install.sh`: one-command installer that patches `~/.tmux.conf`
- Integration with existing `tmux-mem-cpu-load` status bar
