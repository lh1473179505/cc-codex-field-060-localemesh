"""URL frontier with a seen set. Cycle safety beyond normalize+seen is left to crawl.py."""
from __future__ import annotations

from collections import deque
from localemesh.urls import normalize


class Frontier:
    def __init__(self, base: str):
        self.base = base
        self.q = deque()
        self.seen = set()
        self.skipped_duplicate = 0

    def add(self, url: str) -> bool:
        n = normalize(url, self.base)
        if n in self.seen:
            self.skipped_duplicate += 1
            return False
        self.seen.add(n)
        self.q.append(n)
        return True

    def __len__(self):
        return len(self.q)

    def pop(self) -> str:
        return self.q.popleft()
