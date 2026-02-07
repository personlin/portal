#!/usr/bin/env python3
"""Step B2: Enrich GeoSci items with Abstract (HTML + Crossref) and write to SQLite.

- Selects items where enrich_status is NULL/pending/failed (not ok) and abstract is NULL.
- For each item:
  1) Try extract abstract from article HTML (best-effort, may be blocked)
  2) Else try Crossref using DOI (extract from link if needed)

Updates items:
- doi (if extracted)
- abstract
- abstract_source: html|crossref
- enrich_status: abstract_ok|failed
- enrich_error
- enriched_at_utc

No external deps.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def http_get(url: str, timeout: int = 25, accept: str | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw geosci_enrich_abstract)",
            "Accept": accept
            or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read()
    return raw.decode(charset, errors="ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_doi(link: str) -> str | None:
    if not link:
        return None
    pats = [
        r"/doi/(10\.[0-9]{4,9}/[^/?#]+)",
        r"doi\.(?:org|doi:)/(10\.[0-9]{4,9}/[^\s?#]+)",
        r"(10\.[0-9]{4,9}/[^\s?#]+)",
    ]
    for p in pats:
        m = re.search(p, link)
        if m:
            doi = m.group(1).rstrip(").,;]")
            return doi
    return None


def crossref_lookup(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    try:
        raw = http_get(url, accept="application/json")
        data = json.loads(raw)
        return data.get("message")
    except Exception:
        return None


def crossref_abstract(doi: str) -> str | None:
    msg = crossref_lookup(doi)
    if not msg:
        return None
    abs_jats = msg.get("abstract")
    if not abs_jats:
        return None
    abs_txt = strip_tags(abs_jats)
    abs_txt = re.sub(r"^Abstract\s*", "", abs_txt, flags=re.I)
    return abs_txt if len(abs_txt) > 80 else None


def extract_abstract_from_html(html: str) -> str | None:
    meta_patterns = [
        r'<meta[^>]+name="citation_abstract"[^>]+content="([^"]+)"',
        r"<meta[^>]+name='citation_abstract'[^>]+content='([^']+)'",
        r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
    ]
    for pat in meta_patterns:
        m = re.search(pat, html, flags=re.I)
        if m:
            txt = strip_tags(m.group(1))
            if len(txt) > 80:
                return txt

    m = re.search(r"<h[1-6][^>]*>\s*Abstract\s*</h[1-6]>", html, flags=re.I)
    if m:
        tail = html[m.end() : m.end() + 10000]
        txt = strip_tags(tail)
        if len(txt) > 120:
            return txt[:4000]

    return None


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--sleep", type=float, default=0.0)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT i.id, i.title, i.link, i.doi, i.abstract, i.enrich_status
        FROM items i
        WHERE (i.abstract IS NULL OR i.abstract = '')
          AND (i.enrich_status IS NULL OR i.enrich_status IN ('pending','failed'))
        ORDER BY i.first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    results = []

    for r in rows:
        item_id = int(r[0])
        link = r[2] or ""
        doi = (r[3] or "").strip() or None

        started = time.time()
        abstract = None
        source = None
        err_parts = []

        doi2 = doi or extract_doi(link)

        # 1) HTML
        if link:
            try:
                html = http_get(link)
                abstract = extract_abstract_from_html(html)
                if abstract:
                    source = "html"
            except Exception as e:
                err_parts.append(f"html:{type(e).__name__}:{e}")

        # 2) Crossref
        if not abstract and doi2:
            try:
                abstract = crossref_abstract(doi2)
                if abstract:
                    source = "crossref"
            except Exception as e:
                err_parts.append(f"crossref:{type(e).__name__}:{e}")

        if abstract:
            conn.execute(
                """
                UPDATE items
                SET doi=COALESCE(?, doi),
                    abstract=?,
                    abstract_source=?,
                    enrich_status='abstract_ok',
                    enrich_error=NULL,
                    enriched_at_utc=?
                WHERE id=?
                """,
                (doi2, abstract, source, utc_now_iso(), item_id),
            )
            status = "abstract_ok"
            error = None
        else:
            error = ";".join(err_parts) if err_parts else "no_abstract_found"
            conn.execute(
                """
                UPDATE items
                SET doi=COALESCE(?, doi),
                    enrich_status='failed',
                    enrich_error=?,
                    enriched_at_utc=?
                WHERE id=?
                """,
                (doi2, error, utc_now_iso(), item_id),
            )
            status = "failed"

        conn.commit()

        results.append(
            {
                "itemId": item_id,
                "doi": doi2,
                "source": source,
                "abstractLen": len(abstract) if abstract else 0,
                "status": status,
                "error": error,
                "durationMs": int((time.time() - started) * 1000),
            }
        )

        if args.sleep:
            time.sleep(float(args.sleep))

    out = {"ok": True, "count": len(rows), "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
