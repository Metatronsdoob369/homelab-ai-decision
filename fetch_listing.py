#!/usr/bin/env python3
"""Pull a product page into the sheet's {title, price, url} JSON.

Usage:
  python3 fetch_listing.py 'https://pcserverandparts.com/actual-product-slug/'
  python3 fetch_listing.py URL URL > ~/Downloads/servers.json

The URL must be a product page that loads in a browser, not a search page
and not the YOUR-LISTING-HERE placeholder.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", "replace")


def from_jsonld(html: str, url: str) -> dict | None:
    for blob in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    ):
        data = json.loads(blob)
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        for item in graph:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers") or {}
            title = item.get("name") or ""
            if not title:
                continue
            return {
                "title": title,
                "price": float(offers.get("price") or 0),
                "url": offers.get("url") or url,
            }
    return None


def from_jina(url: str) -> dict:
    text = fetch("https://r.jina.ai/" + url)
    title_m = re.search(r"^Title:\s*(.+)$", text, re.M)
    price_m = re.search(r"Now:\s*\$([0-9,]+\.?\d*)", text)
    if not title_m:
        raise SystemExit(f"reader returned no title for {url}")
    return {
        "title": title_m.group(1).strip(),
        "price": float(price_m.group(1).replace(",", "")) if price_m else 0,
        "url": url,
    }


def product(url: str) -> dict:
    if "YOUR-LISTING" in url or "your-listing" in url:
        raise SystemExit(
            "that is the placeholder URL. Paste a real product link from the "
            "browser address bar, the long pcserverandparts.com/dell-poweredge-... one."
        )
    try:
        parsed = from_jsonld(fetch(url), url)
        if parsed:
            return parsed
    except urllib.error.HTTPError as e:
        print(f"direct fetch {e.code} {url} — trying reader", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"direct fetch failed {url}: {e.reason} — trying reader", file=sys.stderr)
    try:
        return from_jina(url)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"HTTP {e.code} for {url}\n"
            "Open that link in a browser. If it 404s there too, it is not a product page.\n"
            "Copy the address bar after the listing loads — full slug, quotes around it."
        ) from None


def main() -> None:
    urls = [u.strip() for u in sys.argv[1:] if u.strip()]
    if not urls:
        print(
            "usage: python3 fetch_listing.py 'https://pcserverandparts.com/dell-poweredge-.../' > ~/Downloads/servers.json",
            file=sys.stderr,
        )
        sys.exit(2)
    print(json.dumps([product(u) for u in urls], indent=2))


if __name__ == "__main__":
    main()
