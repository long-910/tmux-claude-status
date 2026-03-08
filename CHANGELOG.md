# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.7.0] - 2026-03-08

### Added
- **`dashboard` command** — interactive full-screen dashboard, designed for use as a tmux popup (`<prefix>+D`)
  - **Rate Limits panel**: 5h/7d utilization with ASCII progress bars and reset countdowns (Claude.ai subscription)
  - **Token Usage & Cost panel**: input / output / cache-read / cache-write breakdown for 5h, today, and 7d windows
  - **Top Projects panel**: per-project 7-day cost ranking with proportional progress bars (top 8 projects)
  - **Status bar**: provider, update mode, and current display mode
  - Interactive keys: `r` = refresh, `w` = toggle 30-second auto-watch, `q` / `Esc` / `Ctrl-C` = quit
  - Non-TTY safe: prints once and exits when stdin is not a terminal (piped / testing)
- **`@claude-tmux-dashboard-key` TPM option** (default `"D"`): binds `<prefix>+D` to open the dashboard in a tmux popup (`display-popup -E`); set to `"none"` to disable
- **`decode_project_name()`**: converts Claude Code's encoded project folder names (`-home-user-proj`) to human-readable labels
- **`load_jsonl_records_by_project()`**: groups JSONL token records by project for per-project cost breakdown
- **`progress_bar()`**: fixed-width ASCII progress bar renderer (used in both dashboard and available for extension)
- **`--version` / `-V` flag**: prints `claude-usage X.Y.Z` and exits; version also appears right-aligned in the dashboard status bar and as a `"version"` field in `json` output
- **`VERSION` constant** (`"0.7.0"`) defined at module level — single source of truth for all version surfaces
- 27 new unit tests: `TestVersion` (5), `TestDecodeProjectName` (5), `TestProgressBar` (7), `TestLoadJsonlByProject` (3), `TestRenderDashboard` (7) — total 92 tests

### Fixed
- **Dashboard keybinding default changed `"D"` → `"B"`**: `<prefix>+D` is bound to `choose-client -Z` in tmux by default, causing a conflict. The new default `B` (mnemonic: **B**oard) is free in all standard tmux configurations. Users who set `@claude-tmux-dashboard-key "D"` explicitly should update to `"B"` or another free key.

### Notes
- tmux popup (`display-popup`) requires **tmux 3.2+**. The `dashboard` command itself works in any terminal without tmux.

---

## [0.6.1] - 2026-03-05

### Added
- **Provider auto-detection**: Checks `~/.claude/.credentials.json` for an OAuth token at startup.
  - Found → `"anthropic"` mode: rate-limit % display (existing behavior)
  - Not found → `"other"` mode: cost display from local JSONL (no API call)
  - AWS Bedrock and raw API-key users now see `[cost] 5h:$x.xxx day:$x.xxx 7d:$x.xxx` automatically
- **`"provider"` setting** in `~/.claude/claude-tmux-status.json`:
  `"auto"` (default) | `"anthropic"` | `"bedrock"` | `"other"` — overrides auto-detection
- **5h-only plan support**: When the Anthropic API returns no weekly (7d) limit headers,
  the status bar shows only `5h:xx%(Xhxxm)` without the `7d:` field
- **`json` command** now includes a `"provider"` field in output
- **`long` command** now shows detected provider and omits or annotates 7d when not available
- New unit tests: `TestDetectProvider` (6 cases), `TestHas7dLimit` (4 cases), two `TestShortPercent` cases for 5h-only plans (65 tests total)

### Notes
- The rate-limit % display has been tested with **Claude.ai Pro plan only**.
  Behavior on Max, Team, Enterprise, AWS Bedrock, and raw API-key plans is untested.
  If the display is incorrect for your plan, please [file an issue](https://github.com/long-910/claude-tmux-status/issues).

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
