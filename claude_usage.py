#!/usr/bin/env python3
"""
claude_usage.py - Claude Code usage aggregator for tmux status bar

Reads ~/.claude/projects/**/*.jsonl and aggregates token usage.
Supports multiple time windows: 5h (rate-limit window), today, 7d.

Usage:
  claude-usage short    # tmux compact: 5h + 7d costs
  claude-usage long     # full token breakdown per window
  claude-usage json     # JSON with all windows
"""

import json
import os
import glob
import sys
from datetime import datetime, date, timedelta, timezone
from typing import Optional

# Claude Sonnet 4.x pricing (USD per million tokens)
PRICING = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_create": 3.75,
}

# Claude Code rate-limit window (rolling hours)
RATE_LIMIT_HOURS = 5


def empty_totals() -> dict:
    return {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "records": 0}


def add_usage(totals: dict, usage: dict) -> None:
    totals["input"] += usage.get("input_tokens", 0)
    totals["output"] += usage.get("output_tokens", 0)
    totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
    totals["cache_create"] += usage.get("cache_creation_input_tokens", 0)
    totals["records"] += 1


def load_all_records() -> list[tuple[datetime, dict]]:
    """Load all (timestamp, usage) pairs from ~/.claude/projects/."""
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
                        dt = datetime.fromisoformat(
                            ts.replace("Z", "+00:00")
                        )
                        records.append((dt, usage))
                    except Exception:
                        continue
        except Exception:
            continue

    return records


def aggregate(records: list, since: datetime) -> dict:
    """Sum usage for all records at or after `since`."""
    totals = empty_totals()
    for dt, usage in records:
        if dt >= since:
            add_usage(totals, usage)
    return totals


def calc_cost(totals: dict) -> float:
    """Approximate USD cost from token totals."""
    return (
        totals["input"] * PRICING["input"]
        + totals["output"] * PRICING["output"]
        + totals["cache_read"] * PRICING["cache_read"]
        + totals["cache_create"] * PRICING["cache_create"]
    ) / 1_000_000


def fmt_tokens(n: int) -> str:
    """Format: 1234 -> 1.2K, 1234567 -> 1.2M"""
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


def window_summary(totals: dict) -> str:
    """One-line compact: out:67.9K $13.74"""
    return f"out:{fmt_tokens(totals['output'])} {fmt_cost(calc_cost(totals))}"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "short"

    now = datetime.now(timezone.utc)
    since_5h = now - timedelta(hours=RATE_LIMIT_HOURS)
    since_today = datetime.combine(
        date.today(), datetime.min.time(), tzinfo=timezone.utc
    )
    since_7d = now - timedelta(days=7)

    records = load_all_records()

    t5h = aggregate(records, since_5h)
    tday = aggregate(records, since_today)
    t7d = aggregate(records, since_7d)

    if mode == "short":
        # Compact for tmux status bar
        # 🤖 5h:out:1.2K $2.31 | day:$13.74 | 7d:$45.20
        print(
            f"🤖 "
            f"5h:{fmt_tokens(t5h['output'])} {fmt_cost(calc_cost(t5h))} | "
            f"day:{fmt_cost(calc_cost(tday))} | "
            f"7d:{fmt_cost(calc_cost(t7d))}"
        )

    elif mode == "long":
        def line(label: str, t: dict) -> str:
            c = calc_cost(t)
            return (
                f"{label}: "
                f"in:{fmt_tokens(t['input'])} "
                f"out:{fmt_tokens(t['output'])} "
                f"cr:{fmt_tokens(t['cache_read'])} "
                f"cw:{fmt_tokens(t['cache_create'])} "
                f"cost:{fmt_cost(c)}"
            )

        print(line(f"5h  (last {RATE_LIMIT_HOURS}h)", t5h))
        print(line("day (today)           ", tday))
        print(line("7d  (last 7 days)     ", t7d))

    elif mode == "json":
        output = {
            "5h": {**t5h, "cost_usd": round(calc_cost(t5h), 6)},
            "today": {**tday, "cost_usd": round(calc_cost(tday), 6)},
            "7d": {**t7d, "cost_usd": round(calc_cost(t7d), 6)},
            "generated_at": now.isoformat(),
        }
        print(json.dumps(output, indent=2))

    else:
        print(f"Usage: {sys.argv[0]} [short|long|json]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
