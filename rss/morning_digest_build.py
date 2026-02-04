#!/usr/bin/env python3
"""Build morning digest texts for Telegram (concise) and Email (richer).

Runs existing local scripts and composes zh-TW output.
Prints JSON:
{
  runAt, dateTaipei,
  telegram: {text},
  email: {to, from, subject, text, html}
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
TECH_RPI = os.path.join(BASE_DIR, "technews_rpi_watcher.py")
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


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def linkify(url: str) -> str:
    u = html_escape(url)
    return f'<a href="{u}" style="color:#2563eb; text-decoration:none;">{u}</a>'


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

    # 4) Tech news (Raspberry Pi) — daily
    rpi = run_json(["python3", TECH_RPI])
    rpi_new = int(rpi.get("newCount") or 0)
    rpi_items = rpi.get("newItems") or []

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
    if rpi_new == 0:
        t_lines += ["", "科技新聞（Raspberry Pi）：今日無更新"]
    else:
        # keep Telegram short
        top = rpi_items[0] if rpi_items else {}
        t_lines += ["", f"科技新聞（Raspberry Pi）：{rpi_new} 則更新", f"- {top.get('title','(no title)')}\n  {top.get('link','')}" ]

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
        "[4] 科技新聞（Raspberry Pi）",
    ]
    if rpi_new == 0:
        e_lines.append("今日無更新")
    else:
        e_lines.append(f"今日新增 {rpi_new} 則（列出前 10 則）")
        for it in summarize_rweekly(rpi_items, limit=10):
            e_lines.append(f"- {it['title']}\n  {it['link']}")
            if it.get("summary"):
                e_lines.append(f"  摘要：{it['summary']}")

    email_text = "\n".join(e_lines)

    # Email HTML (styled)
    rss_count_s = str(rss_count or 0)
    gist_url_s = str(gist_url or "")

    # Build HTML blocks
    crypto_rows = []
    for it in (crypto.get("items") or []):
        sym = html_escape(str(it.get("symbol") or ""))
        price = it.get("price")
        p1 = it.get("pct_1h")
        p24 = it.get("pct_24h")

        def pct_badge(p):
            if p is None:
                return '<span style="color:#6b7280;">—</span>'
            color = "#16a34a" if p > 0 else ("#dc2626" if p < 0 else "#6b7280")
            sign = "+" if p > 0 else ""
            return f'<span style="color:{color}; font-weight:700;">{sign}{p:.1f}%</span>'

        def pr(p):
            if p is None:
                return "—"
            if p >= 1000:
                return f"${p:,.0f}"
            if p >= 1:
                return f"${p:,.2f}"
            return f"${p:.6f}"

        crypto_rows.append(
            f"<tr>"
            f"<td style='padding:8px 10px; border-bottom:1px solid #e5e7eb; font-weight:700;'>{sym}</td>"
            f"<td style='padding:8px 10px; border-bottom:1px solid #e5e7eb; text-align:right;'>{html_escape(pr(price))}</td>"
            f"<td style='padding:8px 10px; border-bottom:1px solid #e5e7eb; text-align:right;'>{pct_badge(p1)}</td>"
            f"<td style='padding:8px 10px; border-bottom:1px solid #e5e7eb; text-align:right;'>{pct_badge(p24)}</td>"
            f"</tr>"
        )

    eq_items = eq.get("items") or []
    if not eq_items:
        eq_html = "<div style='color:#6b7280;'>今日無重大地震（USGS significant_day）</div>"
    else:
        lis = []
        for it in eq_items[:10]:
            mag = it.get("mag")
            place = html_escape(str(it.get("place") or ""))
            tpe = html_escape(str(it.get("timeTaipei") or ""))
            link = str(it.get("link") or "")
            m = f"M{mag:.1f}" if isinstance(mag, (int, float)) else "M?"
            lis.append(
                f"<li style='margin:0 0 10px 0;'>"
                f"<div style='font-weight:700;'>{html_escape(m)} {place}</div>"
                f"<div style='color:#6b7280; font-size:12px;'>{tpe}</div>"
                f"<div style='margin-top:3px;'>{linkify(link) if link else ''}</div>"
                f"</li>"
            )
        eq_html = "<ul style='padding-left:18px; margin:10px 0 0 0;'>" + "".join(lis) + "</ul>"

    if rpi_new == 0:
        tech_html = "<div style='color:#6b7280;'>今日無更新</div>"
    else:
        lis = []
        for it in summarize_rweekly(rpi_items, limit=10):
            title = html_escape(it.get("title") or "")
            link = str(it.get("link") or "")
            summ = html_escape(it.get("summary") or "")
            lis.append(
                f"<li style='margin:0 0 12px 0;'>"
                f"<div style='font-weight:700;'>{title}</div>"
                f"<div style='margin-top:3px;'>{linkify(link) if link else ''}</div>"
                + (f"<div style='margin-top:4px; color:#374151;'>{summ}</div>" if summ else "")
                + "</li>"
            )
        tech_html = (
            f"<div style='color:#111827; margin-top:6px;'>今日新增 <b>{rpi_new}</b> 則（列出前 10 則）</div>"
            + "<ul style='padding-left:18px; margin:10px 0 0 0;'>"
            + "".join(lis)
            + "</ul>"
        )

    email_html = f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>早安彙整 {html_escape(date_tpe)}</title>
</head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans TC','PingFang TC','Microsoft JhengHei',Arial,sans-serif;">
  <div style="max-width:760px; margin:0 auto; padding:18px;">
    <div style="background:#111827; color:#fff; padding:18px 18px; border-radius:12px;">
      <div style="font-size:22px; font-weight:800;">早安彙整</div>
      <div style="font-size:14px; opacity:.9; margin-top:4px;">{html_escape(date_tpe)}（Asia/Taipei）</div>
    </div>

    <div style="background:#fff; padding:16px 18px; border-radius:12px; margin-top:12px; border:1px solid #e5e7eb;">
      <div style="font-size:16px; font-weight:800; color:#111827;">[1] 期刊 RSS（GeoSci）</div>
      <div style="margin-top:8px; color:#111827;">今日新增：<b>{html_escape(rss_count_s)}</b> 則</div>
      <div style="margin-top:6px;">完整內容（Secret Gist）：{linkify(gist_url_s) if gist_url_s else ''}</div>
    </div>

    <div style="background:#fff; padding:16px 18px; border-radius:12px; margin-top:12px; border:1px solid #e5e7eb;">
      <div style="font-size:16px; font-weight:800; color:#111827;">[2] 加密貨幣</div>
      <div style="margin-top:10px; overflow-x:auto;">
        <table style="border-collapse:collapse; width:100%; min-width:520px;">
          <thead>
            <tr>
              <th style="text-align:left; padding:8px 10px; border-bottom:2px solid #e5e7eb; color:#374151; font-size:12px;">幣別</th>
              <th style="text-align:right; padding:8px 10px; border-bottom:2px solid #e5e7eb; color:#374151; font-size:12px;">價格</th>
              <th style="text-align:right; padding:8px 10px; border-bottom:2px solid #e5e7eb; color:#374151; font-size:12px;">1h</th>
              <th style="text-align:right; padding:8px 10px; border-bottom:2px solid #e5e7eb; color:#374151; font-size:12px;">24h</th>
            </tr>
          </thead>
          <tbody>
            {''.join(crypto_rows) if crypto_rows else '<tr><td colspan="4" style="padding:10px; color:#6b7280;">（無資料）</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>

    <div style="background:#fff; padding:16px 18px; border-radius:12px; margin-top:12px; border:1px solid #e5e7eb;">
      <div style="font-size:16px; font-weight:800; color:#111827;">[3] 地震（USGS Significant past day）</div>
      {eq_html}
    </div>

    <div style="background:#fff; padding:16px 18px; border-radius:12px; margin-top:12px; border:1px solid #e5e7eb;">
      <div style="font-size:16px; font-weight:800; color:#111827;">[4] 科技新聞（Raspberry Pi）</div>
      {tech_html}
    </div>

    <div style="color:#6b7280; font-size:12px; margin-top:12px; padding:0 6px;">
      產生時間（UTC）：{html_escape(utc_now_iso())}
    </div>
  </div>
</body>
</html>
"""

    out = {
        "runAt": utc_now_iso(),
        "dateTaipei": date_tpe,
        "telegram": {"text": telegram_text},
        "email": {
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": f"早安彙整 {date_tpe}",
            "text": email_text,
            "html": email_html,
        },
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
