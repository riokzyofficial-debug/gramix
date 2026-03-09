from __future__ import annotations
import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class MiddlewareManager:
    def __init__(self) -> None:
        self._middlewares: list[Callable] = []

    def register(self, func: Callable) -> Callable:
        self._middlewares.append(func)
        logger.debug("Middleware зарегистрирован: %s", func.__name__)
        return func

    def run(self, update: Any, handler: Callable) -> None:
        chain = list(self._middlewares)

        def call_next(idx: int) -> None:
            if idx < len(chain):
                chain[idx](update, lambda: call_next(idx + 1))
            else:
                handler(update)

        call_next(0)

    async def async_run(self, update: Any, handler: Callable) -> None:
        chain = list(self._middlewares)

        async def call_next(idx: int) -> None:
            if idx < len(chain):
                mw = chain[idx]

                async def next_fn() -> None:
                    await call_next(idx + 1)

                if asyncio.iscoroutinefunction(mw):
                    await mw(update, next_fn)
                else:
                    mw(update, next_fn)
            else:
                if asyncio.iscoroutinefunction(handler):
                    await handler(update)
                else:
                    handler(update)

        await call_next(0)
