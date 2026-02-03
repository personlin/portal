#!/usr/bin/env python3
"""Build morning digest texts for Telegram (concise) and Email (richer).

Runs existing local scripts and composes zh-TW output.
Prints JSON:
{
  runAt, dateTaipei,
  telegram: {text},
  email: {to, from, subject, text}
}

No external deps.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(BASE_DIR)

RSS_WATCHER = os.path.join(BASE_DIR, "rss_watcher.py")
RSS_ENRICH = os.path.join(BASE_DIR, "rss_enrich.py")
RSS_TO_GIST = os.path.join(BASE_DIR, "rss_to_gist.py")
EQ_DIGEST = os.path.join(BASE_DIR, "earthquake_digest.py")
RWEEKLY = os.path.join(BASE_DIR, "rweekly_watcher.py")
CRYPTO = os.path.join(WORKSPACE, "crypto", "crypto_watcher.py")

EMAIL_FROM = "p0937087703@gmail.com"
EMAIL_TO = "personlin@gmail.com"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def run_json(cmd: list[str]) -> dict:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def redact_codes(s: str) -> str:
    # redact sequences of 4+ digits (OTP etc.)
    return re.sub(r"\d{4,}", "[REDACTED]", s)


def summarize_rweekly(items: list[dict], limit: int) -> list[dict]:
    out = []
    for it in items[:limit]:
        title = (it.get("title") or "(no title)").strip()
        link = (it.get("link") or "").strip()
        summ = (it.get("summary") or "").strip()
        summ = redact_codes(summ)
        if len(summ) > 200:
            summ = summ[:199] + "…"
        out.append({"title": title, "link": link, "summary": summ})
    return out


def fmt_crypto(crypto_json: dict) -> tuple[str, str]:
    # returns (short, long)
    items = crypto_json.get("items") or []
    lines_short = []
    lines_long = []
    for it in items:
        sym = it.get("symbol")
        price = it.get("price")
        p1 = it.get("pct_1h")
        p24 = it.get("pct_24h")
        def pct(p):
            if p is None:
                return "—"
            arrow = "▲" if p > 0 else ("▼" if p < 0 else "■")
            return f"{arrow}{p:+.1f}%"
        def pr(p):
            if p is None:
                return "—"
            if p >= 1000:
                return f"${p:,.0f}"
            if p >= 1:
                return f"${p:,.2f}"
            return f"${p:.6f}"
        lines_short.append(f"- {sym}: {pr(price)} (1h {pct(p1)}, 24h {pct(p24)})")
        lines_long.append(f"- {sym}\t價格 {pr(price)}\t1h {pct(p1)}\t24h {pct(p24)}")
    return "\n".join(lines_short), "\n".join(lines_long)


def fmt_eq(eq_json: dict, limit: int) -> str:
    items = eq_json.get("items") or []
    if not items:
        return "今日無重大地震（USGS significant_day）"
    lines = []
    for it in items[:limit]:
        mag = it.get("mag")
        place = it.get("place")
        tpe = it.get("timeTaipei")
        link = it.get("link")
        m = f"M{mag:.1f}" if isinstance(mag, (int, float)) else "M?"
        lines.append(f"- {m} {place}（{tpe}）\n  {link}")
    if len(items) > limit:
        lines.append(f"- …其餘 {len(items)-limit} 則略")
    return "\n".join(lines)


def main() -> int:
    date_tpe = taipei_date()

    # 1) GeoSci RSS -> gist
    rss_json_path = "/tmp/rss.json"
    rss_enriched_path = "/tmp/rss_enriched.json"

    rss = run_json(["python3", RSS_WATCHER])
    with open(rss_json_path, "w", encoding="utf-8") as f:
        json.dump(rss, f, ensure_ascii=False)

    # Enrich (best-effort)
    enr = run_json(["python3", RSS_ENRICH, "--input", rss_json_path])
    with open(rss_enriched_path, "w", encoding="utf-8") as f:
        json.dump(enr, f, ensure_ascii=False)

    gist = run_json(["python3", RSS_TO_GIST, "--input", rss_enriched_path, "--max", "12"])
    gist_url = gist.get("url")
    rss_count = gist.get("itemCount")

    # 2) Crypto
    crypto = run_json(["python3", CRYPTO, "--mode", "summary"])
    crypto_short, crypto_long = fmt_crypto(crypto)

    # 3) Earthquake
    eq = run_json(["python3", EQ_DIGEST])

    # 4) RWeekly
    rw = run_json(["python3", RWEEKLY])
    rw_new = int(rw.get("newCount") or 0)
    rw_items = rw.get("newItems") or []

    # Telegram (concise)
    t_lines = [
        f"早安彙整（{date_tpe}）",
        "",
        f"期刊 RSS：{rss_count or 0} 則\n{gist_url}",
        "",
        "加密貨幣（簡）",
        crypto_short or "- （無資料）",
        "",
        "地震（USGS 重大，近 24h）",
        fmt_eq(eq, limit=3),
    ]
    if rw_new == 0:
        t_lines += ["", "RWeekly：今日無更新"]
    else:
        t_lines += ["", f"RWeekly：{rw_new} 則更新", "（詳見 Email）"]

    telegram_text = "\n".join([l for l in t_lines if l is not None])

    # Email (richer)
    e_lines = [
        f"早安彙整（{date_tpe}）",
        f"產生時間(UTC)：{utc_now_iso()}",
        "",
        "[1] 期刊 RSS（GeoSci）",
        f"- 今日新增：{rss_count or 0} 則",
        f"- 完整內容（Secret Gist）：{gist_url}",
        "",
        "[2] 加密貨幣（較完整）",
        crypto_long or "（無資料）",
        "",
        "[3] 地震（USGS Significant past day）",
        fmt_eq(eq, limit=10),
        "",
        "[4] RWeekly（R 語言）",
    ]
    if rw_new == 0:
        e_lines.append("今日無更新")
    else:
        e_lines.append(f"今日新增 {rw_new} 則（列出前 10 則）")
        for it in summarize_rweekly(rw_items, limit=10):
            e_lines.append(f"- {it['title']}\n  {it['link']}")
            if it.get("summary"):
                e_lines.append(f"  摘要：{it['summary']}")

    email_text = "\n".join(e_lines)

    out = {
        "runAt": utc_now_iso(),
        "dateTaipei": date_tpe,
        "telegram": {"text": telegram_text},
        "email": {
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": f"早安彙整 {date_tpe}",
            "text": email_text,
        },
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
