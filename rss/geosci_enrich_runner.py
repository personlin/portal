#!/usr/bin/env python3
"""Step B5-1: GeoSci enrichment runner (skeleton + stats only).

This version:
- selects candidate items
- reports what is missing
- DOES NOT modify DB
- DOES NOT call network or models

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


def is_empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT
          id, title, link, doi,
          abstract, title_zh_tw, abstract_zh_tw,
          summary_en, summary_zh_tw,
          enrich_status, enrich_error,
          first_seen_at_utc
        FROM items
        WHERE enrich_status IS NULL OR enrich_status != 'ok'
        ORDER BY first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    missing = {
        "abstract_en": 0,
        "title_zh_tw": 0,
        "abstract_zh_tw": 0,
        "summary_en": 0,
        "summary_zh_tw": 0,
    }
    status_counts = {}

    sample = []
    for r in rows:
        st = r[9] if r[9] is not None else None
        status_counts[st] = status_counts.get(st, 0) + 1

        if is_empty(r[4]):
            missing["abstract_en"] += 1
        if is_empty(r[5]):
            missing["title_zh_tw"] += 1
        if is_empty(r[6]):
            missing["abstract_zh_tw"] += 1
        if is_empty(r[7]):
            missing["summary_en"] += 1
        if is_empty(r[8]):
            missing["summary_zh_tw"] += 1

        if len(sample) < 10:
            sample.append({
                "id": int(r[0]),
                "status": st,
                "title": r[1],
                "missing": {
                    "abstract_en": is_empty(r[4]),
                    "title_zh_tw": is_empty(r[5]),
                    "abstract_zh_tw": is_empty(r[6]),
                    "summary_en": is_empty(r[7]),
                    "summary_zh_tw": is_empty(r[8]),
                }
            })

    out = {
        "ok": True,
        "selected": len(rows),
        "missingTotals": missing,
        "statusCounts": status_counts,
        "sample": sample,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
