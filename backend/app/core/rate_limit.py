"""
Sliding-Window Rate Limiter for CONVELINA API endpoints.

Protects sensitive authentication, OTP, document upload, conflict detection,
and AI assistant routes against abuse and brute-force traffic.
"""

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Tuple


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def check_and_record(
        self, key: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Records a hit for `key` if below `limit` within `window_seconds`.
        Returns (allowed, remaining, retry_after_seconds).
        """
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return False, 0, retry_after

            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return True, remaining, 0

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = SlidingWindowRateLimiter()

