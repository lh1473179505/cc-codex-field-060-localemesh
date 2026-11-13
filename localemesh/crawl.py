"""Crawl orchestrator. Wiring exists; cluster/classify/sink logic is not implemented."""


def run_crawl(args) -> int:
    raise NotImplementedError(
        "run_crawl is not implemented. Use localemesh.http, sitemap, htmlparse, frontier and urls; "
        "implement cluster merge, soft-404 classification, sitemap stale detection and outputs described in docs/."
    )
