#!/usr/bin/env python3
"""Step C4: finalize enrich_status to 'ok' when all required fields exist.

Rule: if an item has
- abstract
- title_zh_tw
- abstract_zh_tw
- summary_en
- summary_zh_tw
then set enrich_status='ok'.

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
    conn = rss_store.connect()
    rss_store.init_db(conn)

    # Mark ok where all fields exist
    conn.execute(
        """
        UPDATE items
        SET enrich_status='ok', enrich_error=NULL
        WHERE (enrich_status IS NULL OR enrich_status IN ('pending','abstract_ok','translated_ok','summarized_ok'))
          AND abstract IS NOT NULL AND abstract != ''
          AND title_zh_tw IS NOT NULL AND title_zh_tw != ''
          AND abstract_zh_tw IS NOT NULL AND abstract_zh_tw != ''
          AND summary_en IS NOT NULL AND summary_en != ''
          AND summary_zh_tw IS NOT NULL AND summary_zh_tw != ''
        """
    )
    conn.commit()

    ok_count = conn.execute("SELECT COUNT(*) FROM items WHERE enrich_status='ok'").fetchone()[0]
    pending_count = conn.execute("SELECT COUNT(*) FROM items WHERE enrich_status IS NULL OR enrich_status!='ok'").fetchone()[0]

    out = {"ok": True, "okItems": int(ok_count), "notOkItems": int(pending_count)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
