#!/usr/bin/env python3
"""Watch a PChome 24h product page price and alert when below a threshold.

- Scrapes the current price from HTML (o-prodPrice__price...).
- Stores state to avoid duplicate alerts.
- No external dependencies.

Exit codes:
- 0 ok
- 2 parse/fetch error

Output JSON:
{
  runAt, ok,
  url, label, productId,
  price, originalPrice,
  threshold,
  below,
  shouldNotify,
  reason
}
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "pchome_watch_config.json")
STATE_PATH = os.path.join(BASE_DIR, "pchome_watch_state.json")


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


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw price watcher)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        # site is UTF-8
        return raw.decode("utf-8", errors="ignore")


def parse_price(html: str) -> tuple[int | None, int | None]:
    # Current sale price
    m = re.search(r'o-prodPrice__price[^>]*>\s*\$\s*([0-9]{1,3}(?:,[0-9]{3})*)\s*<', html)
    price = int(m.group(1).replace(",", "")) if m else None

    # Original price if present
    m2 = re.search(r'o-prodPrice__originalPrice[^>]*>\s*\$\s*([0-9]{1,3}(?:,[0-9]{3})*)\s*<', html)
    orig = int(m2.group(1).replace(",", "")) if m2 else None

    return price, orig


def main() -> int:
    cfg = load_json(CONFIG_PATH, {})
    st = load_json(STATE_PATH, {"version": 1, "lastPrice": None, "lastSeenAt": None, "lastNotifiedAt": None, "notifiedBelow": False})

    url = cfg.get("url")
    threshold = int(cfg.get("threshold") or 0)
    label = cfg.get("label") or url
    product_id = cfg.get("productId")
    cooldown_min = int(cfg.get("cooldownMinutes") or 360)

    now_s = int(time.time())

    try:
        html = fetch_html(url)
        price, orig = parse_price(html)
        if price is None:
            out = {
                "runAt": utc_now_iso(),
                "ok": False,
                "url": url,
                "label": label,
                "productId": product_id,
                "price": None,
                "originalPrice": None,
                "threshold": threshold,
                "below": None,
                "shouldNotify": False,
                "reason": "parse_failed",
            }
            print(json.dumps(out, ensure_ascii=False))
            return 2

        below = price < threshold

        # Decide notify
        should = False
        reason = ""
        last_notified = st.get("lastNotifiedAt")
        last_notified_s = int(last_notified) if isinstance(last_notified, (int, float, str)) and str(last_notified).isdigit() else None

        cooldown_ok = True
        if last_notified_s is not None and (now_s - last_notified_s) < cooldown_min * 60:
            cooldown_ok = False

        if below and cooldown_ok:
            # Notify when first time going below OR periodic reminder while below
            if not st.get("notifiedBelow"):
                should = True
                reason = "crossed_below"
            else:
                should = True
                reason = "still_below_cooldown_elapsed"

        # Update state
        st["lastPrice"] = price
        st["lastSeenAt"] = now_s
        if below:
            if should:
                st["lastNotifiedAt"] = now_s
                st["notifiedBelow"] = True
        else:
            st["notifiedBelow"] = False

        save_json(STATE_PATH, st)

        out = {
            "runAt": utc_now_iso(),
            "ok": True,
            "url": url,
            "label": label,
            "productId": product_id,
            "price": price,
            "originalPrice": orig,
            "threshold": threshold,
            "below": below,
            "shouldNotify": should,
            "reason": reason or ("below" if below else "above_or_equal"),
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0

    except Exception as e:
        out = {
            "runAt": utc_now_iso(),
            "ok": False,
            "url": url,
            "label": label,
            "productId": product_id,
            "price": None,
            "originalPrice": None,
            "threshold": threshold,
            "below": None,
            "shouldNotify": False,
            "reason": f"error:{type(e).__name__}:{e}",
        }
        print(json.dumps(out, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
