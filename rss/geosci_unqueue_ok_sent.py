#!/usr/bin/env python3
"""Cleanup: unqueue items that are already fully delivered after enrichment.

If a delivery is currently pending but:
- item.enrich_status='ok'
- delivery.sent_at_utc is not null
- delivery.sent_at_utc >= item.enriched_at_utc
then it's already been delivered in complete form, so set status back to 'sent'.

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
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    cur = conn.execute(
        """
        UPDATE deliveries
        SET status='sent', error=NULL
        WHERE channel=? AND target=? AND status='pending'
          AND item_id IN (
            SELECT i.id
            FROM items i
            JOIN deliveries d2 ON d2.item_id=i.id AND d2.channel=? AND d2.target=?
            WHERE i.enrich_status='ok'
              AND d2.status='pending'
              AND d2.sent_at_utc IS NOT NULL
              AND i.enriched_at_utc IS NOT NULL
              AND d2.sent_at_utc >= i.enriched_at_utc
          )
        """,
        (str(args.channel), str(args.target), str(args.channel), str(args.target)),
    )
    conn.commit()

    print(json.dumps({"ok": True, "fixed": int(cur.rowcount or 0)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
