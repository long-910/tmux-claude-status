#!/usr/bin/env python3
"""claude_usage.py - Claude Code usage for tmux status bar

Default mode (no API calls):
  Reads cached rate-limit data. Updates cache only when Claude Code
  JSONL files change (i.e., when Claude is actually being used).
  Shows staleness indicator when data is not fresh.

Realtime mode (opt-in, costs tokens):
  Polls Anthropic API every 5 min regardless of Claude activity.
  Cost: ~$0.001/day, ~$0.009/week, ~$0.04/month.

Commands:
  claude-usage              short display (current mode)
  claude-usage short        compact for tmux
  claude-usage long         full breakdown (percent + cost)
  claude-usage json         JSON output
  claude-usage cost         force cost display
  claude-usage toggle       switch percent / cost display
  claude-usage --refresh    force API update (for hooks / manual)
  claude-usage --install-hook  add Stop hook to ~/.claude/settings.json

Settings: ~/.claude/claude-tmux-status.json
  { "realtime": false, "cache_ttl": 300 }
"""

import json
import os
import glob
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta, timezone

CREDENTIALS_FILE = os.path.expanduser("~/.claude/.credentials.json")
SETTINGS_FILE    = os.path.expanduser("~/.claude/claude-tmux-status.json")
MODE_FILE        = os.path.expanduser("~/.claude/tmux-display-mode")
CACHE_FILE       = os.path.expanduser("~/.claude/tmux-rate-limit-cache.json")
CLAUDE_PROJECTS  = os.path.expanduser("~/.claude/projects")
CLAUDE_SETTINGS  = os.path.expanduser("~/.claude/settings.json")

DEFAULT_SETTINGS = {"realtime": False, "cache_ttl": 300}

PRICING = {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_create": 3.75}


# -- Settings -----------------------------------------------------------------

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception:
        return dict(DEFAULT_SETTINGS)


# -- Display mode (percent / cost) --------------------------------------------

def get_display_mode():
    try:
        return open(MODE_FILE).read().strip()
    except Exception:
        return "percent"


def toggle_display_mode():
    new = "cost" if get_display_mode() == "percent" else "percent"
    with open(MODE_FILE, "w") as f:
        f.write(new)
    return new


# -- JSONL latest mtime -------------------------------------------------------

def latest_jsonl_mtime():
    mt = 0.0
    if not os.path.isdir(CLAUDE_PROJECTS):
        return mt
    for path in glob.glob(f"{CLAUDE_PROJECTS}/**/*.jsonl", recursive=True):
        try:
            mt = max(mt, os.path.getmtime(path))
        except Exception:
            pass
    return mt


# -- Cache --------------------------------------------------------------------

def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# -- Anthropic API call -------------------------------------------------------

def fetch_rate_limit():
    """One minimal API call (claude-haiku, 1 output token) to get rate-limit headers.
    Cost: ~$0.0000046 per call (8 input + 1 output tokens at Haiku pricing).
    """
    try:
        with open(CREDENTIALS_FILE) as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "."}],
    }).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body, headers=headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            rl = {k.lower(): v for k, v in r.headers.items()
                  if "ratelimit-unified" in k.lower()}
            return {
                "fetched_at": time.time(),
                "util_5h":    float(rl.get("anthropic-ratelimit-unified-5h-utilization", 0)),
                "util_7d":    float(rl.get("anthropic-ratelimit-unified-7d-utilization", 0)),
                "reset_5h":   int(rl.get("anthropic-ratelimit-unified-5h-reset", 0)),
                "reset_7d":   int(rl.get("anthropic-ratelimit-unified-7d-reset", 0)),
                "status_5h":  rl.get("anthropic-ratelimit-unified-5h-status", ""),
                "status_7d":  rl.get("anthropic-ratelimit-unified-7d-status", ""),
                "overall":    rl.get("anthropic-ratelimit-unified-status", ""),
            }
    except Exception:
        return None


def get_rate_limit(force=False):
    """Return rate-limit data from cache or API depending on settings.

    Default mode (realtime=False):
      API is called ONLY when both conditions are true:
        1. Cache is older than cache_ttl
        2. JSONL files were updated after the last cache write
           (= Claude was actually used since last update)

    Realtime mode (realtime=True):
      API is called whenever cache is older than cache_ttl,
      regardless of Claude activity. Costs ~$0.001/day.
    """
    settings = load_settings()
    ttl      = settings.get("cache_ttl", 300)
    realtime = settings.get("realtime", False)
    cache    = load_cache()
    now      = time.time()
    cache_age = (now - cache["fetched_at"]) if cache else float("inf")

    if force:
        data = fetch_rate_limit()
        if data:
            save_cache(data)
        return data or cache

    if cache and cache_age < ttl:
        return cache  # Cache is fresh; never hit the API

    if realtime:
        # Realtime mode: refresh on TTL expiry regardless of Claude activity
        data = fetch_rate_limit()
        if data:
            save_cache(data)
            return data
        return cache

    # Default mode: only refresh if Claude was RECENTLY active (within ttl window).
    # "Recently active" = JSONL files were updated within the last ttl seconds.
    # This ensures we never call the API when Claude is idle, even if cache is stale.
    jmtime = latest_jsonl_mtime()
    recently_active = jmtime > 0 and (now - jmtime) < ttl

    if recently_active:
        data = fetch_rate_limit()
        if data:
            save_cache(data)
            return data

    return cache  # Claude idle or API failed → return stale cache (may be None)


