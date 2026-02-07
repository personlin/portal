#!/usr/bin/env python3
"""GeoSci enrichment runner.

Step B5-2: adds abstract enrichment stage (HTML + Crossref) with per-item commits.

Modes:
- stats (default): report what is missing
- abstract: fill Abstract EN (and DOI if found) -> enrich_status='abstract_ok' or 'failed'

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def http_get(url: str, timeout: int = 25, accept: str | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw geosci_enrich_runner)",
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


def enrich_one_abstract(conn, item_id: int, title: str, link: str, doi: str | None, timeout: int) -> dict:
    started = time.time()
    err_parts = []

    doi2 = doi or extract_doi(link)
    abstract = None
    source = None

    if link:
        try:
            html = http_get(link, timeout=timeout)
            abstract = extract_abstract_from_html(html)
            if abstract:
                source = "html"
        except Exception as e:
            err_parts.append(f"html:{type(e).__name__}:{e}")

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
        ok = True
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
        ok = False

    conn.commit()

    return {
        "itemId": item_id,
        "ok": ok,
        "doi": doi2,
        "source": source,
        "abstractLen": len(abstract) if abstract else 0,
        "error": error,
        "durationMs": int((time.time() - started) * 1000),
        "title": title,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["stats", "abstract"], default="stats")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--sleep", type=float, default=0.0)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    if args.mode == "abstract":
        rows = conn.execute(
            """
            SELECT id, title, link, doi
            FROM items
            WHERE (abstract IS NULL OR abstract='')
              AND (enrich_status IS NULL OR enrich_status IN ('pending','failed'))
            ORDER BY first_seen_at_utc ASC
            LIMIT ?
            """,
            (int(args.limit),),
        ).fetchall()

        results = []
        for (item_id, title, link, doi) in rows:
            res = enrich_one_abstract(conn, int(item_id), title or "", link or "", doi, int(args.timeout))
            results.append(res)
            if args.sleep:
                time.sleep(float(args.sleep))

        out = {"ok": True, "mode": "abstract", "processed": len(rows), "results": results}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # stats mode
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
        "mode": "stats",
        "selected": len(rows),
        "missingTotals": missing,
        "statusCounts": status_counts,
        "sample": sample,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
