#!/usr/bin/env python3
"""Backfill abstracts from Crossref for items with DOI where abstract is missing.

Useful for publishers blocked by HTML fetch (e.g., OUP) when Crossref still provides abstract.

Updates:
- abstract
- abstract_source='crossref'
- enrich_status='abstract_ok' (only if abstract filled)

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import re
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def http_get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "OpenClaw geosci_crossref_backfill", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def crossref_abstract(doi: str) -> str | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    raw = http_get(url)
    data = json.loads(raw)
    msg = data.get("message") or {}
    abs_jats = msg.get("abstract")
    if not abs_jats:
        return None
    txt = strip_tags(abs_jats)
    txt = re.sub(r"^Abstract\s*", "", txt, flags=re.I)
    return txt if len(txt) > 80 else None


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT id, doi
        FROM items
        WHERE (abstract IS NULL OR abstract='')
          AND doi IS NOT NULL AND doi != ''
          AND (enrich_status IS NULL OR enrich_status IN ('pending','failed'))
        ORDER BY first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    results=[]
    for item_id, doi in rows:
        started=time.time()
        try:
            abs_txt = crossref_abstract(str(doi))
            if abs_txt:
                conn.execute(
                    """
                    UPDATE items
                    SET abstract=?, abstract_source='crossref', enrich_status='abstract_ok', enrich_error=NULL, enriched_at_utc=?
                    WHERE id=?
                    """,
                    (abs_txt, utc_now_iso(), int(item_id)),
                )
                conn.commit()
                results.append({"itemId": int(item_id), "ok": True, "doi": doi, "abstractLen": len(abs_txt), "durationMs": int((time.time()-started)*1000)})
            else:
                results.append({"itemId": int(item_id), "ok": False, "doi": doi, "error": "no_crossref_abstract", "durationMs": int((time.time()-started)*1000)})
        except Exception as e:
            results.append({"itemId": int(item_id), "ok": False, "doi": doi, "error": f"{type(e).__name__}:{e}", "durationMs": int((time.time()-started)*1000)})

    print(json.dumps({"ok": True, "count": len(rows), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
