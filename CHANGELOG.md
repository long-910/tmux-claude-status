# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.6.0] - 2026-03-01

### Added
- **Unit tests** (`tests/test_claude_usage.py`): 53 tests covering formatters, aggregation, cost calculation, cache I/O, settings, display mode toggle, hook management, and short output formatting
- **CI workflow** (`.github/workflows/ci.yml`): lint (shellcheck + Python syntax) and pytest across Python 3.10/3.11/3.12 matrix on every push/PR to `main`
- **Release workflow** (`.github/workflows/release.yml`): triggered by `v*.*.*` tags — automatically extracts the matching CHANGELOG section and creates a GitHub Release
- **CONTRIBUTING.md**: architecture overview, data sources, cost calculation pricing, CI/CD and release process documentation
- **README badges**: CI status, License, Python 3.10+, tmux 3.0+, GitHub Sponsors

### Changed
- README (EN/JA/ZH): moved developer-specific sections (data sources, cost calculation pricing) to `CONTRIBUTING.md`; simplified update behavior description; added link to `CONTRIBUTING.md`

### Fixed
- `install.sh`: removed unused `CURRENT_RIGHT` variable (shellcheck SC2034)
- `uninstall.sh`: replaced `A && B || C` pattern with `if/then` (shellcheck SC2015)

---

## [0.5.1] - 2026-02-23

### Fixed
- Staleness indicator (`[Xm ago]`, `[Xh ago]`, `[Xd ago]`) was displayed in Japanese (`前`) — changed to English
- Updated all README files (EN/JA/ZH) to reflect the English-only display format

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