# -- Claude Code hook install -------------------------------------------------

def install_hook():
    """Add a Stop hook to ~/.claude/settings.json so the cache is updated
    whenever a Claude Code session ends (zero extra token cost for the hook
    itself; the hook triggers one --refresh API call per session end)."""
    refresh_cmd = (
        os.path.expanduser("~/.local/bin/claude-usage")
        + " --refresh >/dev/null 2>&1"
    )
    try:
        with open(CLAUDE_SETTINGS) as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    hooks     = settings.setdefault("hooks", {})
    stop_list = hooks.setdefault("Stop", [])

    for entry in stop_list:
        for h in entry.get("hooks", []):
            if "claude-usage" in h.get("command", ""):
                print("[skip] Stop hook already configured")
                return

    stop_list.append({"hooks": [{"type": "command", "command": refresh_cmd}]})

    with open(CLAUDE_SETTINGS, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("[ok] Stop hook added to ~/.claude/settings.json")
    print("     Cache will update automatically at end of each Claude session.")


def uninstall_hook():
    """Remove the claude-usage Stop hook from ~/.claude/settings.json."""
    try:
        with open(CLAUDE_SETTINGS) as f:
            settings = json.load(f)
    except Exception:
        print("[skip] ~/.claude/settings.json not found or invalid")
        return

    hooks = settings.get("hooks", {})
    stop_list = hooks.get("Stop", [])
    new_stop = [
        entry for entry in stop_list
        if not any("claude-usage" in h.get("command", "")
                   for h in entry.get("hooks", []))
    ]

    if len(new_stop) == len(stop_list):
        print("[skip] No claude-usage Stop hook found")
        return

    hooks["Stop"] = new_stop
    if not hooks["Stop"]:
        del hooks["Stop"]
    if not hooks:
        del settings["hooks"]

    with open(CLAUDE_SETTINGS, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("[ok] Stop hook removed from ~/.claude/settings.json")


# -- Cost aggregation from local JSONL ----------------------------------------

def load_jsonl_records():
    records = []
    if not os.path.isdir(CLAUDE_PROJECTS):
        return records
    for path in glob.glob(f"{CLAUDE_PROJECTS}/**/*.jsonl", recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    msg = data.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {})
                    if not usage:
                        continue
                    ts = data.get("timestamp")
                    if not ts:
                        continue
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        records.append((dt, usage))
                    except Exception:
                        continue
        except Exception:
            continue
    return records


def aggregate(records, since):
    t = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "records": 0}
    for dt, usage in records:
        if dt >= since:
            t["input"]        += usage.get("input_tokens", 0)
            t["output"]       += usage.get("output_tokens", 0)
            t["cache_read"]   += usage.get("cache_read_input_tokens", 0)
            t["cache_create"] += usage.get("cache_creation_input_tokens", 0)
            t["records"]      += 1
    return t


def calc_cost(t):
    return (
        t["input"]        * PRICING["input"]
        + t["output"]     * PRICING["output"]
        + t["cache_read"] * PRICING["cache_read"]
        + t["cache_create"] * PRICING["cache_create"]
    ) / 1_000_000


# -- Formatters ---------------------------------------------------------------

def fmt_tokens(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)


def fmt_cost(c):
    if c >= 100: return f"${c:.1f}"
    if c >= 10:  return f"${c:.2f}"
    return f"${c:.3f}"


def fmt_pct(v):
    return f"{v*100:.0f}%"


def fmt_reset(ts):
    secs = max(0, ts - time.time())
    if secs < 86400:
        h, m = divmod(int(secs / 60), 60)
        return f"{h}h{m:02d}m"
    return f"{secs/86400:.1f}d"


def fmt_age(fetched_at):
    """Return staleness label; empty string if data is fresh (< 2 min)."""
    if not fetched_at:
        return " [--]"
    age = time.time() - fetched_at
    if age < 120:   return ""
    if age < 3600:  return f" [{int(age/60)}m ago]"
    if age < 86400: return f" [{int(age/3600)}h ago]"
    return f" [{int(age/86400)}d ago]"


def pct_bar(v, width=8):
    filled = round(v * width)
    return "X" * filled + "." * (width - filled)


def status_ind(status):
    if status in ("denied", "blocked"): return "X"
    if "warning" in status:             return "!"
    return ""


# -- Output formatters --------------------------------------------------------

def short_percent(rl):
    u5   = rl["util_5h"]
    u7   = rl["util_7d"]
    age  = fmt_age(rl.get("fetched_at", 0))
    ind5 = status_ind(rl["status_5h"])
    ind7 = status_ind(rl["status_7d"])
    r5   = fmt_reset(rl["reset_5h"])
    return (
        f"5h:{fmt_pct(u5)}{ind5}({r5}) "
        f"7d:{fmt_pct(u7)}{ind7}"
        f"{age}"
    )


def short_cost(records):
    now  = datetime.now(timezone.utc)
    t5h  = aggregate(records, now - timedelta(hours=5))
    tday = aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))
    t7d  = aggregate(records, now - timedelta(days=7))
    return (
        f"5h:{fmt_cost(calc_cost(t5h))} "
        f"day:{fmt_cost(calc_cost(tday))} "
        f"7d:{fmt_cost(calc_cost(t7d))}"
    )


