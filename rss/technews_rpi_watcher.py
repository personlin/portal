#!/usr/bin/env python3
"""Watch Raspberry Pi-related RSS feed and extract new items.

Feed (Mailchimp campaign archive RSS):
https://us8.campaign-archive.com/feed?u=e31349e35c9c4dfb8bdf10e69&id=e2ce89f288

Stores seen ids in rss/technews_rpi_state.json.
Designed for inclusion in the DAILY morning digest under category: 科技新聞.

Output JSON:
{
  runAt, feedUrl, category, newCount,
  newItems: [{title, link, published, summary}]
}

No external deps.
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
STATE_PATH = os.path.join(BASE_DIR, "technews_rpi_state.json")
FEED_URL = "https://us8.campaign-archive.com/feed?u=e31349e35c9c4dfb8bdf10e69&id=e2ce89f288"
CATEGORY = "科技新聞"


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
            "User-Agent": "OpenClaw TechNews watcher/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
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
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
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

    # RSS usually: <rss><channel><item>...
    channel = None
    for c in list(root):
        if strip_ns(c.tag).lower() == "channel":
            channel = c
            break
    if channel is None:
        channel = root

    items = []
    for item in channel.iter():
        if strip_ns(item.tag).lower() != "item":
            continue

        title = None
        link = None
        guid = None
        pub = None
        desc = None

        for sub in list(item):
            st = strip_ns(sub.tag).lower()
            if st == "title":
                title = (sub.text or "").strip() or None
            elif st == "link":
                link = (sub.text or "").strip() or None
            elif st == "guid":
                guid = (sub.text or "").strip() or None
            elif st in ("pubdate", "published", "date"):
                pub = (sub.text or "").strip() or None
            elif st in ("description", "summary", "content") and desc is None:
                desc = (sub.text or "").strip() or None

        sid = sha1(guid or link or title or "")
        items.append({
            "sid": sid,
            "title": title,
            "link": link,
            "published": pub,
            "summary": clean_text(desc),
        })

    # Keep feed order (often newest first). If pub exists and is sortable string, we can sort desc.
    # But Mailchimp pubDate is RFC-822; avoid parsing; keep original order.

    new_items = []
    for it in items:
        sid = it["sid"]
        if sid in seen:
            continue
        seen[sid] = {"seenAt": utc_now_iso()}
        new_items.append({k: it.get(k) for k in ("title", "link", "published", "summary")})

    # trim
    MAX_SEEN = 3000
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
        "category": CATEGORY,
        "newCount": len(new_items),
        "newItems": new_items,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
