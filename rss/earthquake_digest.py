#!/usr/bin/env python3
"""Daily digest for USGS Significant Earthquakes (past day).

Fetches the Atom feed and summarizes key fields:
- magnitude, location, time (UTC + Asia/Taipei), depth (if available), link.

Stores last sent feed updated timestamp in rss/earthquake_state.json.
Prints JSON to stdout.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "earthquake_state.json")
FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.atom"


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"version": 1, "lastSentUpdated": None}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OpenClaw USGS Digest/1.0 (+https://openclaw.ai)",
            "Accept": "application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_iso(ts: str) -> datetime:
    # handles '2026-01-31T00:00:00Z'
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def fmt_time(dt: datetime) -> tuple[str, str]:
    dt_utc = dt.astimezone(timezone.utc)
    dt_tpe = dt.astimezone(ZoneInfo("Asia/Taipei"))
    return (
        dt_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        dt_tpe.replace(microsecond=0).isoformat(),
    )


def parse_entry_title(title: str) -> tuple[float | None, str]:
    # Common format: "M 6.5 - 10 km SSW of ..."
    m = re.match(r"\s*M\s*([0-9.]+)\s*-\s*(.*)$", title)
    if m:
        return float(m.group(1)), m.group(2).strip()
    return None, title.strip()


def main() -> int:
    state = load_state()
    data = fetch(FEED_URL)
    root = ET.fromstring(data)

    feed_updated = None
    entries = []

    for child in list(root):
        tag = strip_ns(child.tag).lower()
        if tag == "updated":
            feed_updated = (child.text or "").strip() or None
        if tag != "entry":
            continue

        title = None
        updated = None
        link = None

        for sub in list(child):
            st = strip_ns(sub.tag).lower()
            if st == "title":
                title = (sub.text or "").strip() or None
            elif st == "updated":
                updated = (sub.text or "").strip() or None
            elif st == "link":
                href = sub.attrib.get("href")
                rel = (sub.attrib.get("rel") or "alternate").lower()
                if href and (link is None or rel == "alternate"):
                    link = href

        if not title:
            continue
        mag, place = parse_entry_title(title)
        dt = parse_iso(updated) if updated else None
        utc_s, tpe_s = (None, None)
        if dt:
            utc_s, tpe_s = fmt_time(dt)

        entries.append({
            "title": title,
            "mag": mag,
            "place": place,
            "timeUtc": utc_s,
            "timeTaipei": tpe_s,
            "link": link,
        })

    # Sort by magnitude desc then time desc
    entries_sorted = sorted(entries, key=lambda e: ((e.get("mag") or 0.0), e.get("timeUtc") or ""), reverse=True)

    should_send = True
    if feed_updated and state.get("lastSentUpdated") == feed_updated:
        should_send = False

    if should_send and feed_updated:
        state["lastSentUpdated"] = feed_updated
        save_state(state)

    out = {
        "feedUrl": FEED_URL,
        "runAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feedUpdated": feed_updated,
        "shouldSend": should_send,
        "count": len(entries_sorted),
        "items": entries_sorted,
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
