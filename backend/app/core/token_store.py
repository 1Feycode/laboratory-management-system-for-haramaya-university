import asyncio
import time


class InMemoryRefreshTokenStore:
    def __init__(self) -> None:
        self._revoked: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def consume(self, token_id: str, expires_at: int) -> bool:
        async with self._lock:
            self._prune()
            if token_id in self._revoked:
                return False
            self._revoked[token_id] = expires_at
            return True

    async def revoke(self, token_id: str, expires_at: int) -> None:
        async with self._lock:
            self._prune()
            self._revoked[token_id] = expires_at

    async def clear(self) -> None:
        async with self._lock:
            self._revoked.clear()

    def _prune(self) -> None:
        now = int(time.time())
        self._revoked = {
            token_id: expiry
            for token_id, expiry in self._revoked.items()
            if expiry > now
        }


refresh_token_store = InMemoryRefreshTokenStore()
