from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def _load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _origin(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, "", "", "")).rstrip("/")


def _abs(value, origin: str):
    if value is None:
        return value
    if isinstance(value, list):
        return [_abs(v, origin) for v in value]
    if isinstance(value, dict):
        return {k: _abs(v, origin) if k != "_rules" else v for k, v in value.items()}
    if isinstance(value, str) and value.startswith("/"):
        return origin + value
    return value


def run_verify(args) -> int:
    out = Path(args.out)
    expect = json.loads(Path(args.expect).read_text(encoding="utf-8"))
    clusters_path = out / "clusters.jsonl"
    report_path = out / "report.json"
    if not clusters_path.is_file() or not report_path.is_file():
        print("missing clusters.jsonl or report.json")
        return 1
    got_clusters = _load_jsonl(clusters_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not got_clusters:
        print("clusters.jsonl is empty")
        return 1
    origin = _origin(got_clusters[0]["canonical_url"])
    expect = _abs(expect, origin)

    errors = []
    exp_clusters = [c for c in expect["clusters"]]
    if len(got_clusters) != len(exp_clusters):
        errors.append(f"cluster count {len(got_clusters)} != {len(exp_clusters)}")

    def key(c):
        return c.get("canonical_url")

    got_by = {key(c): c for c in got_clusters}
    exp_by = {key(c): c for c in exp_clusters}
    if set(got_by) != set(exp_by):
        errors.append(
            f"canonical set mismatch extra={sorted(set(got_by)-set(exp_by))} missing={sorted(set(exp_by)-set(got_by))}"
        )
    for k, exp in exp_by.items():
        got = got_by.get(k)
        if not got:
            continue
        exp_locales = sorted(m["locale"] for m in exp["members"])
        got_locales = sorted(m["locale"] for m in got.get("members") or [])
        if exp_locales != got_locales:
            errors.append(f"{k} locales {got_locales} != {exp_locales}")
        exp_urls = sorted(m["url"] for m in exp["members"])
        got_urls = sorted(m["url"] for m in got.get("members") or [])
        if exp_urls != got_urls:
            errors.append(f"{k} member urls mismatch\n    got={got_urls}\n    exp={exp_urls}")
        if sorted(got.get("aliases") or []) != sorted(exp.get("aliases") or []):
            errors.append(f"{k} aliases {got.get('aliases')} != {exp.get('aliases')}")

        def dkey(d):
            return (d.get("from"), d.get("to"))

        if sorted(got.get("dangling_hreflang") or [], key=dkey) != sorted(exp.get("dangling_hreflang") or [], key=dkey):
            errors.append(f"{k} dangling_hreflang mismatch")

    def slist(name):
        return sorted(report.get(name) or [])

    if slist("soft_404") != sorted(expect["report"]["soft_404"]):
        errors.append(f"soft_404 {slist('soft_404')} != {expect['report']['soft_404']}")
    if slist("http_404") != sorted(expect["report"]["http_404"]):
        errors.append(f"http_404 {slist('http_404')} != {expect['report']['http_404']}")

    def sk(x):
        return x["url"]

    got_stale = sorted(report.get("sitemap_stale") or [], key=sk)
    exp_stale = sorted(expect["report"]["sitemap_stale"], key=sk)
    if got_stale != exp_stale:
        errors.append(f"sitemap_stale {got_stale} != {exp_stale}")

    if errors:
        print("verify failed:")
        for e in errors:
            print(" -", e)
        return 1
    print("verify ok")
    return 0
