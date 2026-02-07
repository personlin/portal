#!/usr/bin/env python3
"""Step B1: select GeoSci items pending enrichment (no network, no model).

Uses fine-grained enrich_status:
- pending / abstract_ok / translated_ok / summarized_ok / ok / failed

We select items that are not fully ok.

Outputs JSON with sample rows.
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
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT
          i.id, i.title, i.link, i.doi,
          i.enrich_status, i.enrich_error,
          i.first_seen_at_utc,
          f.title AS feed_title, f.publisher AS publisher
        FROM items i
        JOIN feeds f ON f.id = i.feed_id
        WHERE (i.enrich_status IS NULL OR i.enrich_status != 'ok')
        ORDER BY i.first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    out = {
        "ok": True,
        "count": len(rows),
        "items": [dict(r) for r in rows],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
