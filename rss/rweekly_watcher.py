#!/usr/bin/env python3
"""Watch R Weekly Atom feed and extract new items.

- Feed: https://rweekly.org/atom.xml
- Stores seen ids in rss/rweekly_state.json
- Designed for daily use in the morning digest.

Output JSON:
{
  runAt, feedUrl, newCount,
  newItems: [{title, link, published, summary}]
}

Note: R Weekly feed usually includes summary content in <summary>/<content>.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "rweekly_state.json")
FEED_URL = "https://rweekly.org/atom.xml"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"version": 1, "seen": {}, "lastRunAt": None}
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
            "User-Agent": "OpenClaw RWeekly watcher/1.0",
            "Accept": "application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def clean_text(s: str | None) -> str | None:
    if not s:
        return None
    # Remove HTML tags if present
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def main() -> int:
    state = load_state()
    seen = state.get("seen", {})
    if not isinstance(seen, dict):
        seen = {}

    data = fetch(FEED_URL)
    root = ET.fromstring(data)

    items = []
    for child in list(root):
        if strip_ns(child.tag).lower() != "entry":
            continue

        title = None
        link = None
        entry_id = None
        published = None
        summary = None

        for sub in list(child):
            st = strip_ns(sub.tag).lower()
            if st == "title":
                title = (sub.text or "").strip() or None
            elif st == "id":
                entry_id = (sub.text or "").strip() or None
            elif st == "published":
                published = (sub.text or "").strip() or None
            elif st == "updated" and not published:
                published = (sub.text or "").strip() or None
            elif st in ("summary", "content") and summary is None:
                summary = (sub.text or "").strip() or None
            elif st == "link":
                href = sub.attrib.get("href")
                rel = (sub.attrib.get("rel") or "alternate").lower()
                if href and (link is None or rel == "alternate"):
                    link = href

        sid = sha1(entry_id or link or title or "")
        items.append({
            "sid": sid,
            "title": title,
            "link": link,
            "published": published,
            "summary": clean_text(summary),
        })

    # newest first: published/updated can be ISO, sort descending
    items = sorted(items, key=lambda x: (x.get("published") or ""), reverse=True)

    new_items = []
    for it in items:
        sid = it["sid"]
        if sid in seen:
            continue
        seen[sid] = {"seenAt": utc_now_iso()}
        new_items.append({k: it.get(k) for k in ("title", "link", "published", "summary")})

    # trim
    MAX_SEEN = 2000
    if len(seen) > MAX_SEEN:
        drop = len(seen) - MAX_SEEN
        for k in list(seen.keys())[:drop]:
            seen.pop(k, None)

    state["seen"] = seen
    state["lastRunAt"] = utc_now_iso()
    save_state(state)

    out = {
        "runAt": state["lastRunAt"],
        "feedUrl": FEED_URL,
        "newCount": len(new_items),
        "newItems": new_items,
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
