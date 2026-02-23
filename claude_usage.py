#!/usr/bin/env python3
"""
claude_usage.py - Claude Code usage for tmux status bar

Default:  percentage display from Anthropic API rate-limit headers
Alternate: cost display from local ~/.claude/projects/**/*.jsonl

Usage:
  claude-usage [short|long|json|cost|toggle]

  short    Compact tmux display (default: percent mode)
  long     Full breakdown (both percent and cost)
  json     JSON with all data
  cost     Force cost display for this invocation
  toggle   Toggle default display mode (percent <-> cost)
"""

import json
import os
import glob
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta, timezone

# ── Config ───────────────────────────────────────────────────────────────────

CREDENTIALS_FILE = os.path.expanduser("~/.claude/.credentials.json")
MODE_FILE = os.path.expanduser("~/.claude/tmux-display-mode")    # 'percent' or 'cost'
CACHE_FILE = "/tmp/claude-usage-ratelimit.json"
CACHE_TTL = 300   # seconds between API calls (5 min)

# Claude Sonnet 4.x pricing (USD / 1M tokens)
PRICING = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_create": 3.75,
}


# ── Mode toggle ───────────────────────────────────────────────────────────────

def get_display_mode() -> str:
    """Return 'percent' or 'cost'."""
    try:
        return open(MODE_FILE).read().strip()
    except Exception:
        return "percent"


def toggle_display_mode() -> str:
    current = get_display_mode()
    new_mode = "cost" if current == "percent" else "percent"
    with open(MODE_FILE, "w") as f:
        f.write(new_mode)
    return new_mode


# ── API: rate-limit percentages ───────────────────────────────────────────────

def _load_credentials() -> str | None:
    """Return OAuth access token from ~/.claude/.credentials.json."""
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def _fetch_rate_limit() -> dict | None:
    """
    Make a 1-token API call to get anthropic-ratelimit-unified-* headers.
    Returns parsed dict or None on error.
    """
    token = _load_credentials()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "."}],
    }).encode()

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            rl = {}
            for k, v in r.headers.items():
                if "ratelimit-unified" in k.lower():
                    rl[k.lower()] = v
            return {
                "fetched_at": time.time(),
                "util_5h": float(rl.get("anthropic-ratelimit-unified-5h-utilization", 0)),
                "util_7d": float(rl.get("anthropic-ratelimit-unified-7d-utilization", 0)),
                "reset_5h": int(rl.get("anthropic-ratelimit-unified-5h-reset", 0)),
                "reset_7d": int(rl.get("anthropic-ratelimit-unified-7d-reset", 0)),
                "status_5h": rl.get("anthropic-ratelimit-unified-5h-status", ""),
                "status_7d": rl.get("anthropic-ratelimit-unified-7d-status", ""),
                "overall":   rl.get("anthropic-ratelimit-unified-status", ""),
            }
    except Exception:
        return None


