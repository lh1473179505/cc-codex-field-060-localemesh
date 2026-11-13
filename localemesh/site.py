"""Local multi-locale catalog fixture. All pages are defined here."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse


# Catalog facts. last_updated is the meta date (real content time).
# sitemap_lastmod may differ (see SITEMAP_LASTMOD).
PRODUCTS = {
    "kettle": {
        "en": {"title": "Steel Kettle", "body": "A 1.5L steel kettle for the stovetop.", "last_updated": "2026-01-10"},
        "fr": {"title": "Bouilloire en acier", "body": "Une bouilloire de 1,5 L pour la cuisinière.", "last_updated": "2026-01-10"},
        "de": {"title": "Stahlkessel", "body": "Ein 1,5-Liter-Wasserkessel für den Herd.", "last_updated": "2026-01-10"},
        # ja is not a real page: /ja/p/kettle redirects to en
    },
    "mug": {
        "en": {"title": "Blue Mug", "body": "A 300ml ceramic mug.", "last_updated": "2026-02-01"},
        "fr": {"title": "Tasse bleue", "body": "Une tasse en céramique de 300 ml.", "last_updated": "2026-02-01"},
        "de": {"title": "Blaue Tasse", "body": "Eine Keramiktasse mit 300 ml.", "last_updated": "2026-02-01"},
        "ja": {"title": "青いマグ", "body": "300ml のセラミックマグカップ。", "last_updated": "2026-02-01"},
    },
    "notebook": {
        # short but valid
        "en": {"title": "Notebook", "body": "A5.", "last_updated": "2026-03-01"},
        "fr": {"title": "Carnet", "body": "A5.", "last_updated": "2026-03-01"},
    },
    "ghost": {
        # soft-404 in en/fr (200 + template, no product-card). de is a real leftover page.
        "en": {"soft404": True, "title": "Unavailable", "body": "This product is not available in your region.", "last_updated": None},
        "fr": {"soft404": True, "title": "Indisponible", "body": "Cet article n'est pas disponible dans votre région.", "last_updated": None},
        "de": {"title": "Restposten", "body": "Ein auslaufender Restposten, nur auf Deutsch gelistet.", "last_updated": "2025-11-01"},
    },
    "lamp": {
        "en": {"title": "Desk Lamp", "body": "LED desk lamp with two brightness levels.", "last_updated": "2026-04-01"},
        "fr": {"title": "Lampe de bureau", "body": "Lampe LED avec deux niveaux de luminosité.", "last_updated": "2026-04-01"},
        "de": {"title": "Schreibtischlampe", "body": "LED-Lampe mit zwei Helligkeitsstufen.", "last_updated": "2026-04-01"},
    },
}

# mug EN sitemap lastmod is newer than meta last-updated, content unchanged.
SITEMAP_LASTMOD = {
    ("mug", "en"): "2026-08-01",
    ("mug", "fr"): "2026-02-01",
    ("mug", "de"): "2026-02-01",
    ("mug", "ja"): "2026-02-01",
    ("kettle", "en"): "2026-01-10",
    ("kettle", "fr"): "2026-01-10",
    ("kettle", "de"): "2026-01-10",
    ("notebook", "en"): "2026-03-01",
    ("notebook", "fr"): "2026-03-01",
    ("lamp", "en"): "2026-04-01",
    ("lamp", "fr"): "2026-04-01",
    ("lamp", "de"): "2026-04-01",
    ("ghost", "de"): "2025-11-01",
    # ghost en/fr listed so crawlers discover the soft-404 URLs
    ("ghost", "en"): "2026-01-01",
    ("ghost", "fr"): "2026-01-01",
}

# Intentional hreflang / canonical quirks:
# - kettle: fr/de/en mutually linked; ja is only a 302, should not be a member.
#   canonical on fr and de both point to en; en canonical is self.
# - mug: all four mutually linked; each canonical is self (cluster canonical by x-default / en).
#   en is x-default.
# - notebook: en <-> fr mutual; both canonical to en.
# - ghost: en hreflang points to fr and de, but en/fr are soft-404. de has a one-way hreflang
#   to /en/p/ghost (dangling from de's perspective if en is rejected? actually en is fetched
#   but classified soft-404). de canonical is self. en also points to /es/p/ghost which does
#   not exist (dangling + http 404).
# - lamp: de has a broken one-way hreflang to /en/p/lamp-old (404). en/fr/de otherwise mutual.
#   en and fr canonical point to en; de wrongly canonicals to /de/p/mug (another cluster).
#   votes: en is pointed by en+fr (and de's canonical is invalid because it is not in this cluster).

LOCALES = ["en", "fr", "de", "ja"]
LOCALE_LABEL = {"en": "English", "fr": "Français", "de": "Deutsch", "ja": "日本語"}


def _abs(path: str) -> str:
    return path


def hreflang_tags(slug: str, locale: str) -> list[tuple[str, str]]:
    tags = []
    if slug == "kettle":
        tags = [("en", "/en/p/kettle"), ("fr", "/fr/p/kettle"), ("de", "/de/p/kettle"), ("x-default", "/en/p/kettle")]
        if locale != "ja":
            return tags
        return tags
    if slug == "mug":
        return [
            ("en", "/en/p/mug"),
            ("fr", "/fr/p/mug"),
            ("de", "/de/p/mug"),
            ("ja", "/ja/p/mug"),
            ("x-default", "/en/p/mug"),
        ]
    if slug == "notebook":
        return [("en", "/en/p/notebook"), ("fr", "/fr/p/notebook"), ("x-default", "/en/p/notebook")]
    if slug == "ghost":
        if locale in {"en", "fr"}:
            return [("en", "/en/p/ghost"), ("fr", "/fr/p/ghost"), ("de", "/de/p/ghost"), ("es", "/es/p/ghost")]
        if locale == "de":
            return [("de", "/de/p/ghost"), ("en", "/en/p/ghost")]
    if slug == "lamp":
        tags = [("en", "/en/p/lamp"), ("fr", "/fr/p/lamp"), ("de", "/de/p/lamp"), ("x-default", "/en/p/lamp")]
        if locale == "de":
            tags.append(("en", "/en/p/lamp-old"))  # one-way broken
        return tags
    return tags


def canonical_href(slug: str, locale: str) -> str | None:
    if slug == "kettle":
        return "/en/p/kettle"
    if slug == "mug":
        return f"/{locale}/p/mug"
    if slug == "notebook":
        return "/en/p/notebook"
    if slug == "ghost":
        return f"/{locale}/p/ghost"
    if slug == "lamp":
        if locale == "de":
            return "/de/p/mug"  # wrong cluster
        return "/en/p/lamp"
    return None


def page_html(slug: str, locale: str, product: dict, extra_links: list[str] | None = None) -> str:
    soft = product.get("soft404")
    alts = "".join(
        '<link rel="alternate" hreflang="%s" href="%s">\n' % (lang, href)
        for lang, href in hreflang_tags(slug, locale)
    )
    can = canonical_href(slug, locale)
    can_tag = ('<link rel="canonical" href="%s">\n' % can) if can else ""
    meta = ""
    if product.get("last_updated"):
        meta = '<meta name="last-updated" content="%s">\n' % product["last_updated"]
    links = extra_links or []
    # cycles: every product links to locale index, home, and a couple of siblings
    links += ["/", f"/{locale}/", f"/{locale}/p/{slug}?utm_source=footer&ref=cycle"]
    a_tags = "".join(f'<a href="{h}">link</a> ' for h in links)
    if soft:
        body = f'<p>{product["body"]}</p><div data-soft404="1" hidden>soft-404</div>'
        card = ""
    else:
        body = f'<p class="desc">{product["body"]}</p>'
        card = f'<div class="product-card"><h1>{product["title"]}</h1>{body}</div>'
    return f"""<!doctype html>
