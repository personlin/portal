#!/usr/bin/env python3
"""Central Weather Administration (Taiwan) earthquake digest.

Fetches the "recent earthquakes" module HTML and extracts events.
Outputs JSON for inclusion in morning digest.

Source page:
- https://www.cwa.gov.tw/V8/C/E/index.html
Module used:
- https://www.cwa.gov.tw/V8/C/E/MOD/EQ_ROW.html

No external dependencies.
"""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MODULE_URL = "https://www.cwa.gov.tw/V8/C/E/MOD/EQ_ROW.html"
BASE_URL = "https://www.cwa.gov.tw"
TZ = ZoneInfo("Asia/Taipei")


def http_get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw cwa_earthquake_digest)",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.6",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class Eq:
    num: str
    intensity: str
    time_mmdd_hhmm: str
    place: str
    depth_km: float | None
    magnitude: float | None
    url: str

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "intensity": self.intensity,
            "time": self.time_mmdd_hhmm,
            "place": self.place,
            "depthKm": self.depth_km,
            "magnitude": self.magnitude,
            "url": self.url,
        }


def parse_event_dt(mmdd_hhmm: str, now: datetime) -> datetime | None:
    # mmdd_hhmm like "02/17 05:44"
    m = re.match(r"^(\d{2})/(\d{2})\s+(\d{2}):(\d{2})$", (mmdd_hhmm or "").strip())
    if not m:
        return None
    mon, day, hh, mi = map(int, m.groups())
    year = now.year
    # handle year boundary: if event month/day is in the future relative to now, it belongs to last year.
    try_dt = datetime(year, mon, day, hh, mi, tzinfo=TZ)
    if try_dt > now + timedelta(days=1):
        try_dt = datetime(year - 1, mon, day, hh, mi, tzinfo=TZ)
    return try_dt


def parse_eq_row_html(html: str) -> list[Eq]:
    events: list[Eq] = []

    # Split into <tr ...> blocks.
    for m in re.finditer(r"<tr[^>]*class=\"eq-row\"[\s\S]*?</tr>", html, flags=re.I):
        tr = m.group(0)

        num = strip_tags(re.search(r"<td[^>]*headers=\"num\"[^>]*>([\s\S]*?)</td>", tr, flags=re.I).group(1)) if re.search(r"headers=\"num\"", tr) else ""
        intensity = strip_tags(re.search(r"<td[^>]*headers=\"maximum\"[^>]*>([\s\S]*?)</td>", tr, flags=re.I).group(1)) if re.search(r"headers=\"maximum\"", tr) else ""

        href_m = re.search(r"<a[^>]+href=\"([^\"]+)\"", tr, flags=re.I)
        href = href_m.group(1) if href_m else ""
        url = href if href.startswith("http") else (BASE_URL + href if href.startswith("/") else href)

        time_m = re.search(r"<span>(\d{2}/\d{2}\s+\d{2}:\d{2})</span>", tr)
        t = time_m.group(1) if time_m else ""

        # Place
        place = ""
        pm = re.search(r"<li[^>]*>[\s\S]*?<span>地點</span>[\s\S]*?</li>", tr)
        if pm:
            place = strip_tags(pm.group(0))
            place = place.replace("地點", "").strip()

        # Depth
        depth_km = None
        dm = re.search(r"深度</span>[\s\S]*?(\d+(?:\.\d+)?)\s*km", tr)
        if dm:
            try:
                depth_km = float(dm.group(1))
            except Exception:
                depth_km = None

        # Magnitude
        magnitude = None
        mm = re.search(r"地震規模</span>[\s\S]*?(\d+(?:\.\d+)?)", tr)
        if mm:
            try:
                magnitude = float(mm.group(1))
            except Exception:
                magnitude = None

        if num or url or t:
            events.append(Eq(num=num, intensity=intensity, time_mmdd_hhmm=t, place=place, depth_km=depth_km, magnitude=magnitude, url=url))

    return events


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    now = datetime.now(TZ)
    html = http_get(MODULE_URL, timeout=20)
    events = parse_eq_row_html(html)

    # filter by recency
    cutoff = now - timedelta(hours=int(args.hours))
    out = []
    for e in events:
        dt = parse_event_dt(e.time_mmdd_hhmm, now)
        if not dt:
            continue
        if dt >= cutoff:
            out.append((dt, e))

    out.sort(key=lambda x: x[0], reverse=True)
    out = out[: int(args.limit)]

    payload = {
        "ok": True,
        "source": "cwa",
        "runAtTaipei": now.isoformat(timespec="seconds"),
        "hours": int(args.hours),
        "count": len(out),
        "items": [
            {
                **e.to_dict(),
                "timeTaipei": dt.isoformat(timespec="minutes"),
            }
            for dt, e in out
        ],
        "sourceUrl": "https://www.cwa.gov.tw/V8/C/E/index.html",
    }

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
