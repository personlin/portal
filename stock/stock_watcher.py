#!/usr/bin/env python3
"""Daily stock/ETF watcher using Yahoo Finance chart endpoint.

Features:
- % change vs previous close
- skips sending if no new trading day since last run (per market)
- highlights biggest movers by abs % change
- detects cross above/below moving averages (20/60/240 SMA by default)

Outputs a single JSON object to stdout.

Note: Yahoo Finance is an unofficial endpoint; may rate-limit.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def yahoo_chart(symbol: str, range_: str = "400d", interval: str = "1d") -> tuple[str, dict]:
    """Fetch Yahoo chart data.

    Returns (resolvedSymbol, result).

    For Taiwan tickers, Yahoo sometimes uses .TWO (OTC) instead of .TW; we fallback.
    """

    def fetch(sym: str) -> dict:
        sym_q = urllib.parse.quote(sym, safe="")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym_q}?range={range_}&interval={interval}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OpenClaw stock watcher)"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        data = json.loads(raw)
        err = data.get("chart", {}).get("error")
        if err:
            raise RuntimeError(f"Yahoo error for {sym}: {err}")
        return data["chart"]["result"][0]

    try:
        return symbol, fetch(symbol)
    except urllib.error.HTTPError as e:
        # OTC fallback for Taiwan
        if e.code == 404 and symbol.endswith(".TW"):
            alt = symbol[:-3] + ".TWO"
            return alt, fetch(alt)
        raise


def last_two_closes(result: dict) -> tuple[tuple[int, float], tuple[int, float]]:
    ts = result.get("timestamp") or []
    closes = (result.get("indicators", {}).get("quote", [{}])[0].get("close")) or []
    pairs = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        pairs.append((int(t), float(c)))
    if len(pairs) < 2:
        raise RuntimeError("Not enough close data")
    return pairs[-2], pairs[-1]


def sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if window <= 0:
        return out
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= window:
            s -= values[i - window]
        if i >= window - 1:
            out[i] = s / window
    return out


def compute_ma_cross(closes: list[float], window: int) -> dict | None:
    ma = sma(closes, window)
    if len(closes) < window + 2:
        return None
    i2 = len(closes) - 1
    i1 = i2 - 1
    if ma[i1] is None or ma[i2] is None:
        return None

    prev_close, curr_close = closes[i1], closes[i2]
    prev_ma, curr_ma = float(ma[i1]), float(ma[i2])

    crossed_up = prev_close <= prev_ma and curr_close > curr_ma
    crossed_down = prev_close >= prev_ma and curr_close < curr_ma
    if not (crossed_up or crossed_down):
        return None
    return {
        "window": window,
        "direction": "up" if crossed_up else "down",
        "prevClose": prev_close,
        "currClose": curr_close,
        "prevMA": prev_ma,
        "currMA": curr_ma,
    }


def to_local_date(ts: int, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    return datetime.fromtimestamp(ts, tz=tz).date().isoformat()


def yahoo_quote_batch(symbols: list[str]) -> dict[str, dict]:
    """Fetch quote metadata (e.g., marketCap) for many symbols at once.

    Best-effort: if blocked/rate-limited, returns empty dict and we fall back.
    """
    if not symbols:
        return {}
    try:
        # Yahoo recommends <= 200 symbols; we're far below.
        sym_str = ",".join(symbols)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(sym_str)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OpenClaw stock watcher)"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        data = json.loads(raw)
        out: dict[str, dict] = {}
        for q in (data.get("quoteResponse", {}) or {}).get("result", []) or []:
            sym = q.get("symbol")
            if sym:
                out[sym] = q
        return out
    except Exception:
        return {}


def run_market(market_key: str, indices: list[str], tickers: list[str], ma_cfg: dict, highlights_top_n: int, state: dict, name_map: dict | None = None, commit_state: bool = True) -> dict:
    items = []
    errors = []
    market_date = None
    market_tz = None

    # Build a list including indices for chart pulls
    all_syms = list(indices or []) + list(tickers or [])

    # Batch quote metadata for market cap sorting (best-effort)
    quote_meta = yahoo_quote_batch(all_syms)

    for sym in all_syms:
        try:
            resolved_sym, res = yahoo_chart(sym)
            meta = res.get("meta", {})
            market_tz = meta.get("exchangeTimezoneName") or market_tz or "UTC"

            (t_prev, c_prev), (t_last, c_last) = last_two_closes(res)
            d_last = to_local_date(t_last, market_tz)

            # capture a single market_date (latest among symbols)
            if market_date is None or d_last > market_date:
                market_date = d_last

            pct = (c_last - c_prev) / c_prev * 100.0

            closes_raw = (res.get("indicators", {}).get("quote", [{}])[0].get("close")) or []
            closes = [float(c) for c in closes_raw if c is not None]

            signals = {}
            for label, win in ma_cfg.items():
                cross = compute_ma_cross(closes, int(win))
                if cross:
                    signals[label] = cross

            q = quote_meta.get(resolved_sym) or quote_meta.get(sym) or {}
            market_cap = q.get("marketCap")

            name = meta.get("shortName") or meta.get("longName") or q.get("shortName") or sym

            # Build a friendly display label (esp. for Taiwan tickers)
            display = name
            code = None
            if isinstance(sym, str) and (sym.endswith(".TW") or sym.endswith(".TWO")):
                code = sym.split(".")[0]
                tw_name = None
                if isinstance(name_map, dict):
                    tw_name = name_map.get(code)
                display_name = tw_name or name
                display = f"{display_name}({code})"

            items.append({
                "symbol": sym,
                "resolvedSymbol": resolved_sym,
                "name": name,
                "code": code,
                "display": display,
                "currency": meta.get("currency") or q.get("currency"),
                "exchange": meta.get("exchangeName") or meta.get("fullExchangeName") or q.get("fullExchangeName"),
                "marketTz": market_tz,
                "date": d_last,
                "close": c_last,
                "prevClose": c_prev,
                "pct": pct,
                "marketCap": market_cap,
                "isIndex": sym in (indices or []),
                "signals": signals,
            })

        except Exception as e:
            errors.append({"symbol": sym, "error": f"{type(e).__name__}: {e}"})

    # Determine whether this market has a new trading day since last sent
    last_sent = (state.get("lastSent", {}) or {}).get(market_key)
    should_send = bool(market_date) and (last_sent != market_date)

    # Extra guard for TW: only send if today actually had a close (i.e., marketDate == today's date in Asia/Taipei)
    if market_key == "tw" and market_date:
        today_tpe = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()
        if market_date != today_tpe:
            should_send = False

    # Sort for highlights (exclude indices)
    movers = sorted(
        [it for it in items if it.get("pct") is not None and not it.get("isIndex")],
        key=lambda x: abs(x["pct"]),
        reverse=True,
    )
    highlights = movers[:highlights_top_n]

    # Extract MA crosses
    crosses = []
    for it in items:
        for label, cross in (it.get("signals") or {}).items():
            crosses.append({
                "symbol": it["symbol"],
                "name": it.get("name"),
                "label": label,
                **cross,
            })

    # Market-cap sort for display (descending; unknown caps at end)
    def cap_key(it: dict):
        cap = it.get("marketCap")
        return (-int(cap), it.get("symbol")) if isinstance(cap, (int, float)) else (10**30, it.get("symbol"))

    items_sorted = sorted(items, key=cap_key)

    # Split indices for nicer formatting downstream
    indices_items = [it for it in items_sorted if it.get("isIndex")]
    securities_items = [it for it in items_sorted if not it.get("isIndex")]

    report = {
        "market": market_key,
        "marketDate": market_date,
        "marketTz": market_tz,
        "shouldSend": should_send,
        "count": len(items),
        "indices": indices_items,
        "items": securities_items,
        "highlights": highlights,
        "crosses": crosses,
        "errors": errors,
    }

    if should_send and commit_state:
        state.setdefault("lastSent", {})[market_key] = market_date

    return report


def main() -> int:
    cfg = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"version": 1, "lastSent": {}})

    ma_cfg = (cfg.get("movingAverages") or {"month": 20, "quarter": 60, "year": 240})
    top_n = int((cfg.get("highlights") or {}).get("topN", 6))

    # Optional: --market tw|us (so separate schedules don't interfere)
    markets = ["tw", "us"]
    if "--market" in sys.argv:
        i = sys.argv.index("--market")
        if i + 1 < len(sys.argv):
            markets = [sys.argv[i + 1]]

    # Default behavior (legacy): commit lastSent state when a new market day is detected.
    # For scheduling systems that may terminate mid-run, you can disable state writes and
    # commit only after successful delivery (see mark_sent.py).
    commit_state = True
    if "--no-save-state" in sys.argv:
        commit_state = False

    out = {
        "runAt": utc_now_iso(),
        "reports": [],
    }

    for market_key in markets:
        if market_key not in cfg:
            continue
        indices = cfg[market_key].get("indices") or []
        tickers = cfg[market_key].get("tickers") or []

        name_map = None
        if market_key == "tw":
            p = cfg[market_key].get("nameMapPath")
            if p and os.path.exists(p):
                try:
                    name_map = load_json(p, {})
                except Exception:
                    name_map = None

        rep = run_market(market_key, indices, tickers, ma_cfg, top_n, state, name_map=name_map, commit_state=commit_state)
        rep["runLabel"] = cfg[market_key].get("runLabel")
        out["reports"].append(rep)

    if commit_state:
        save_json(STATE_PATH, state)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
