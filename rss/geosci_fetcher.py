#!/usr/bin/env python3
"""GeoSci RSS Fetcher (Step 3D): fetch + log per-feed, parse items, store in SQLite.

- Selects feeds using the same ordering as geosci_select_feeds.py.
- Fetches up to N feeds (default 1 for Step 3C).
- Stores per-run + per-feed logs in SQLite.
- Updates feeds metadata (etag/last_modified/last_success_at_utc/etc.).

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

USER_AGENT = "OpenClaw GeoSci Fetcher/1.0"
DELIVERY_CHANNEL = "geosci"
DELIVERY_TARGET = "morning_digest"


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def normalize_id(feed_url: str, entry: dict) -> str:
    # Prefer explicit ids
    for k in ("id", "guid", "link"):
        v = entry.get(k)
        if v:
            return sha1(f"{feed_url}|{k}|{v}")
    # Fallback: title+published
    title = entry.get("title") or ""
    published = entry.get("published") or ""
    return sha1(f"{feed_url}|fallback|{title}|{published}")


def parse_feed(feed_url: str, data: bytes) -> tuple[str | None, list[dict]]:
    """Parse RSS 2.0 or Atom into (feed_title, items)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None, []

    def strip_ns(tag: str) -> str:
        return tag.split("}")[-1] if "}" in tag else tag

    def text(el: ET.Element | None) -> str | None:
        if el is None:
            return None
        t = (el.text or "").strip()
        return t or None

    def find_first(el: ET.Element, names: list[str]) -> ET.Element | None:
        for n in names:
            r = el.find(n)
            if r is not None:
                return r
        return None

    root_tag = strip_ns(root.tag).lower()

    items: list[dict] = []
    feed_title: str | None = None

    if root_tag == "rss":
        channel = next((c for c in list(root) if strip_ns(c.tag).lower() == "channel"), None)
        if channel is None:
            return None, []
        feed_title = text(find_first(channel, ["title"]))
        for item in channel.findall("item"):
            title = text(find_first(item, ["title"]))
            link = text(find_first(item, ["link"]))
            guid = text(find_first(item, ["guid"]))
            pub = text(find_first(item, ["pubDate"]))
            items.append({"title": title, "link": link, "guid": guid, "published": pub})

    elif root_tag == "feed":
        feed_title = text(find_first(root, ["title"]))
        for child in list(root):
            if strip_ns(child.tag).lower() != "entry":
                continue
            title = None
            link = None
            entry_id = None
            published = None
            updated = None
            for sub in list(child):
                st = strip_ns(sub.tag).lower()
                if st == "title":
                    title = (sub.text or "").strip() or None
                elif st == "id":
                    entry_id = (sub.text or "").strip() or None
                elif st == "published":
                    published = (sub.text or "").strip() or None
                elif st == "updated":
                    updated = (sub.text or "").strip() or None
                elif st == "link":
                    href = sub.attrib.get("href")
                    rel = (sub.attrib.get("rel") or "alternate").lower()
                    if href and (link is None or rel == "alternate"):
                        link = href
            items.append({"title": title, "link": link, "id": entry_id, "published": published or updated, "updated": updated})

    else:
        # generic fallback
        for item in root.findall(".//item"):
            title = text(find_first(item, ["title"]))
            link = text(find_first(item, ["link"]))
            guid = text(find_first(item, ["guid"]))
            pub = text(find_first(item, ["pubDate"]))
            items.append({"title": title, "link": link, "guid": guid, "published": pub})

    cleaned = []
    for it in items:
        if not (it.get("title") or it.get("link")):
            continue
        cleaned.append(it)

    return feed_title, cleaned


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def select_feeds(conn, limit: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
          id, url, enabled, priority,
          etag, last_modified,
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
        LIMIT ?
        """,
        (utc_now_iso(), int(limit)),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_url(url: str, *, etag: str | None, last_modified: str | None, timeout: int = 25) -> tuple[int, bytes, dict]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            data = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return int(status), data, resp_headers
    except urllib.error.HTTPError as e:
        # HTTPError is also a valid response; read body if present
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            body = b""
        hdrs = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        return int(e.code), body, hdrs


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1, help="Max feeds to fetch (Step 3C default 1)")
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--kind", default="geosci")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    run_id = rss_store.create_run(conn, kind=str(args.kind))
    run_started = utc_now_iso()

    feeds = select_feeds(conn, int(args.limit))

    results = []
    success = 0
    errors = 0
    inserted_total = 0

    for f in feeds:
        feed_id = int(f["id"])
        url = f["url"]
        started = utc_now_iso()
        t0 = time.time()

        status = None
        bytes_n = None
        ok = None
        err = None
        new_items_count = 0
        inserted_new = 0

        data = b""
        hdrs = {}

        try:
            status, data, hdrs = fetch_url(url, etag=f.get("etag"), last_modified=f.get("last_modified"), timeout=int(args.timeout))
            bytes_n = len(data)
            ok = 1 if (200 <= int(status) < 400 or int(status) == 304) else 0

            if ok and int(status) != 304 and data:
                feed_title, items = parse_feed(url, data)
                for it in items:
                    entry = {
                        "feedUrl": url,
                        "feedTitle": feed_title,
                        "title": it.get("title"),
                        "link": it.get("link"),
                        "guid": it.get("guid"),
                        "id": it.get("id"),
                        "published": it.get("published"),
                        "updated": it.get("updated"),
                    }
                    dedup = normalize_id(url, entry)
                    item_id, inserted = rss_store.upsert_item(conn, feed_id=feed_id, dedup_hash=dedup, entry=entry)
                    if inserted:
                        inserted_new += 1
                        inserted_total += 1
                        rss_store.ensure_delivery(conn, item_id=item_id, channel=DELIVERY_CHANNEL, target=DELIVERY_TARGET, batch_id=None)

                new_items_count = inserted_new

            # Update feed metadata (success)
            now = utc_now_iso()
            if ok:
                # schedule next fetch ~6h later (scheduler also runs every 6h)
                next_fetch = datetime.now(timezone.utc).replace(microsecond=0)
                next_fetch_iso = (next_fetch + timedelta(hours=6)).isoformat().replace("+00:00", "Z")

                conn.execute(
                    """
                    UPDATE feeds
                    SET last_fetch_at_utc=?, last_success_at_utc=?, last_error=NULL,
                        consecutive_failures=0,
                        priority=CASE WHEN priority>0 THEN priority-1 ELSE 0 END,
                        next_fetch_after_utc=?,
                        etag=COALESCE(?, etag),
                        last_modified=COALESCE(?, last_modified),
                        updated_at_utc=?
                    WHERE id=?
                    """,
                    (
                        now,
                        now,
                        next_fetch_iso,
                        hdrs.get("etag"),
                        hdrs.get("last-modified"),
                        now,
                        feed_id,
                    ),
                )
                success += 1
            else:
                raise RuntimeError(f"HTTP {status}")

        except Exception as e:
            ok = 0
            errors += 1
            err = f"{type(e).__name__}: {e}"
            now = utc_now_iso()

            # Failure: prioritize next time.
            # - next_fetch_after_utc set to now so selector ranks it earlier
            # - priority bump (capped) so repeated failures stay on top
            conn.execute(
                """
                UPDATE feeds
                SET last_fetch_at_utc=?, last_error=?,
                    consecutive_failures=consecutive_failures+1,
                    next_fetch_after_utc=?,
                    priority=MIN(priority+1, 50),
                    updated_at_utc=?
                WHERE id=?
                """,
                (now, err, now, now, feed_id),
            )

        finished = utc_now_iso()

        rss_store.log_feed_fetch(
            conn,
            run_id=run_id,
            feed_id=feed_id,
            started_at_utc=started,
            finished_at_utc=finished,
            ok=bool(ok),
            http_status=int(status) if status is not None else None,
            bytes_n=int(bytes_n) if bytes_n is not None else None,
            new_items_count=int(new_items_count),
            error=err,
        )

        results.append(
            {
                "feedId": feed_id,
                "url": url,
                "ok": bool(ok),
                "httpStatus": status,
                "bytes": bytes_n,
                "insertedNew": inserted_new,
                "durationMs": int((time.time() - t0) * 1000),
                "error": err,
            }
        )

    rss_store.finish_run(
        conn,
        run_id,
        ok=(errors == 0),
        feed_count=len(feeds),
        success_count=success,
        error_count=errors,
        notes="step3d:parse+store",
    )

    out = {
        "ok": errors == 0,
        "runId": run_id,
        "runStartedAtUtc": run_started,
        "kind": str(args.kind),
        "limit": int(args.limit),
        "insertedTotal": int(inserted_total),
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
