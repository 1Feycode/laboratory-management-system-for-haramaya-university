import asyncio
import time

from fastapi import HTTPException


class InMemoryRateLimiter:
    def __init__(self, limit: int = 10, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def check(self, *keys: str) -> None:
        now = time.monotonic()
        async with self._lock:
            self._prune(now)
            for key in keys:
                window_start, count = self._hits.get(key, (now, 0))
                if count >= self.limit:
                    retry_after = max(1, int(self.window_seconds - (now - window_start)))
                    raise HTTPException(
                        status_code=429,
                        detail="Too many authentication attempts",
                        headers={"Retry-After": str(retry_after)},
                    )
            for key in keys:
                window_start, count = self._hits.get(key, (now, 0))
                if now - window_start >= self.window_seconds:
                    window_start, count = now, 0
                self._hits[key] = (window_start, count + 1)

    async def clear(self) -> None:
        async with self._lock:
            self._hits.clear()

    def _prune(self, now: float) -> None:
        self._hits = {
            key: value
            for key, value in self._hits.items()
            if now - value[0] < self.window_seconds
        }


auth_rate_limiter = InMemoryRateLimiter()