<html lang="{locale}">
<head>
<meta charset="utf-8">
<title>{product["title"]}</title>
{meta}{can_tag}{alts}</head>
<body>
<nav><a href="/">home</a> <a href="/{locale}/">{locale} catalog</a></nav>
{card}
{'' if card else body}
<footer>{a_tags}</footer>
</body>
</html>
"""


def index_html(locale: str | None) -> str:
    if locale is None:
        items = " ".join(f'<a href="/{loc}/">{LOCALE_LABEL[loc]}</a>' for loc in LOCALES)
        return f"""<!doctype html><html><head><title>Catalog</title></head>
<body><h1>Catalog</h1><p>{items}</p>
<p><a href="/sitemap.xml">sitemap</a></p>
<p><a href="/p/kettle">language-negotiated kettle</a></p>
</body></html>"""
    slugs = [s for s, data in PRODUCTS.items() if locale in data or (s == "kettle" and locale == "ja")]
    lis = "".join(f'<li><a href="/{locale}/p/{s}">{s}</a></li>' for s in slugs)
    # also a tracking-param link to exercise normalization
    lis += f'<li><a href="/{locale}/p/mug?utm_campaign=nav&fbclid=abc">mug tracked</a></li>'
    return f"""<!doctype html><html lang="{locale}"><head><title>{locale} catalog</title></head>
