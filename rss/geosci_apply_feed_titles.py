#!/usr/bin/env python3
"""Step A: apply human-friendly feed titles/publisher into SQLite feeds.

Reads rss/geosci_feed_name_map.json and updates feeds.title/publisher.
No network.
"""

from __future__ import annotations

import json
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "geosci_feed_name_map.json")


def main() -> int:
    m = json.load(open(MAP_PATH, "r", encoding="utf-8"))
    conn = rss_store.connect()
    rss_store.init_db(conn)

    updated = 0
    for url, meta in m.items():
        title = meta.get("title")
        publisher = meta.get("publisher")
        if not (title or publisher):
            continue
        cur = conn.execute("SELECT id FROM feeds WHERE url=?", (url,)).fetchone()
        if not cur:
            continue
        conn.execute(
            "UPDATE feeds SET title=COALESCE(?, title), publisher=COALESCE(?, publisher), updated_at_utc=? WHERE url=?",
            (title, publisher, rss_store.utc_now_iso(), url),
        )
        updated += 1

    conn.commit()
    print(json.dumps({"ok": True, "updated": updated}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
