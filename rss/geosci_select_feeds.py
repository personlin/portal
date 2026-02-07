#!/usr/bin/env python3
"""Step 3B: select feed fetch order from SQLite (no network).

Implements the prioritization rules:
1) never succeeded
2) consecutive_failures > 0
3) next_fetch_after_utc <= now OR NULL
4) priority DESC then next_fetch_after_utc ASC

Outputs ordered list.
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
    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT
          id, url, enabled, priority,
          last_success_at_utc, last_fetch_at_utc,
          consecutive_failures, next_fetch_after_utc,
          last_error
        FROM feeds
        WHERE enabled = 1
        ORDER BY
          CASE WHEN last_success_at_utc IS NULL THEN 0 ELSE 1 END ASC,
          CASE WHEN consecutive_failures > 0 THEN 0 ELSE 1 END ASC,
          CASE WHEN next_fetch_after_utc IS NULL THEN 0
               WHEN next_fetch_after_utc <= ? THEN 0
               ELSE 1 END ASC,
          priority DESC,
          COALESCE(next_fetch_after_utc, '') ASC,
          id ASC
        """,
        (rss_store.utc_now_iso(),),
    ).fetchall()

    out = {
        "ok": True,
        "count": len(rows),
        "order": [dict(r) for r in rows],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