<body><h1>{LOCALE_LABEL[locale]}</h1><ul>{lis}</ul><p><a href="/">home</a></p></body></html>"""


def sitemap_xml() -> str:
    urls = []
    for (slug, loc), lastmod in sorted(SITEMAP_LASTMOD.items()):
        urls.append(f"  <url><loc>/{loc}/p/{slug}</loc><lastmod>{lastmod}</lastmod></url>")
    # include prefix-less kettle to exercise negotiation + alias
    urls.append("  <url><loc>/p/kettle</loc><lastmod>2026-01-10</lastmod></url>")
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body
        + "\n</urlset>\n"
    )


def negotiate_locale(accept: str) -> str:
    if not accept:
        return "en"
    # very small parser: take first known tag in order of q, default q=1
    parts = []
    for raw in accept.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ";q=" in raw:
            tag, q = raw.split(";q=", 1)
            try:
                qv = float(q)
            except ValueError:
                qv = 0.0
        else:
            tag, qv = raw, 1.0
        tag = tag.strip().lower()
        if "-" in tag:
            tag = tag.split("-", 1)[0]
        if tag in LOCALES:
            parts.append((qv, tag))
    if not parts:
        return "en"
    parts.sort(key=lambda x: -x[0])
    return parts[0][1]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, status: int, body: bytes, content_type: str, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        accept = self.headers.get("Accept-Language", "")

        if path == "/sitemap.xml":
            data = sitemap_xml().encode("utf-8")
            return self._send(200, data, "application/xml; charset=utf-8")
        if path == "/":
            return self._send(200, index_html(None).encode("utf-8"), "text/html; charset=utf-8")
        if path in {f"/{loc}/" for loc in LOCALES} or path in {f"/{loc}" for loc in LOCALES}:
            loc = path.strip("/").split("/")[0]
            return self._send(200, index_html(loc).encode("utf-8"), "text/html; charset=utf-8")

        # language-negotiated unprefixed product
        if path.startswith("/p/"):
            slug = path[len("/p/"):].strip("/")
            loc = negotiate_locale(accept)
            dest = f"/{loc}/p/{slug}"
            return self._send(302, b"", "text/plain", {"Location": dest})

        # locale product
        segs = [s for s in path.split("/") if s]
        if len(segs) == 3 and segs[0] in LOCALES and segs[1] == "p":
            loc, slug = segs[0], segs[2]
            if slug == "kettle" and loc == "ja":
                return self._send(302, b"", "text/plain", {"Location": "/en/p/kettle"})
            prod = PRODUCTS.get(slug, {}).get(loc)
            if not prod:
                return self._send(404, b"not found", "text/plain; charset=utf-8")
            extra = []
            if slug == "lamp" and loc == "en":
                extra.append("/en/p/mug")
            html = page_html(slug, loc, prod, extra)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

        return self._send(404, b"not found", "text/plain; charset=utf-8")


def serve(host="127.0.0.1", port=8761, root=None):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"localemesh fixture site on http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8761)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--root", default="fixtures/catalog")
    args = ap.parse_args()
    serve(args.host, args.port, args.root)
