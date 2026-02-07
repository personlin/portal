#!/usr/bin/env python3
"""Step 4A: Preview pending GeoSci items from SQLite (no sending).

Lists pending/failed deliveries for channel=geosci, target=morning_digest.

Outputs JSON with:
- counts
- by_feed counts
- sample items

No external deps.
"""

from __future__ import annotations

import json
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = rss_store.list_pending_items(conn, channel=str(args.channel), target=str(args.target), limit=int(args.limit))

    # counts
    total_pending = conn.execute(
        "SELECT COUNT(*) FROM deliveries WHERE channel=? AND (target IS ? OR target=?) AND status IN ('pending','failed')",
        (str(args.channel), str(args.target), str(args.target)),
    ).fetchone()[0]

    by_feed = conn.execute(
        """
        SELECT f.url AS feed_url, COALESCE(f.title, f.url) AS feed_title, COUNT(*) AS c
        FROM deliveries d
        JOIN items i ON i.id=d.item_id
        JOIN feeds f ON f.id=i.feed_id
        WHERE d.channel=? AND (d.target IS ? OR d.target=?) AND d.status IN ('pending','failed')
        GROUP BY f.url
        ORDER BY c DESC
        """,
        (str(args.channel), str(args.target), str(args.target)),
    ).fetchall()

    sample = []
    for r in rows:
        sample.append(
            {
                "itemId": r["id"],
                "title": r["title"],
                "link": r["link"],
                "publishedAt": r["published_at"],
                "feedUrl": r["feed_url"],
                "feedTitle": r["feed_title"],
                "deliveryId": r["delivery_id"],
                "deliveryStatus": r["delivery_status"],
            }
        )

    out = {
        "ok": True,
        "channel": str(args.channel),
        "target": str(args.target),
        "pendingCount": int(total_pending),
        "byFeed": [dict(r) for r in by_feed],
        "sample": sample,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
