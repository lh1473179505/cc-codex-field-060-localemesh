"""Extract links, hreflang, canonical, title and product markers from HTML."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hreflang = []  # (lang, href)
        self.canonical = None
        self.links = []
        self.title_parts = []
        self.in_title = False
        self.last_updated = None
        self.has_product_card = False
        self.soft404_flag = False
        self.text_parts = []
        self._capture_text = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): v for k, v in attrs}
        if tag == "title":
            self.in_title = True
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])
        if tag == "link":
            rel = (d.get("rel") or "").lower().split()
            href = d.get("href")
            if href and "alternate" in rel and d.get("hreflang"):
                self.hreflang.append((d["hreflang"], href))
            if href and "canonical" in rel:
                self.canonical = href
        if tag == "meta" and (d.get("name") or "").lower() == "last-updated":
            self.last_updated = d.get("content")
        if tag == "div":
            classes = (d.get("class") or "").split()
            if "product-card" in classes:
                self.has_product_card = True
            if d.get("data-soft404") == "1":
                self.soft404_flag = True
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self._skip == 0:
            self.text_parts.append(data)


def parse_html(html: str) -> dict:
    p = _Parser()
    p.feed(html)
    text = re.sub(r"\s+", " ", "".join(p.text_parts)).strip()
    title = re.sub(r"\s+", " ", "".join(p.title_parts)).strip()
    return {
        "hreflang": p.hreflang,
        "canonical": p.canonical,
        "links": p.links,
        "title": title,
        "last_updated": p.last_updated,
        "has_product_card": p.has_product_card,
        "soft404_flag": p.soft404_flag,
        "text": text,
    }


SOFT_PATTERNS = [
    "is not available in your region",
    "n'est pas disponible dans votre région",
    "n’est pas disponible dans votre région",
]


def looks_like_soft_404_text(text: str) -> bool:
    low = text.lower()
    return any(s.lower() in low for s in SOFT_PATTERNS)
