#!/usr/bin/env python3
"""Simple RSS/Atom watcher.

- Reads feed URLs from rss/feeds.txt (one per line)
- Stores seen item ids in rss/state.json
- Prints a JSON payload to stdout with new items (for easy use by agent)

Designed to be run daily.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDS_PATH = os.path.join(BASE_DIR, "feeds.txt")
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_feeds() -> list[str]:
    if not os.path.exists(FEEDS_PATH):
        return []
    urls: list[str] = []
    with open(FEEDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            urls.append(u)
    return urls


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


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def text(el: ET.Element | None) -> str | None:
    if el is None:
        return None
    t = (el.text or "").strip()
    return t or None


def find_first(el: ET.Element, names: list[str]) -> ET.Element | None:
    for n in names:
        r = el.find(n)
        if r is not None:
            return r
    return None


def normalize_id(feed_url: str, entry: dict) -> str:
    # Prefer explicit ids
    for k in ("id", "guid", "link"):
        v = entry.get(k)
        if v:
            return sha1(f"{feed_url}|{k}|{v}")
    # Fallback: title+published
    title = entry.get("title") or ""
    published = entry.get("published") or ""
    return sha1(f"{feed_url}|fallback|{title}|{published}")


def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OpenClaw RSS Watcher/1.0 (+https://openclaw.ai)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed(feed_url: str, data: bytes) -> tuple[str | None, list[dict]]:
    # Very small Atom/RSS parser using ElementTree.
    # Handles RSS 2.0 (<rss><channel><item>) and Atom (<feed><entry>).

    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None, []

    def strip_ns(tag: str) -> str:
        return tag.split("}")[-1] if "}" in tag else tag

    root_tag = strip_ns(root.tag).lower()

    items: list[dict] = []
    feed_title: str | None = None

    if root_tag == "rss":
        channel = next((c for c in list(root) if strip_ns(c.tag).lower() == "channel"), None)
        if channel is None:
            return None, []
        feed_title = text(find_first(channel, ["title"]))
        for item in channel.findall("item"):
            title = text(find_first(item, ["title"]))
            link = text(find_first(item, ["link"]))
            guid = text(find_first(item, ["guid"]))
            pub = text(find_first(item, ["pubDate"]))
            items.append({
                "title": title,
                "link": link,
                "guid": guid,
                "published": pub,
            })
    elif root_tag == "feed":
        feed_title = text(find_first(root, ["title"]))
        # Atom default namespace is common; ElementTree needs full ns to find,
        # so iterate children and match by stripped tag.
        for child in list(root):
            if strip_ns(child.tag).lower() != "entry":
                continue
            title = None
            link = None
            entry_id = None
            published = None
            updated = None
            for sub in list(child):
                st = strip_ns(sub.tag).lower()
                if st == "title":
                    title = (sub.text or "").strip() or None
                elif st == "id":
                    entry_id = (sub.text or "").strip() or None
                elif st == "published":
                    published = (sub.text or "").strip() or None
                elif st == "updated":
                    updated = (sub.text or "").strip() or None
                elif st == "link":
                    # Prefer alternate/href
                    href = sub.attrib.get("href")
                    rel = (sub.attrib.get("rel") or "alternate").lower()
                    if href and (link is None or rel == "alternate"):
                        link = href
            items.append({
                "title": title,
                "link": link,
                "id": entry_id,
                "published": published or updated,
            })
    else:
        # Unknown root; try to find items generically
        for item in root.findall(".//item"):
            title = text(find_first(item, ["title"]))
            link = text(find_first(item, ["link"]))
            guid = text(find_first(item, ["guid"]))
            pub = text(find_first(item, ["pubDate"]))
            items.append({"title": title, "link": link, "guid": guid, "published": pub})

    # Clean items: drop empties
    cleaned = []
    for it in items:
        if not (it.get("title") or it.get("link")):
            continue
        cleaned.append(it)
    return feed_title, cleaned


def main() -> int:
    feeds = load_feeds()
    state = load_state()
    seen: dict[str, dict] = state.get("seen", {})

    all_new: list[dict] = []
    errors: list[dict] = []

    for url in feeds:
        try:
            data = fetch(url)
            title, items = parse_feed(url, data)

            feed_key = url
            feed_seen = seen.get(feed_key, {})
            if not isinstance(feed_seen, dict):
                feed_seen = {}

            new_items = []
            for it in items:
                nid = normalize_id(url, it)
                if nid in feed_seen:
                    continue
                feed_seen[nid] = {"seenAt": utc_now_iso()}
                new_items.append({
                    "feedUrl": url,
                    "feedTitle": title,
                    "title": it.get("title"),
                    "link": it.get("link"),
                    "published": it.get("published"),
                })

            # Trim seen set to keep file bounded
            # Keep only the most recent N ids.
            MAX_SEEN = 2000
            if len(feed_seen) > MAX_SEEN:
                # dict insertion order is preserved in py3.7+
                drop = len(feed_seen) - MAX_SEEN
                for k in list(feed_seen.keys())[:drop]:
                    feed_seen.pop(k, None)

            seen[feed_key] = feed_seen
            all_new.extend(new_items)

        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            errors.append({"feedUrl": url, "error": str(e)})
        except Exception as e:
            errors.append({"feedUrl": url, "error": f"{type(e).__name__}: {e}"})

    state["seen"] = seen
    state["lastRunAt"] = utc_now_iso()
    save_state(state)

    out = {
        "runAt": state["lastRunAt"],
        "feedCount": len(feeds),
        "newCount": len(all_new),
        "newItems": all_new,
        "errors": errors,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
