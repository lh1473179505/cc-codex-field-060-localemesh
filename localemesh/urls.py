"""URL normalization helpers. Implemented so crawl code can reuse them."""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

DROP = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "ref"}


def normalize(url: str, base: str | None = None) -> str:
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url)
    if base:
        b = urlsplit(base)
        scheme, netloc = b.scheme, b.netloc
    else:
        scheme, netloc = parts.scheme, parts.netloc
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in DROP]
    query = urlencode(q, doseq=True)
    path = parts.path or "/"
    return urlunsplit((scheme, netloc, path, query, ""))
