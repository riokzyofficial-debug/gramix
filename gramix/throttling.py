from __future__ import annotations
import asyncio
import threading
import time
from collections.abc import Callable
from typing import Any

class ThrottlingMiddleware:

    def __init__(
        self,
        rate: float = 1.0,
        on_throttle: Callable | None = None,
    ) -> None:
        self._rate = rate
        self._on_throttle = on_throttle
        self._last_seen: dict[int, float] = {}
        self._lock = threading.Lock()

    def _get_key(self, update: Any) -> int | None:
        from_user = getattr(update, "from_user", None)
        if from_user is not None:
            return getattr(from_user, "id", None)
        chat = getattr(update, "chat", None)
        if chat is not None:
            return getattr(chat, "id", None)
        return None

    _CLEANUP_THRESHOLD: int = 10_000

    def _is_throttled(self, key: int) -> bool:
        now = time.monotonic()
        with self._lock:
            last = self._last_seen.get(key)
            if last is None or (now - last) >= self._rate:
                self._last_seen[key] = now
                self._maybe_cleanup(now)
                return False
            return True

    def _maybe_cleanup(self, now: float) -> None:

        if len(self._last_seen) < self._CLEANUP_THRESHOLD:
            return
        cutoff = now - max(self._rate * 10, 300.0)
        stale = [k for k, t in self._last_seen.items() if t < cutoff]
        for k in stale:
            del self._last_seen[k]

    def __call__(self, update: Any, next_fn: Callable) -> None:
        key = self._get_key(update)
        if key is not None and self._is_throttled(key):
            if self._on_throttle is not None:
                if asyncio.iscoroutinefunction(self._on_throttle):

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._on_throttle(update))
                    except RuntimeError:
                        asyncio.run(self._on_throttle(update))
                else:
                    self._on_throttle(update)
            return
        next_fn()

    async def async_call(self, update: Any, next_fn: Callable) -> None:
        key = self._get_key(update)
        if key is not None and self._is_throttled(key):
            if self._on_throttle is not None:
                if asyncio.iscoroutinefunction(self._on_throttle):
                    await self._on_throttle(update)
                else:
                    self._on_throttle(update)
            return
        if asyncio.iscoroutinefunction(next_fn):
            await next_fn()
        else:
            next_fn()
