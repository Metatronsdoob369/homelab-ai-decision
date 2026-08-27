#!/usr/bin/env python3
"""Pull PCSP (or any page with Product JSON-LD) into the sheet's upload shape.

Usage:
  python3 fetch_listing.py 'https://pcserverandparts.com/your-listing/'
  python3 fetch_listing.py URL URL > ~/Downloads/servers.json
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (compatible; homelab-ai-decision/1.0)"


def product(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    for blob in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    ):
        data = json.loads(blob)
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        for item in graph:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers") or {}
            return {
                "title": item.get("name") or "",
                "price": float(offers.get("price") or 0),
                "url": offers.get("url") or url,
            }
    raise SystemExit(f"no Product JSON-LD in {url}")


def main() -> None:
    urls = [u.strip() for u in sys.argv[1:] if u.strip()]
    if not urls:
        print(
            "usage: python3 fetch_listing.py URL [URL...] > servers.json",
            file=sys.stderr,
        )
        sys.exit(2)
    print(json.dumps([product(u) for u in urls], indent=2))


if __name__ == "__main__":
    main()
