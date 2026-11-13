from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin


def parse_sitemap(xml_text: str, base: str | None = None) -> list[dict]:
    root = ET.fromstring(xml_text)
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"
    items = []
    for url_el in root.findall(f"{ns}url"):
        loc_el = url_el.find(f"{ns}loc")
        lastmod_el = url_el.find(f"{ns}lastmod")
        if loc_el is None or not (loc_el.text or "").strip():
            continue
        loc = loc_el.text.strip()
        if base:
            loc = urljoin(base, loc)
        items.append({
            "loc": loc,
            "lastmod": (lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None),
        })
    return items
