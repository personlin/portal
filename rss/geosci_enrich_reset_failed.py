#!/usr/bin/env python3
"""Reset failed enrichment state for retry.

Step: B3-retry helper.

Resets items from enrich_status='failed' back to a specified status (default 'abstract_ok')
so they can be retried.

Usage:
  python3 rss/geosci_enrich_reset_failed.py --to abstract_ok --limit 100

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
    ap.add_argument("--to", default="abstract_ok")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        "SELECT id, enrich_error FROM items WHERE enrich_status='failed' ORDER BY enriched_at_utc ASC LIMIT ?",
        (int(args.limit),),
    ).fetchall()

    ids = [int(r[0]) for r in rows]
    for item_id in ids:
        conn.execute(
            "UPDATE items SET enrich_status=?, enrich_error=NULL WHERE id=?",
            (str(args.to), item_id),
        )
    conn.commit()

    print(json.dumps({"ok": True, "resetCount": len(ids), "ids": ids}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
