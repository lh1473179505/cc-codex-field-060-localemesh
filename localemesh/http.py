"""Minimal HTTP client used by the crawler. Records redirect chains explicitly."""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urljoin


@dataclass
class Response:
    url: str
    status: int
    headers: dict
    body: bytes
    final_url: str
    redirect_chain: list = field(default_factory=list)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpClient:
    def __init__(self, user_agent: str = "localemesh/0.1"):
        self.user_agent = user_agent
        self._opener = urllib.request.build_opener(_NoRedirect)

    def get(self, url: str, headers: Mapping[str, str] | None = None, follow_redirects: bool = True) -> Response:
        hdrs = {"User-Agent": self.user_agent}
        if headers:
            hdrs.update(headers)
        chain = []
        current = url
        body = b""
        status = 0
        resp_headers = {}
        final = url
        for _ in range(8):
            req = urllib.request.Request(current, headers=hdrs, method="GET")
            try:
                with self._opener.open(req, timeout=10) as r:
                    status = r.getcode()
                    resp_headers = {k.lower(): v for k, v in r.headers.items()}
                    body = r.read()
                    final = current
                    break
            except urllib.error.HTTPError as e:
                status = e.code
                resp_headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
                body = e.read() if e.fp else b""
                loc = resp_headers.get("location")
                if status in {301, 302, 303, 307, 308} and loc and follow_redirects:
                    chain.append(current)
                    current = urljoin(current, loc)
                    final = current
                    continue
                final = current
                break
        return Response(url=url, status=status, headers=resp_headers, body=body, final_url=final, redirect_chain=chain)
