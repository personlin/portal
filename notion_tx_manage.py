#!/usr/bin/env python3
"""Manage Taiwan stock transactions stored in Notion.

Supports:
- list last transactions
- add a transaction (with Portfolio/Account relations resolved by name)

Requires Notion Integration token in env:
- NOTION_API_KEY (preferred) or NOTION_TOKEN

Uses Notion API version: 2025-09-03

This script is tailored to Person's Notion databases:
- Transaction database_id: bf592a9c-b7e2-4fa5-85dc-9d17dbd70e23
  data_source_id:         bbbc830b-cea8-4190-8472-ea616e259e41
- Portfolio database_id:  d2b92238-b570-4f21-a938-3a4356ca9236
  data_source_id:         2f52ec51-2d00-487b-8bc6-cc859c63f69c
- Account database_id:    55d5fd9c-a7ee-4332-9e2e-cfb0e07257b0
  data_source_id:         cc493540-10d8-497f-a62b-7d4d1fbcef37

No external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from typing import Any

NOTION_VERSION = "2025-09-03"
API = "https://api.notion.com/v1"

TX_DB_ID = "bf592a9c-b7e2-4fa5-85dc-9d17dbd70e23"
TX_SRC_ID = "bbbc830b-cea8-4190-8472-ea616e259e41"

PORTFOLIO_SRC_ID = "2f52ec51-2d00-487b-8bc6-cc859c63f69c"
ACCOUNT_SRC_ID = "cc493540-10d8-497f-a62b-7d4d1fbcef37"

# Notion property names (as configured in your DB)
PROP_TITLE = "Transaction"
PROP_DATE = "Date"
PROP_PORTFOLIO = "Portfolio"
PROP_SIDE = "Buy/ Sell"  # select: Bought | Sold
PROP_QTY = "Quantity (Unit)"
PROP_UNIT_PRICE = "Unit Price"
PROP_ACCOUNT = "Account"

# Related DB "name" property (title property)
PORTFOLIO_NAME_PROP = "Name"
ACCOUNT_NAME_PROP = "Name"


def notion_key() -> str:
    key = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    if not key:
        raise RuntimeError("missing_notion_key: set NOTION_API_KEY or NOTION_TOKEN")
    return key.strip()


def http_json(method: str, path: str, *, body: dict | None = None, timeout: int = 25) -> dict:
    key = notion_key()
    url = path if path.startswith("http") else API + path
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
        return json.loads(raw) if raw else {}


def plain_title(page: dict, prop: str) -> str:
    p = (page.get("properties") or {}).get(prop) or {}
    # title property in Notion pages
    arr = p.get("title") or []
    return "".join([x.get("plain_text") or "" for x in arr]).strip()


def resolve_relation_by_name(*, src_id: str, name_prop: str, name: str) -> str:
    """Return the related page_id for a relation, by looking up the related DB by title."""
    name = (name or "").strip()
    if not name:
        raise ValueError("empty_relation_name")

    # Try exact match first, then contains.
    for mode in ("equals", "contains"):
        body: dict[str, Any] = {
            "page_size": 5,
            "filter": {
                "property": name_prop,
                "title": {mode: name},
            },
        }
        out = http_json("POST", f"/data_sources/{src_id}/query", body=body)
        results = out.get("results") or []
        if results:
            return str(results[0].get("id"))

    raise LookupError(f"relation_not_found:{name}")


def list_last(limit: int = 10) -> dict:
    body = {
        "page_size": int(limit),
        "sorts": [{"property": PROP_DATE, "direction": "descending"}],
    }
    out = http_json("POST", f"/data_sources/{TX_SRC_ID}/query", body=body)
    items = []
    for p in out.get("results") or []:
        props = p.get("properties") or {}
        side = ((props.get(PROP_SIDE) or {}).get("select") or {}).get("name")
        date = ((props.get(PROP_DATE) or {}).get("date") or {}).get("start")
        qty = (props.get(PROP_QTY) or {}).get("number")
        price = (props.get(PROP_UNIT_PRICE) or {}).get("number")

        items.append(
            {
                "id": p.get("id"),
                "title": plain_title(p, PROP_TITLE),
                "date": date,
                "side": side,
                "qty": qty,
                "unitPrice": price,
                "url": p.get("url"),
            }
        )

    return {"ok": True, "mode": "list", "count": len(items), "items": items}


def add_tx(*,
           title: str | None,
           date: str,
           portfolio_name: str,
           side: str,
           qty: float,
           unit_price: float,
           account_name: str) -> dict:
    side_in = (side or "").strip()
    side_norm = {"buy": "Bought", "bought": "Bought", "sell": "Sold", "sold": "Sold"}.get(side_in.lower())
    if not side_norm:
        raise ValueError("side_must_be_Bought_or_Sold")
    side = side_norm

    # Basic date validation (YYYY-MM-DD)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ValueError("date_must_be_YYYY-MM-DD")

    portfolio_id = resolve_relation_by_name(src_id=PORTFOLIO_SRC_ID, name_prop=PORTFOLIO_NAME_PROP, name=portfolio_name)
    account_id = resolve_relation_by_name(src_id=ACCOUNT_SRC_ID, name_prop=ACCOUNT_NAME_PROP, name=account_name)

    # Auto-title (Transaction title) if omitted
    title = (title or "").strip()
    if not title:
        action = "買入" if side == "Bought" else "賣出"
        title = f"{action} {portfolio_name}"

    body = {
        "parent": {"database_id": TX_DB_ID},
        "properties": {
            PROP_TITLE: {"title": [{"text": {"content": title}}]},
            PROP_DATE: {"date": {"start": date}},
            PROP_SIDE: {"select": {"name": side}},
            PROP_QTY: {"number": float(qty)},
            PROP_UNIT_PRICE: {"number": float(unit_price)},
            PROP_PORTFOLIO: {"relation": [{"id": portfolio_id}]},
            PROP_ACCOUNT: {"relation": [{"id": account_id}]},
        },
    }

    page = http_json("POST", "/pages", body=body)
    return {"ok": True, "mode": "add", "id": page.get("id"), "url": page.get("url")}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=10)

    p_add = sub.add_parser("add")
    p_add.add_argument("--title", default=None, help="Transaction title (omit to auto-generate)")
    p_add.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_add.add_argument("--portfolio", required=True, help="Portfolio Name (relation)")
    p_add.add_argument("--side", required=True, help="Bought|Sold (also accepts Buy|Sell)")
    p_add.add_argument("--qty", required=True, type=float)
    p_add.add_argument("--unit-price", required=True, type=float)
    p_add.add_argument("--account", required=True, help="Account Name (relation)")

    args = ap.parse_args()

    try:
        if args.cmd == "list":
            out = list_last(limit=int(args.limit))
        elif args.cmd == "add":
            out = add_tx(
                title=(str(args.title) if args.title is not None else None),
                date=str(args.date),
                portfolio_name=str(args.portfolio),
                side=str(args.side),
                qty=float(args.qty),
                unit_price=float(args.unit_price),
                account_name=str(args.account),
            )
        else:
            raise RuntimeError("unknown_cmd")
    except Exception as e:
        out = {"ok": False, "error": f"{type(e).__name__}:{e}"}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