def get_rate_limit() -> dict | None:
    """Return rate limit data, using cache if fresh."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            if time.time() - cached.get("fetched_at", 0) < CACHE_TTL:
                return cached
    except Exception:
        pass

    data = _fetch_rate_limit()
    if data:
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass
    return data


# ── Local JSONL: cost aggregation ─────────────────────────────────────────────

def _empty() -> dict:
    return {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "records": 0}


def _add(totals: dict, usage: dict) -> None:
    totals["input"] += usage.get("input_tokens", 0)
    totals["output"] += usage.get("output_tokens", 0)
    totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
    totals["cache_create"] += usage.get("cache_creation_input_tokens", 0)
    totals["records"] += 1


def load_jsonl_records() -> list:
    records = []
    claude_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_dir):
        return records
    for jsonl_file in glob.glob(f"{claude_dir}/**/*.jsonl", recursive=True):
        try:
            with open(jsonl_file, encoding="utf-8") as f:
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


def aggregate(records: list, since: datetime) -> dict:
    totals = _empty()
    for dt, usage in records:
        if dt >= since:
            _add(totals, usage)
    return totals


def calc_cost(totals: dict) -> float:
    return (
        totals["input"] * PRICING["input"]
        + totals["output"] * PRICING["output"]
        + totals["cache_read"] * PRICING["cache_read"]
        + totals["cache_create"] * PRICING["cache_create"]
    ) / 1_000_000


# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_cost(c: float) -> str:
    if c >= 100:
        return f"${c:.1f}"
    if c >= 10:
        return f"${c:.2f}"
    return f"${c:.3f}"


def fmt_pct(v: float) -> str:
    return f"{v*100:.0f}%"


def fmt_reset(ts: int) -> str:
    """Format seconds-until-reset as '2h47m' or '4.4d'."""
    now = time.time()
    secs = max(0, ts - now)
    if secs < 3600 * 24:
        h, m = divmod(int(secs / 60), 60)
        return f"{h}h{m:02d}m"
    return f"{secs/86400:.1f}d"


def pct_bar(v: float, width: int = 8) -> str:
    """Simple ASCII bar: ▓▓▓▓▓░░░"""
    filled = round(v * width)
    return "▓" * filled + "░" * (width - filled)


def status_indicator(status: str) -> str:
    """Color hint character for tmux (plain text; add tmux colors in config if desired)."""
    if status in ("denied", "blocked"):
        return "✗"
    if "warning" in status:
        return "!"
    return ""


# ── Output modes ──────────────────────────────────────────────────────────────

def short_percent(rl: dict) -> str:
    u5 = rl["util_5h"]
    u7 = rl["util_7d"]
    r5 = fmt_reset(rl["reset_5h"])
    ind5 = status_indicator(rl["status_5h"])
    ind7 = status_indicator(rl["status_7d"])
    return (
        f"🤖 "
        f"5h:{fmt_pct(u5)}{ind5}({r5}) "
        f"7d:{fmt_pct(u7)}{ind7}"
    )


def short_cost(records: list) -> str:
    now = datetime.now(timezone.utc)
    t5h = aggregate(records, now - timedelta(hours=5))
    tday = aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))
    t7d = aggregate(records, now - timedelta(days=7))
    return (
        f"🤖 "
        f"5h:{fmt_cost(calc_cost(t5h))} "
        f"day:{fmt_cost(calc_cost(tday))} "
        f"7d:{fmt_cost(calc_cost(t7d))}"
    )


def long_output(rl: dict | None, records: list) -> str:
    lines = []

    # Percent section
    if rl:
        u5, u7 = rl["util_5h"], rl["util_7d"]
        r5, r7 = fmt_reset(rl["reset_5h"]), fmt_reset(rl["reset_7d"])
        lines.append(f"── Rate limit (Anthropic API) {'─'*30}")
        lines.append(
            f"  5h: {fmt_pct(u5):>4} {pct_bar(u5)}  "
            f"resets in {r5}  [{rl['status_5h']}]"
        )
        lines.append(
            f"  7d: {fmt_pct(u7):>4} {pct_bar(u7)}  "
            f"resets in {r7}  [{rl['status_7d']}]"
        )
    else:
        lines.append("  [Rate limit: unavailable - API call failed]")

    # Cost section
    now = datetime.now(timezone.utc)
    since_5h = now - timedelta(hours=5)
    since_today = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    since_7d = now - timedelta(days=7)

    def row(label: str, t: dict) -> str:
        c = calc_cost(t)
        return (
            f"  {label}: "
            f"in:{fmt_tokens(t['input'])} "
            f"out:{fmt_tokens(t['output'])} "
            f"cr:{fmt_tokens(t['cache_read'])} "
            f"cw:{fmt_tokens(t['cache_create'])} "
            f"cost:{fmt_cost(c)}"
        )

    lines.append(f"── Token cost (local JSONL) {'─'*33}")
    lines.append(row("5h ", aggregate(records, since_5h)))
    lines.append(row("day", aggregate(records, since_today)))
    lines.append(row("7d ", aggregate(records, since_7d)))

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "short"

    if cmd == "toggle":
        new = toggle_display_mode()
        print(f"Display mode → {new}")
        return

    if cmd == "short":
        mode = get_display_mode()
        if mode == "cost":
            records = load_jsonl_records()
            print(short_cost(records))
        else:
            rl = get_rate_limit()
            if rl:
                print(short_percent(rl))
            else:
                records = load_jsonl_records()
                print(short_cost(records) + " [!API]")
        return

    if cmd == "cost":
        records = load_jsonl_records()
        print(short_cost(records))
        return

    if cmd == "long":
        rl = get_rate_limit()
        records = load_jsonl_records()
        print(long_output(rl, records))
        return

    if cmd == "json":
        rl = get_rate_limit()
        records = load_jsonl_records()
        now = datetime.now(timezone.utc)
        output = {
            "rate_limit": rl,
            "cost": {
                "5h":    {**aggregate(records, now - timedelta(hours=5)),
                          "cost_usd": round(calc_cost(aggregate(records, now - timedelta(hours=5))), 6)},
                "today": {**aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)),
                          "cost_usd": round(calc_cost(aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))), 6)},
                "7d":    {**aggregate(records, now - timedelta(days=7)),
                          "cost_usd": round(calc_cost(aggregate(records, now - timedelta(days=7))), 6)},
            },
            "display_mode": get_display_mode(),
            "generated_at": now.isoformat(),
        }
        print(json.dumps(output, indent=2))
        return

    print(f"Usage: {sys.argv[0]} [short|long|json|cost|toggle]", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
