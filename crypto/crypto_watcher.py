#!/usr/bin/env python3
"""Crypto volatility watcher (no API key) using CoinGecko.

Supports:
- Daily summary
- Frequent alert checks with cooldown

Data source: CoinGecko /coins/markets endpoint.

State file keeps last alert timestamps to prevent spam.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_markets(ids: list[str], vs: str = "usd") -> list[dict]:
    params = {
        "vs_currency": vs,
        "ids": ",".join(ids),
        "price_change_percentage": "1h,24h",
    }
    url = "https://api.coingecko.com/api/v3/coins/markets?" + urllib.parse.urlencode(params)

    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "OpenClaw crypto watcher/1.0",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            return json.loads(raw)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    raise last_err


def fmt_pct(p: float | None) -> str:
    if p is None:
        return "—"
    arrow = "▲" if p > 0 else ("▼" if p < 0 else "■")
    return f"{arrow} {p:+.1f}%"


def fmt_price(p: float | None) -> str:
    if p is None:
        return "—"
    if p >= 1000:
        return f"${p:,.0f}"
    if p >= 1:
        return f"${p:,.2f}"
    return f"${p:.6f}"


def run(mode: str) -> dict:
    cfg = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"version": 1, "lastAlertAt": {}})

    coins = cfg.get("coins") or []
    ids = [c["id"] for c in coins]
    id_to_symbol = {c["id"]: c.get("symbol") or c["id"] for c in coins}

    th1 = float((cfg.get("thresholds") or {}).get("pct_1h", 3.0))
    th24 = float((cfg.get("thresholds") or {}).get("pct_24h", 8.0))
    cooldown_s = int(float(cfg.get("cooldownMinutes", 30)) * 60)

    data = fetch_markets(ids)
    now = int(time.time())

    items = []
    alerts = []

    for row in data:
        cid = row.get("id")
        sym = id_to_symbol.get(cid, (row.get("symbol") or "").upper() or cid)
        price = row.get("current_price")
        p1 = row.get("price_change_percentage_1h_in_currency")
        p24 = row.get("price_change_percentage_24h_in_currency")

        items.append({
            "id": cid,
            "symbol": sym,
            "price": price,
            "pct_1h": p1,
            "pct_24h": p24,
        })

        if mode == "alerts":
            # Determine if any threshold exceeded
            triggered = []
            if p1 is not None and abs(p1) >= th1:
                triggered.append("1h")
            if p24 is not None and abs(p24) >= th24:
                triggered.append("24h")
            if not triggered:
                continue

            key = f"{cid}"  # one cooldown per coin regardless of window
            last = (state.get("lastAlertAt") or {}).get(key)
            if last is not None and (now - int(last)) < cooldown_s:
                continue

            (state.setdefault("lastAlertAt", {}))[key] = now
            alerts.append({
                "id": cid,
                "symbol": sym,
                "price": price,
                "pct_1h": p1,
                "pct_24h": p24,
                "triggered": triggered,
            })

    save_json(STATE_PATH, state)

    # Sort for readability
    items_sorted = sorted(items, key=lambda x: x["symbol"])
    alerts_sorted = sorted(alerts, key=lambda x: max(abs(x.get("pct_1h") or 0), abs(x.get("pct_24h") or 0)), reverse=True)

    return {
        "runAt": utc_now_iso(),
        "mode": mode,
        "thresholds": {"pct_1h": th1, "pct_24h": th24, "cooldownMinutes": cooldown_s // 60},
        "items": items_sorted,
        "alerts": alerts_sorted,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["summary", "alerts"], default="alerts")
    args = ap.parse_args()

    out = run(args.mode)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
