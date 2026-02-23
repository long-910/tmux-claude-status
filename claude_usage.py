#!/usr/bin/env python3
"""
claude_usage.py - Claude Code usage aggregator for tmux status bar

Reads ~/.claude/projects/**/*.jsonl and aggregates token usage.
Outputs a compact status string suitable for tmux status-right.
"""

import json
import os
import glob
import sys
from datetime import datetime, date
from typing import Optional

# Claude Sonnet 4.x pricing (per million tokens, USD)
PRICING = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_create": 3.75,
}


def get_usage(target_date: Optional[date] = None) -> dict:
    """Aggregate token usage from all Claude project JSONL files."""
    if target_date is None:
        target_date = date.today()

    totals = {
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_create": 0,
        "records": 0,
    }

    claude_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_dir):
        return totals

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

                    # Filter by date
                    ts = data.get("timestamp")
                    if ts:
                        try:
                            dt = datetime.fromisoformat(
                                ts.replace("Z", "+00:00")
                            ).astimezone().date()
                            if dt != target_date:
                                continue
                        except Exception:
                            continue

                    totals["input"] += usage.get("input_tokens", 0)
                    totals["output"] += usage.get("output_tokens", 0)
                    totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
                    totals["cache_create"] += usage.get(
                        "cache_creation_input_tokens", 0
                    )
                    totals["records"] += 1

        except Exception:
            continue

    return totals


def calc_cost(totals: dict) -> float:
    """Calculate approximate USD cost from token totals."""
    return (
        totals["input"] * PRICING["input"]
        + totals["output"] * PRICING["output"]
        + totals["cache_read"] * PRICING["cache_read"]
        + totals["cache_create"] * PRICING["cache_create"]
    ) / 1_000_000


def fmt_tokens(n: int) -> str:
    """Format token count: 1234 -> 1.2K, 1234567 -> 1.2M"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "short"

    totals = get_usage()
    cost = calc_cost(totals)

    total_tokens = totals["input"] + totals["output"]

    if mode == "short":
        # Compact: 🤖 1.2K/5.6K $0.42
        print(
            f"🤖 in:{fmt_tokens(totals['input'])} "
            f"out:{fmt_tokens(totals['output'])} "
            f"${cost:.3f}"
        )
    elif mode == "long":
        # Detailed breakdown
        print(
            f"Claude | "
            f"in:{fmt_tokens(totals['input'])} "
            f"out:{fmt_tokens(totals['output'])} "
            f"cache_r:{fmt_tokens(totals['cache_read'])} "
            f"cache_w:{fmt_tokens(totals['cache_create'])} "
            f"total:{fmt_tokens(total_tokens)} "
            f"cost:${cost:.3f}"
        )
    elif mode == "json":
        totals["cost_usd"] = round(cost, 6)
        print(json.dumps(totals, indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [short|long|json]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
