#!/usr/bin/env python3
"""Enrich RSS items with DOI + abstract (best-effort), without Selenium.

Why: some publisher sites are blocked by Cloudflare (403). For those, we try:
- Extract DOI from URL (common patterns)
- Fetch Crossref metadata to get JATS abstract (often available for SSA/SEG)

Also attempts simple abstract extraction from HTML when allowed.

Input: --input /path/to/rss.json (from rss_watcher.py or snapshot)
Output: JSON {runAt, itemCount, items:[{feedTitle,title,link,doi,abstract,abstractSource,errors[]}], errors:[]}
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request


def http_get(url: str, timeout: int = 25, accept: str | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw rss_enrich)",
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
    # Common DOI-in-path patterns
    pats = [
        r"/doi/(10\.[0-9]{4,9}/[^/?#]+)",
        r"doi\.(?:org|doi:)/(10\.[0-9]{4,9}/[^\s?#]+)",
        r"(10\.[0-9]{4,9}/[^\s?#]+)",
    ]
    for p in pats:
        m = re.search(p, link)
        if m:
            doi = m.group(1)
            doi = doi.rstrip(").,;]")
            return doi
    return None


def crossref_lookup(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='') }"
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
    # Strip JATS-ish tags
    abs_txt = strip_tags(abs_jats)
    # remove leading 'Abstract' label if present
    abs_txt = re.sub(r"^Abstract\s*", "", abs_txt, flags=re.I)
    return abs_txt if len(abs_txt) > 80 else None


def extract_abstract_from_html(html: str) -> str | None:
    # meta tags
    meta_patterns = [
        r'<meta[^>]+name="citation_abstract"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
    ]
    for pat in meta_patterns:
        m = re.search(pat, html, flags=re.I)
        if m:
            txt = strip_tags(m.group(1))
            if len(txt) > 80:
                return txt

    # try "Abstract" section
    m = re.search(r"<h[1-6][^>]*>\s*Abstract\s*</h[1-6]>", html, flags=re.I)
    if m:
        tail = html[m.end() : m.end() + 8000]
        txt = strip_tags(tail)
        if len(txt) > 120:
            return txt[:2500]

    # ScienceDirect sometimes exposes 'Highlights' only on abs page
    m = re.search(r"Highlights\s*[•\-]", strip_tags(html), flags=re.I)
    if m:
        # too messy; skip
        return None

    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--max", type=int, default=1000)
    args = ap.parse_args()

    src = json.load(open(args.input, "r", encoding="utf-8"))
    items = (src.get("newItems") or [])[: args.max]

    out_items = []
    for it in items:
        link = (it.get("link") or "").strip()
        doi = extract_doi(link) if link else None

        abstract = None
        source = None
        errs = []

        # 1) try direct HTML (may be blocked)
        if link:
            try:
                html = http_get(link)
                abstract = extract_abstract_from_html(html)
                if abstract:
                    source = "html"
            except Exception as e:
                errs.append(f"html:{type(e).__name__}:{e}")

        # 2) Crossref DOI abstract (works even when site blocked)
        if not abstract and doi:
            try:
                abstract = crossref_abstract(doi)
                if abstract:
                    source = "crossref"
            except Exception as e:
                errs.append(f"crossref:{type(e).__name__}:{e}")

        out_items.append(
            {
                "feedTitle": it.get("feedTitle"),
                "title": it.get("title"),
                "link": link,
                "doi": doi,
                "abstract": abstract,
                "abstractSource": source,
                "errors": errs,
            }
        )

    out = {
        "runAt": src.get("runAt"),
        "itemCount": len(out_items),
        "items": out_items,
        "errors": src.get("errors") or [],
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
