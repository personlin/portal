#!/usr/bin/env python3
"""Extract abstracts/descriptions for RSS items.

Input: --input rss.json (from rss_watcher.py or snapshot)
Output: JSON with items + extracted abstract text (best-effort).

This does NOT use an LLM; it only scrapes.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request


def http_get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw abstract extractor)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read()
    return raw.decode(charset, errors="ignore")


def strip_tags(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html


def extract_meta(html: str) -> str | None:
    meta_patterns = [
        r'<meta[^>]+name="citation_abstract"[^>]+content="([^"]+)"',
        r"<meta[^>]+name='citation_abstract'[^>]+content='([^']+)'",
        r'<meta[^>]+name="dc.Description"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="DC.Description"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="dc.description"[^>]+content="([^"]+)"',
    ]
    for pat in meta_patterns:
        m = re.search(pat, html, flags=re.I)
        if m:
            txt = strip_tags(m.group(1))
            if len(txt) > 80:
                return txt
    return None


def extract_jsonld(html: str) -> str | None:
    for m in re.finditer(r"<script[^>]+type=\"application/ld\+json\"[^>]*>([\s\S]*?)</script>", html, flags=re.I):
        blob = m.group(1).strip()
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except Exception:
            continue

        def walk(o):
            if isinstance(o, dict):
                desc = o.get("description")
                if isinstance(desc, str) and len(desc.strip()) > 80:
                    return desc.strip()
                for v in o.values():
                    r = walk(v)
                    if r:
                        return r
            if isinstance(o, list):
                for v in o:
                    r = walk(v)
                    if r:
                        return r
            return None

        d = walk(data)
        if d:
            return strip_tags(d)
    return None


def extract_section(html: str) -> str | None:
    # Look for visible "Abstract" sections in HTML.
    # Try common class/id patterns.
    candidates = [
        r"<section[^>]+(?:id|class)=\"[^\"]*abstract[^\"]*\"[^>]*>([\s\S]*?)</section>",
        r"<div[^>]+(?:id|class)=\"[^\"]*abstract[^\"]*\"[^>]*>([\s\S]*?)</div>",
        r"<div[^>]+class=\"abstract[^\"]*\"[^>]*>([\s\S]*?)</div>",
    ]
    for pat in candidates:
        m = re.search(pat, html, flags=re.I)
        if m:
            txt = strip_tags(m.group(1))
            if len(txt) > 80:
                return txt

    # Fallback: find heading 'Abstract' then take next ~1500 chars of text
    m = re.search(r"<h[1-6][^>]*>\s*Abstract\s*</h[1-6]>", html, flags=re.I)
    if m:
        tail = html[m.end() : m.end() + 5000]
        txt = strip_tags(tail)
        if len(txt) > 80:
            return txt[:2000]

    return None


def extract_abstract(html: str) -> str | None:
    return extract_meta(html) or extract_jsonld(html) or extract_section(html)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--max", type=int, default=50)
    args = ap.parse_args()

    data = json.load(open(args.input, "r", encoding="utf-8"))
    items = data.get("newItems") or []

    out_items = []
    for it in items[: args.max]:
        link = (it.get("link") or "").strip()
        abstract = None
        err = None
        if link:
            try:
                html = http_get(link)
                abstract = extract_abstract(html)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
        out_items.append({
            **it,
            "abstract": abstract,
            "abstractError": err,
        })

    out = {
        "runAt": data.get("runAt"),
        "feedCount": data.get("feedCount"),
        "newCount": data.get("newCount"),
        "items": out_items,
        "errors": data.get("errors") or [],
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
