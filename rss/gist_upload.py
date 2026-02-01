#!/usr/bin/env python3
"""Upload a markdown file as a SECRET GitHub Gist.

Usage:
  python3 gist_upload.py --file /path/to/file.md --description "..."

Token is read from ~/.openclaw/credentials/github-gist-token.txt
Prints JSON: {ok,url,id}
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request

TOKEN_PATH = os.path.expanduser("~/.openclaw/credentials/github-gist-token.txt")


def read_token() -> str:
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--name", default=None)
    args = ap.parse_args()

    content = open(args.file, "r", encoding="utf-8").read()
    name = args.name or os.path.basename(args.file)

    payload = {
        "description": args.description,
        "public": False,
        "files": {name: {"content": content}},
    }

    token = read_token()
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "OpenClaw Gist Upload",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    data = json.loads(raw)

    out = {"ok": True, "url": data.get("html_url"), "id": data.get("id")}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