def long_output(rl, records, settings):
    lines = []
    realtime = settings.get("realtime", False)
    mode_lbl = "realtime(5min)" if realtime else "default(no API)"

    lines.append(f"-- Rate Limit [{mode_lbl}] " + "-" * 30)
    if rl:
        u5  = rl["util_5h"]
        u7  = rl["util_7d"]
        age = fmt_age(rl.get("fetched_at", 0)).strip()
        lines.append(f"  5h: {fmt_pct(u5):>4} [{pct_bar(u5)}] reset:{fmt_reset(rl['reset_5h'])}  ({rl['status_5h']})")
        lines.append(f"  7d: {fmt_pct(u7):>4} [{pct_bar(u7)}] reset:{fmt_reset(rl['reset_7d'])}  ({rl['status_7d']})")
        lines.append(f"  last updated: {age or 'just now'}")
    else:
        lines.append("  [no data] run: claude-usage --refresh")

    now = datetime.now(timezone.utc)
    def row(label, t):
        return (
            f"  {label}: in:{fmt_tokens(t['input'])} out:{fmt_tokens(t['output'])} "
            f"cr:{fmt_tokens(t['cache_read'])} cw:{fmt_tokens(t['cache_create'])} "
            f"cost:{fmt_cost(calc_cost(t))}"
        )
    lines.append("-- Token Cost [local JSONL] " + "-" * 33)
    lines.append(row("5h ", aggregate(records, now - timedelta(hours=5))))
    lines.append(row("day", aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))))
    lines.append(row("7d ", aggregate(records, now - timedelta(days=7))))
    return "\n".join(lines)


# -- Main ---------------------------------------------------------------------

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "short"

    if cmd == "--refresh":
        data = fetch_rate_limit()
        if data:
            save_cache(data)
            sys.stdout.write(f"[ok] 5h={fmt_pct(data['util_5h'])} 7d={fmt_pct(data['util_7d'])}\n")
            sys.stdout.flush()
        else:
            sys.stderr.write("[err] API fetch failed\n")
        return

    if cmd == "--install-hook":
        install_hook()
        return

    if cmd == "--uninstall-hook":
        uninstall_hook()
        return

    if cmd == "toggle":
        new = toggle_display_mode()
        sys.stdout.write(f"mode -> {new}\n")
        sys.stdout.flush()
        return

    if cmd in ("short", ""):
        mode = get_display_mode()
        if mode == "cost":
            out = "[cost] " + short_cost(load_jsonl_records())
        else:
            rl = get_rate_limit()
            if rl:
                out = short_percent(rl)
            else:
                out = "[--] run: claude-usage --refresh"
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        return

    if cmd == "cost":
        out = short_cost(load_jsonl_records())
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        return

    if cmd == "long":
        s = load_settings()
        sys.stdout.write(long_output(get_rate_limit(), load_jsonl_records(), s) + "\n")
        sys.stdout.flush()
        return

    if cmd == "json":
        rl = get_rate_limit()
        records = load_jsonl_records()
        now = datetime.now(timezone.utc)
        def w(since):
            t = aggregate(records, since)
            return {**t, "cost_usd": round(calc_cost(t), 6)}
        out = {
            "rate_limit":   rl,
            "cost": {
                "5h":    w(now - timedelta(hours=5)),
                "today": w(datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)),
                "7d":    w(now - timedelta(days=7)),
            },
            "display_mode": get_display_mode(),
            "settings":     load_settings(),
            "generated_at": now.isoformat(),
        }
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
        sys.stdout.flush()
        return

    sys.stderr.write(f"Usage: {sys.argv[0]} [short|long|json|cost|toggle|--refresh|--install-hook|--uninstall-hook]\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
