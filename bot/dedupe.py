"""Short-lived in-memory protection against duplicate Discord events."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable, Hashable


class MessageDeduplicator:
    """Keep message IDs for a bounded time and capacity."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 15 * 60,
        max_entries: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._entries: OrderedDict[Hashable, float] = OrderedDict()

    def _purge_expired(self, now: float) -> None:
        expired = [
            message_id
            for message_id, marked_at in self._entries.items()
            if now - marked_at >= self._ttl_seconds
        ]
        for message_id in expired:
            self._entries.pop(message_id, None)

    def check_and_mark(self, message_id: Hashable) -> bool:
        """Atomically mark a new ID and return whether it should be processed."""

        now = self._clock()
        self._purge_expired(now)
        if message_id in self._entries:
            return False

        self._entries[message_id] = now
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)
        return True
