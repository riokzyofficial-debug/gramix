from __future__ import annotations
import asyncio
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from gramix.bot import Bot
from gramix.constants import POLLING_TIMEOUT
from gramix.exceptions import NetworkError, TelegramAPIError, WebhookError
from gramix.middleware import MiddlewareManager
from gramix.router import Router
from gramix.types.callback import CallbackQuery
from gramix.types.chat_member import ChatMemberUpdated
from gramix.types.inline_query import InlineQuery
from gramix.types.message import Message

logger = logging.getLogger(__name__)

class Dispatcher:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._routers: list[Router] = []
        self._middleware = MiddlewareManager()
        self._running = False
        self._startup_handlers: list[Callable] = []
        self._shutdown_handlers: list[Callable] = []
        self._webhook_secret: str | None = None

    def include(self, router: Router) -> None:
        self._routers.append(router)

    @property
    def middleware(self) -> Callable:
        return self._middleware.register

    def on_startup(self, func: Callable) -> Callable:
        self._startup_handlers.append(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        self._shutdown_handlers.append(func)
        return func

    def _dispatch(self, raw_update: dict) -> None:
        if "message" in raw_update:
            msg = Message.from_dict(raw_update["message"], self._bot)
            if self._middleware._middlewares:
                self._middleware.run(msg, self._route_message)
            else:
                self._route_message(msg)

        elif "edited_message" in raw_update:
            msg = Message.from_dict(raw_update["edited_message"], self._bot)
            if self._middleware._middlewares:
                self._middleware.run(msg, self._route_edited_message)
            else:
                self._route_edited_message(msg)

        elif "channel_post" in raw_update:
            msg = Message.from_dict(raw_update["channel_post"], self._bot)
            if self._middleware._middlewares:
                self._middleware.run(msg, self._route_channel_post)
            else:
                self._route_channel_post(msg)

        elif "edited_channel_post" in raw_update:
            msg = Message.from_dict(raw_update["edited_channel_post"], self._bot)
            if self._middleware._middlewares:
                self._middleware.run(msg, self._route_edited_channel_post)
            else:
                self._route_edited_channel_post(msg)

        elif "callback_query" in raw_update:
            cb = CallbackQuery.from_dict(raw_update["callback_query"], self._bot)
            if cb.game_short_name is not None:
                def _route_game(c: CallbackQuery) -> None:
                    for router in self._routers:
                        if router.process_game_callback(c):
                            break
                if self._middleware._middlewares:
                    self._middleware.run(cb, _route_game)
                else:
                    _route_game(cb)
            else:
                def _route_cb(c: CallbackQuery) -> None:
                    for router in self._routers:
                        if router.process_callback(c):
                            break
                if self._middleware._middlewares:
                    self._middleware.run(cb, _route_cb)
                else:
                    _route_cb(cb)

        elif "inline_query" in raw_update:
            query = InlineQuery.from_dict(raw_update["inline_query"], self._bot)
            def _route_inline(q: InlineQuery) -> None:
                for router in self._routers:
                    if router.process_inline(q):
                        break
            if self._middleware._middlewares:
                self._middleware.run(query, _route_inline)
            else:
                _route_inline(query)

        elif "my_chat_member" in raw_update or "chat_member" in raw_update:
            key = "my_chat_member" if "my_chat_member" in raw_update else "chat_member"
            update = ChatMemberUpdated.from_dict(raw_update[key])
            if self._middleware._middlewares:
                self._middleware.run(update, lambda u: [router.process_chat_member(u) for router in self._routers])
            else:
                for router in self._routers:
                    router.process_chat_member(update)

        elif "poll_answer" in raw_update:
            from gramix.types.poll import PollAnswer
            answer = PollAnswer.from_dict(raw_update["poll_answer"])
            def _route_poll(a: object) -> None:
                for router in self._routers:
                    if router.process_poll_answer(a):
                        break
            if self._middleware._middlewares:
                self._middleware.run(answer, _route_poll)
            else:
                _route_poll(answer)

        elif "pre_checkout_query" in raw_update:
            from gramix.types.payment import PreCheckoutQuery
            query = PreCheckoutQuery.from_dict(raw_update["pre_checkout_query"])
            def _route_precheckout(q: object) -> None:
                for router in self._routers:
                    if router.process_pre_checkout_query(q):
                        break
            if self._middleware._middlewares:
                self._middleware.run(query, _route_precheckout)
            else:
                _route_precheckout(query)

    async def _async_dispatch(self, raw_update: dict) -> None:
        if "message" in raw_update:
            msg = Message.from_dict(raw_update["message"], self._bot)
            if self._middleware._middlewares:
                await self._middleware.async_run(msg, self._async_route_message)
            else:
                await self._async_route_message(msg)

        elif "edited_message" in raw_update:
            msg = Message.from_dict(raw_update["edited_message"], self._bot)
            if self._middleware._middlewares:
                await self._middleware.async_run(msg, self._async_route_edited_message)
            else:
                await self._async_route_edited_message(msg)

        elif "channel_post" in raw_update:
            msg = Message.from_dict(raw_update["channel_post"], self._bot)
            if self._middleware._middlewares:
                await self._middleware.async_run(msg, self._async_route_channel_post)
            else:
                await self._async_route_channel_post(msg)

        elif "edited_channel_post" in raw_update:
            msg = Message.from_dict(raw_update["edited_channel_post"], self._bot)
            if self._middleware._middlewares:
                await self._middleware.async_run(msg, self._async_route_edited_channel_post)
            else:
                await self._async_route_edited_channel_post(msg)

        elif "callback_query" in raw_update:
            cb = CallbackQuery.from_dict(raw_update["callback_query"], self._bot)
            if cb.game_short_name is not None:
                async def _route_game(c: CallbackQuery) -> None:
                    for router in self._routers:
                        if await router.async_process_game_callback(c):
                            break
                if self._middleware._middlewares:
                    await self._middleware.async_run(cb, _route_game)
                else:
                    await _route_game(cb)
            else:
                async def _route_cb(c: CallbackQuery) -> None:
                    for router in self._routers:
                        if await router.async_process_callback(c):
                            break
                if self._middleware._middlewares:
                    await self._middleware.async_run(cb, _route_cb)
                else:
                    await _route_cb(cb)

        elif "inline_query" in raw_update:
            query = InlineQuery.from_dict(raw_update["inline_query"], self._bot)
            async def _route_inline(q: InlineQuery) -> None:
                for router in self._routers:
                    if await router.async_process_inline(q):
                        break
            if self._middleware._middlewares:
                await self._middleware.async_run(query, _route_inline)
            else:
                await _route_inline(query)

        elif "my_chat_member" in raw_update or "chat_member" in raw_update:
            key = "my_chat_member" if "my_chat_member" in raw_update else "chat_member"
            update = ChatMemberUpdated.from_dict(raw_update[key])
            async def _route_member(u: ChatMemberUpdated) -> None:
                for router in self._routers:
                    await router.async_process_chat_member(u)
            if self._middleware._middlewares:
                await self._middleware.async_run(update, _route_member)
            else:
                await _route_member(update)

        elif "poll_answer" in raw_update:
            from gramix.types.poll import PollAnswer
            answer = PollAnswer.from_dict(raw_update["poll_answer"])
            async def _route_poll(a: object) -> None:
                for router in self._routers:
                    if await router.async_process_poll_answer(a):
                        break
            if self._middleware._middlewares:
                await self._middleware.async_run(answer, _route_poll)
            else:
                await _route_poll(answer)

        elif "pre_checkout_query" in raw_update:
            from gramix.types.payment import PreCheckoutQuery
            query = PreCheckoutQuery.from_dict(raw_update["pre_checkout_query"])
            async def _route_precheckout(q: object) -> None:
                for router in self._routers:
                    if await router.async_process_pre_checkout_query(q):
                        break
            if self._middleware._middlewares:
                await self._middleware.async_run(query, _route_precheckout)
            else:
                await _route_precheckout(query)

    def _route_message(self, msg: Message) -> None:
        if msg.successful_payment is not None:
            for router in self._routers:
                if router.process_successful_payment(msg):
                    break
            return
        for router in self._routers:
            if router.process_message(msg):
                break

    def _route_edited_message(self, msg: Message) -> None:
        for router in self._routers:
            if router.process_edited_message(msg):
                break

    def _route_channel_post(self, msg: Message) -> None:
        for router in self._routers:
            if router.process_channel_post(msg):
                break

    def _route_edited_channel_post(self, msg: Message) -> None:
        for router in self._routers:
            if router.process_edited_channel_post(msg):
                break

    async def _async_route_message(self, msg: Message) -> None:
        if msg.successful_payment is not None:
            for router in self._routers:
                if await router.async_process_successful_payment(msg):
                    break
            return
        for router in self._routers:
            if await router.async_process_message(msg):
                break

    async def _async_route_edited_message(self, msg: Message) -> None:
        for router in self._routers:
            if await router.async_process_edited_message(msg):
                break

    async def _async_route_channel_post(self, msg: Message) -> None:
        for router in self._routers:
            if await router.async_process_channel_post(msg):
                break

    async def _async_route_edited_channel_post(self, msg: Message) -> None:
        for router in self._routers:
            if await router.async_process_edited_channel_post(msg):
                break

    def run(
        self,
        *,
        webhook: bool = False,
        host: str = "0.0.0.0",
        port: int = 8080,
        webhook_url: str | None = None,
        secret_token: str | None = None,
        backend: str = "raw",
        drop_pending: bool = True,
    ) -> None:
        if webhook:
            self._run_webhook(host=host, port=port, url=webhook_url, secret_token=secret_token, backend=backend)
        else:
            self._run_polling(drop_pending=drop_pending)

    def _print_banner(self, username: str, user_id: int, mode: str) -> None:
        from gramix import __version__
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("━" * 40)
        logger.info("  gramix v%s", __version__)
        logger.info("  Бот:    @%s (id=%d)", username, user_id)
        logger.info("  Режим:  %s", mode)
        logger.info("  Старт:  %s", started_at)
        logger.info("━" * 40)

    def _run_polling(self, *, drop_pending: bool = True) -> None:
        me = self._bot.get_me()
        self._print_banner(me.username or str(me.id), me.id, "polling")
        self._call_handlers(self._startup_handlers)

        if drop_pending:
            try:
                updates = self._bot.get_updates(timeout=0, limit=100)
                while updates:
                    offset = updates[-1]["update_id"] + 1
                    updates = self._bot.get_updates(offset=offset, timeout=0, limit=100)
            except Exception:
                pass

        self._running = True
        self._stop_event = threading.Event()
        offset: int | None = None
        _CHUNK = 1

        def poll() -> None:
            nonlocal offset
            while not self._stop_event.is_set():
                try:
                    updates = self._bot.get_updates(offset=offset, timeout=_CHUNK)
                    if self._stop_event.is_set():
                        break
                    for update in updates:
                        offset = update["update_id"] + 1
                        try:
                            self._dispatch(update)
                        except Exception:
                            logger.exception("Ошибка при обработке update %d:", update["update_id"])
                except NetworkError as e:
                    if not self._stop_event.is_set():
                        logger.warning("Сетевая ошибка: %s. Переподключение...", e)
                        self._stop_event.wait(timeout=3)
                except TelegramAPIError as e:
                    if not self._stop_event.is_set():
                        logger.error("Telegram API ошибка: %s", e)
                        self._stop_event.wait(timeout=1)
                except Exception:
                    if not self._stop_event.is_set():
                        logger.exception("Неожиданная ошибка в polling:")
                        self._stop_event.wait(timeout=1)

        import signal as _signal

        def _stop(*_: Any) -> None:
            logger.info("Остановка бота...")
            self._running = False
            self._stop_event.set()
            self._bot.close()

        try:
            _signal.signal(_signal.SIGINT, _stop)
            _signal.signal(_signal.SIGTERM, _stop)
        except (OSError, ValueError):
            pass

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

        logger.info("Polling запущен. Ctrl+C для остановки.")
        try:
            while thread.is_alive():
                thread.join(timeout=0.2)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Остановка бота...")
            self._running = False
            self._stop_event.set()
            self._bot.close()
            thread.join(timeout=3)
        finally:
            self._call_handlers(self._shutdown_handlers)
            logger.info("Бот остановлен.")

    async def _async_polling(self, *, drop_pending: bool = True) -> None:
        me = await self._bot.async_get_me()
        self._print_banner(me.username or str(me.id), me.id, "async polling")
        await self._async_call_handlers(self._startup_handlers)

        if drop_pending:
            try:
                updates = await self._bot.async_get_updates(timeout=0, limit=100)
                while updates:
                    offset = updates[-1]["update_id"] + 1
                    updates = await self._bot.async_get_updates(offset=offset, timeout=0, limit=100)
            except Exception:
                pass

        self._running = True
        offset: int | None = None
        _CHUNK = 1

        logger.info("Async polling запущен. Ctrl+C для остановки.")
        try:
            while self._running:
                try:
                    updates = await self._bot.async_get_updates(
                        offset=offset, timeout=_CHUNK
                    )
                    for update in updates:
                        offset = update["update_id"] + 1
                        try:
                            await self._async_dispatch(update)
                        except Exception:
                            logger.exception(
                                "Ошибка при обработке update %d:", update["update_id"]
                            )
                except NetworkError as e:
                    if self._running:
                        logger.warning("Сетевая ошибка: %s.", e)
                        await asyncio.sleep(3)
                except TelegramAPIError as e:
                    if self._running:
                        logger.error("Telegram API ошибка: %s", e)
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
                except Exception:
                    if self._running:
                        logger.exception("Неожиданная ошибка:")
                        await asyncio.sleep(1)
        finally:
            await self._async_call_handlers(self._shutdown_handlers)
            await self._bot.async_close()
            logger.info("Бот остановлен.")

    def run_async(self, *, drop_pending: bool = True) -> None:
        asyncio.run(self._async_polling(drop_pending=drop_pending))

    def _run_webhook(self, host: str, port: int, url: str | None, backend: str = "raw", secret_token: str | None = None) -> None:
        from gramix.env import get_webhook_url

        webhook_url = url or get_webhook_url()
        if not webhook_url:
            raise WebhookError(
                "URL webhook не указан. Передай параметр url= или установи WEBHOOK_URL в .env."
            )

        self._bot.set_webhook(webhook_url, secret_token=secret_token)
        self._webhook_secret = secret_token
        me = self._bot.get_me()
        self._print_banner(me.username or str(me.id), me.id, f"webhook [{backend}] {webhook_url}")
        logger.info("Сервер: %s:%d", host, port)
        self._call_handlers(self._startup_handlers)

        if backend == "aiohttp":
            self._run_webhook_aiohttp(host=host, port=port)
        elif backend == "fastapi":
            self._run_webhook_fastapi(host=host, port=port)
        else:
            self._run_webhook_raw(host=host, port=port)

    def _run_webhook_raw(self, host: str, port: int) -> None:
        import socket

        self._running = True
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        server.settimeout(1.0)

        try:
            while self._running:
                try:
                    conn, _ = server.accept()
                    self._handle_webhook_request(conn)
                except TimeoutError:
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            self._bot.delete_webhook()
            self._call_handlers(self._shutdown_handlers)
            self._bot.close()
            logger.info("Webhook сервер остановлен.")

    def _run_webhook_aiohttp(self, host: str, port: int) -> None:
        try:
            from aiohttp import web
        except ImportError:
            raise WebhookError(
                "aiohttp не установлен. Установи: pip install gramix[aiohttp]"
            )

        async def handle(request: web.Request) -> web.Response:
            try:
                data = await request.json()
                await self._async_dispatch(data)
            except Exception:
                logger.exception("Ошибка при обработке webhook запроса:")
            return web.Response(text="OK")

        async def run() -> None:
            app = web.Application()
            app.router.add_post("/", handle)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()
            logger.info("aiohttp webhook сервер запущен.")
            try:
                while True:
                    await asyncio.sleep(3600)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                await runner.cleanup()
                self._bot.delete_webhook()
                await self._async_call_handlers(self._shutdown_handlers)
                await self._bot.async_close()
                logger.info("Webhook сервер остановлен.")

        asyncio.run(run())

    def _run_webhook_fastapi(self, host: str, port: int) -> None:
        try:
            import uvicorn
            from contextlib import asynccontextmanager
            from fastapi import FastAPI, Request, Response
        except ImportError:
            raise WebhookError(
                "fastapi/uvicorn не установлены. Установи: pip install gramix[fastapi]"
            )

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            self._bot.delete_webhook()
            await self._async_call_handlers(self._shutdown_handlers)
            await self._bot.async_close()
            logger.info("Webhook сервер остановлен.")

        app = FastAPI(lifespan=lifespan)

        @app.post("/")
        async def handle(request: Request) -> Response:
            try:
                data = await request.json()
                await self._async_dispatch(data)
            except Exception:
                logger.exception("Ошибка при обработке webhook запроса:")
            return Response(content="OK")

        logger.info("fastapi webhook сервер запущен.")
        uvicorn.run(app, host=host, port=port)

    def _handle_webhook_request(self, conn: Any) -> None:
        import json
        try:
            raw = b""
            conn.settimeout(5.0)
            while True:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                raw += chunk
                if b"\r\n\r\n" in raw:
                    header_part, _, body_part = raw.partition(b"\r\n\r\n")
                    headers = {}
                    for line in header_part.decode("utf-8", errors="replace").splitlines()[1:]:
                        if ":" in line:
                            k, _, v = line.partition(":")
                            headers[k.strip().lower()] = v.strip()

                    if self._webhook_secret is not None:
                        incoming = headers.get("x-telegram-bot-api-secret-token", "")
                        if incoming != self._webhook_secret:
                            conn.send(
                                b"HTTP/1.1 403 Forbidden\r\nContent-Length: 9\r\n"
                                b"Content-Type: text/plain\r\n\r\nForbidden"
                            )
                            return

                    content_length = int(headers.get("content-length", 0))
                    while len(body_part) < content_length:
                        chunk = conn.recv(8192)
                        if not chunk:
                            break
                        body_part += chunk
                    if body_part:
                        self._dispatch(json.loads(body_part.decode("utf-8")))
                    break

            conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Type: text/plain\r\n\r\nOK")
        except Exception:
            logger.exception("Ошибка при обработке webhook запроса:")
        finally:
            conn.close()

    def _call_handlers(self, handlers: list[Callable]) -> None:
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):

                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop is not None and loop.is_running():

                        import concurrent.futures
                        future = asyncio.run_coroutine_threadsafe(handler(), loop)
                        future.result(timeout=30)
                    else:
                        asyncio.run(handler())
                else:
                    handler()
            except Exception:
                logger.exception("Ошибка в lifecycle handler:")

    async def _async_call_handlers(self, handlers: list[Callable]) -> None:
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception:
                logger.exception("Ошибка в lifecycle handler:")
