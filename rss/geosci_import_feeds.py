#!/usr/bin/env python3
"""Step 3A: import rss/feeds.txt into SQLite feeds table.

- No network fetch.
- Ensures DB schema exists.

Usage:
  python3 rss/geosci_import_feeds.py

Outputs JSON.
"""

from __future__ import annotations

import json
import os

from rss.db import rss_store

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDS_PATH = os.path.join(BASE_DIR, "feeds.txt")
DEFAULT_CATEGORY = "GeoSci"


def load_feeds() -> list[str]:
    urls: list[str] = []
    if not os.path.exists(FEEDS_PATH):
        return urls
    with open(FEEDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            urls.append(u)
    return urls


def main() -> int:
    urls = load_feeds()
    conn = rss_store.connect()
    rss_store.init_db(conn)

    feed_ids = []
    for u in urls:
        fid = rss_store.ensure_feed(conn, u, category=DEFAULT_CATEGORY)
        feed_ids.append({"id": fid, "url": u})

    # count
    cnt = conn.execute("SELECT COUNT(*) AS c FROM feeds").fetchone()["c"]

    out = {
        "ok": True,
        "feedFileCount": len(urls),
        "dbFeedCount": int(cnt),
        "feeds": feed_ids,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
