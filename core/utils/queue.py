from __future__ import annotations
from collections import deque
from heapq import heappush, heappop


class URLQueue:
    def __init__(self, priority_mode: bool = False):
        self._priority_mode = priority_mode
        self._fifo: deque = deque()
        self._heap: list[tuple[int, int, str]] = []
        self._counter = 0

    def push(self, url: str, priority: int = 0):
        if self._priority_mode:
            heappush(self._heap, (priority, self._counter, url))
        else:
            self._fifo.append(url)
        self._counter += 1

    def pop(self) -> str | None:
        if self._priority_mode:
            if self._heap:
                return heappop(self._heap)[-1]
            return None
        if self._fifo:
            return self._fifo.popleft()
        return None

    def __len__(self) -> int:
        return len(self._fifo) + len(self._heap)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0
