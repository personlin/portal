#!/usr/bin/env python3
"""Create a secret GitHub Gist from today's RSS digest.

- Runs rss_watcher.py output JSON (pass path via --input)
- For each item, attempts to fetch abstract/summary from the article page
- Writes a secret gist using a token stored in ~/.openclaw/credentials/github-gist-token.txt
- Prints JSON to stdout: { ok, url, id, fileName, itemCount, shownCount }

Notes:
- Best-effort extraction; many publishers are paywalled or vary markup.
- Keeps content size reasonable (Telegram has limits; gist can be long but still bounded).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN_PATH = os.path.expanduser("~/.openclaw/credentials/github-gist-token.txt")


def read_token() -> str:
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def http_get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (OpenClaw RSS Digest)",
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


def extract_abstract(html: str) -> str | None:
    # Common meta tags
    meta_patterns = [
        r'<meta[^>]+name="citation_abstract"[^>]+content="([^"]+)"',
        r"<meta[^>]+name='citation_abstract'[^>]+content='([^']+)'",
        r'<meta[^>]+name="dc.Description"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
    ]
    for pat in meta_patterns:
        m = re.search(pat, html, flags=re.I)
        if m:
            return strip_tags(m.group(1))

    # JSON-LD blocks often include description
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
                if isinstance(o.get("description"), str) and len(o["description"].strip()) > 50:
                    return o["description"].strip()
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

        desc = walk(data)
        if desc:
            return strip_tags(desc)

    return None


def summarize_from_abstract(abs_text: str, max_chars: int = 500) -> str:
    # Lightweight summary: keep first ~2-3 sentences, bounded.
    s = re.sub(r"\s+", " ", abs_text).strip()
    # Split on sentence-ish boundaries
    parts = re.split(r"(?<=[。！？.!?])\s+", s)
    out = " ".join(parts[:3]).strip() if parts else s
    if len(out) > max_chars:
        out = out[: max_chars - 1] + "…"
    return out


def to_tpe_date(run_at_iso: str | None) -> str:
    tz = ZoneInfo("Asia/Taipei")
    if not run_at_iso:
        return datetime.now(tz).date().isoformat()
    dt = datetime.fromisoformat(run_at_iso.replace("Z", "+00:00")).astimezone(tz)
    return dt.date().isoformat()


def create_gist(markdown: str, filename: str, description: str) -> dict:
    token = read_token()
    payload = {
        "description": description,
        "public": False,
        "files": {filename: {"content": markdown}},
    }
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "OpenClaw RSS Digest",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    return json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to rss_watcher.py JSON output")
    ap.add_argument("--max", type=int, default=10, help="Max items to include with abstracts")
    args = ap.parse_args()

    data = json.load(open(args.input, "r", encoding="utf-8"))
    run_at = data.get("runAt")
    new_items = data.get("newItems") or []
    errors = data.get("errors") or []

    date_tpe = to_tpe_date(run_at)
    title = f"GeoSci Journals RSS Digest — {date_tpe}"

    md_lines = []
    md_lines.append(f"# {title}")
    md_lines.append("")
    md_lines.append(f"RunAt (UTC): {run_at}")
    md_lines.append("")

    if errors:
        md_lines.append("## Errors")
        for e in errors:
            md_lines.append(f"- {e.get('feedUrl')}: {e.get('error')}")
        md_lines.append("")

    if not new_items:
        md_lines.append("## 今日無更新")
        md_lines.append("")
    else:
        md_lines.append(f"## New items ({len(new_items)})")
        md_lines.append("")

        shown = 0
        for it in new_items:
            if shown >= args.max:
                break
            feed = (it.get("feedTitle") or it.get("feedUrl") or "(unknown feed)").strip()
            title_full = (it.get("title") or "(no title)").strip()
            link = (it.get("link") or "").strip()

            md_lines.append(f"### {title_full}")
            md_lines.append("")
            md_lines.append(f"- Journal: {feed}")
            if link:
                md_lines.append(f"- Link: {link}")

            abstract = None
            if link:
                try:
                    html = http_get(link)
                    abstract = extract_abstract(html)
                except Exception:
                    abstract = None

            if abstract:
                md_lines.append("")
                md_lines.append("**Abstract (extracted)**")
                md_lines.append("")
                md_lines.append(textwrap.fill(abstract, width=100))
                md_lines.append("")
                md_lines.append("**摘要（由 abstract 產生）**")
                md_lines.append("")
                md_lines.append(textwrap.fill(summarize_from_abstract(abstract), width=100))
            else:
                md_lines.append("")
                md_lines.append("**Abstract:** (not found / blocked)")

            md_lines.append("")
            shown += 1

        if len(new_items) > shown:
            md_lines.append(f"\n---\n\nOnly first {shown} items included with abstracts. Remaining: {len(new_items) - shown}.")

    md = "\n".join(md_lines).strip() + "\n"

    filename = f"geosci-rss-{date_tpe}.md"
    gist = create_gist(md, filename, title)

    out = {
        "ok": True,
        "url": gist.get("html_url"),
        "id": gist.get("id"),
        "fileName": filename,
        "itemCount": len(new_items),
        "shownCount": min(len(new_items), args.max),
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
