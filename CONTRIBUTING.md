# Contributing to tmux-claude-status

## Development Setup

```bash
git clone https://github.com/long-910/tmux-claude-status.git
cd tmux-claude-status
```

No external dependencies are required to run or develop the project.
The main script (`scripts/claude_usage.py`) uses the Python standard library only.

## Running Tests

```bash
python -m pytest tests/ -v
```

Or with the built-in runner (no pytest needed):

```bash
python -m unittest discover tests/ -v
```

## Architecture

```
tmux-claude-status/
├── scripts/claude_usage.py   # Main script: API, cache, formatters, output modes, dashboard
├── tmux-claude-status.tmux   # TPM entry point: installs script, configures tmux
├── install.sh                # Manual installer
├── uninstall.sh              # Manual uninstaller
└── tests/
    └── test_claude_usage.py  # Unit tests (87 tests)
```

### Script structure (`scripts/claude_usage.py`)

| Section | Key functions |
|---------|--------------|
| Settings | `load_settings()`, `detect_provider()` |
| Display mode | `get_display_mode()`, `toggle_display_mode()` |
| JSONL monitoring | `latest_jsonl_mtime()` |
| Cache | `load_cache()`, `save_cache()` |
| API | `fetch_rate_limit()`, `get_rate_limit()` |
| Hook management | `install_hook()`, `uninstall_hook()` |
| Cost aggregation | `load_jsonl_records()`, `load_jsonl_records_by_project()`, `aggregate()`, `calc_cost()` |
| Formatters | `fmt_tokens()`, `fmt_cost()`, `fmt_pct()`, `fmt_reset()`, `fmt_age()`, `pct_bar()`, `progress_bar()` |
| Status bar output | `short_percent()`, `short_cost()`, `long_output()` |
| Dashboard | `decode_project_name()`, `render_dashboard()`, `read_key()`, `dashboard_cmd()` |
| Entry point | `main()` |

### How it works

1. **Default mode** — zero API consumption when Claude is idle:
   - Watches `~/.claude/projects/**/*.jsonl` modification time
   - Calls the Anthropic API only when both conditions hold:
     1. Cached data is older than `cache_ttl` (default: 300 s)
     2. A JSONL file was modified within the last `cache_ttl` seconds
   - Shows stale cache with `[Xm ago]` indicator when Claude is idle

2. **Realtime mode** — polls every `cache_ttl` seconds regardless of activity:
   - Enabled via `"realtime": true` in `~/.claude/tmux-claude-status.json`
   - Cost: ~$0.001/day (claude-haiku-4-5, ~9 tokens/call)

3. **Stop hook** — single API call on session end:
   - Installed into `~/.claude/settings.json` as a Claude Code `Stop` hook
   - Ensures the cache is always fresh right after a session ends

4. **Dashboard** (`claude-usage dashboard`):
   - Renders a full-screen 80-column ASCII box with four panels:
     Rate Limits / Token Usage & Cost / Top Projects / Status
   - Uses `tty` + `termios` + `select` (stdlib) for raw keypress input with timeout
   - Decodes project folder names via `decode_project_name()` (path encoding: `/` → `-`)
   - Non-TTY safe: prints once and exits when stdin is not a terminal
   - Invoked as a tmux popup via `display-popup -E -w 82 -h 90%` (requires tmux 3.2+)

### Settings file

`~/.claude/tmux-claude-status.json`

```json
{
  "realtime": false,
  "cache_ttl": 300,
  "provider": "auto"
}
```

### Cache file

`~/.claude/tmux-rate-limit-cache.json` — stores the last API response:

```json
{
  "fetched_at": 1234567890.0,
  "util_5h":    0.78,
  "util_7d":    0.84,
  "reset_5h":   1234567890,
  "reset_7d":   1234567890,
  "status_5h":  "allowed",
  "status_7d":  "allowed_warning",
  "overall":    "allowed_warning"
}
```

## Data Sources

**Percentage** values come from Anthropic API rate-limit response headers:

| Header | Description |
|--------|-------------|
| `anthropic-ratelimit-unified-5h-utilization` | 5-hour window utilization (0.0–1.0) |
| `anthropic-ratelimit-unified-7d-utilization` | 7-day window utilization (0.0–1.0) |
| `anthropic-ratelimit-unified-5h-reset` | Epoch timestamp when 5h window resets |
| `anthropic-ratelimit-unified-7d-reset` | Epoch timestamp when 7d window resets |
| `anthropic-ratelimit-unified-5h-status` | `allowed`, `allowed_warning`, or `denied` |
| `anthropic-ratelimit-unified-7d-status` | `allowed`, `allowed_warning`, or `denied` |

These are identical to the values shown on the Claude.ai settings page.

**Cost** values are computed locally from `~/.claude/projects/**/*.jsonl`:

Each line is a JSON record. The relevant fields are:

```json
{
  "timestamp": "2026-02-23T11:23:00Z",
  "message": {
    "usage": {
      "input_tokens": 100,
      "output_tokens": 50,
      "cache_read_input_tokens": 1000,
      "cache_creation_input_tokens": 200
    }
  }
}
```

## Cost Calculation Pricing (Claude Sonnet 4.x)

| Token type | USD / 1M tokens |
|------------|-----------------|
| Input | $3.00 |
| Output | $15.00 |
| Cache read | $0.30 |
| Cache create | $3.75 |

## CI / CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push / PR to `main` | shellcheck, Python syntax, pytest (3.10–3.12) |
| `release.yml` | push `v*.*.*` tag | Create GitHub Release with CHANGELOG notes |

### Creating a release

1. Update `CHANGELOG.md` with a `## [X.Y.Z] - YYYY-MM-DD` section
2. Commit and push to `main`
3. Tag and push:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. The `release.yml` workflow will automatically create a GitHub Release

## Pull Request Guidelines

See [CLAUDE.md](CLAUDE.md) for branch naming conventions.

1. Fork and create a feature branch: `git checkout -b feat/<description>`
2. Make changes and add / update tests in `tests/`
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Push and open a PR against `main`
