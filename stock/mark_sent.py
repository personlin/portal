#!/usr/bin/env python3
"""Mark a market's lastSent date in stock/state.json.

Use this after successfully delivering a notification when stock_watcher.py was
run with --no-save-state.

Usage:
  python3 mark_sent.py --market tw --date 2026-02-04
"""

from __future__ import annotations

import argparse
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["tw", "us"], required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD in that market's local TZ")
    args = ap.parse_args()

    state = load_json(STATE_PATH, {"version": 1, "lastSent": {}})
    state.setdefault("lastSent", {})[args.market] = args.date
    save_json(STATE_PATH, state)

    print(json.dumps({"ok": True, "market": args.market, "date": args.date}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
