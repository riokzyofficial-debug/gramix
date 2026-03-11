from __future__ import annotations
import asyncio
import logging
from collections.abc import Callable
from typing import Any

from gramix.filters import (
    BaseFilter,
    CallbackFilter,
    CommandFilter,
    RegexFilter,
    TextFilter,
)
from gramix.fsm import BaseStorage, MemoryStorage, Step
from gramix.types.callback import CallbackQuery
from gramix.types.chat_member import ChatMemberUpdated
from gramix.types.inline_query import InlineQuery
from gramix.types.message import Message

logger = logging.getLogger(__name__)

class Handler:
    __slots__ = ("func", "filters")

    def __init__(self, func: Callable, filters: list[BaseFilter]) -> None:
        self.func = func
        self.filters = filters

    def matches(self, update: Any) -> bool:
        return all(f.check(update) for f in self.filters)

class Router:
    def __init__(self, storage: BaseStorage | None = None) -> None:
        self._message_handlers: list[Handler] = []
        self._edited_message_handlers: list[Handler] = []
        self._channel_post_handlers: list[Handler] = []
        self._edited_channel_post_handlers: list[Handler] = []
        self._callback_handlers: list[Handler] = []
        self._inline_handlers: list[Handler] = []
        self._chat_member_handlers: list[Callable] = []
        self._game_callback_handlers: list[Callable] = []
        self._state_handlers: dict[str, Callable] = {}
        self._poll_answer_handlers: list[Callable] = []
        self._pre_checkout_handlers: list[Callable] = []
        self._successful_payment_handlers: list[Callable] = []
        self.fsm: BaseStorage = storage if storage is not None else MemoryStorage()

    def message(self, *args: str | BaseFilter, **kwargs: Any) -> Callable:
        filters = self._build_message_filters(args, kwargs)

        def decorator(func: Callable) -> Callable:
            self._message_handlers.append(Handler(func, filters))
            logger.debug("Handler: %s → %s", func.__name__, [type(f).__name__ for f in filters])
            return func

        return decorator

    def edited_message(self, *args: str | BaseFilter, **kwargs: Any) -> Callable:
        filters = self._build_message_filters(args, kwargs)

        def decorator(func: Callable) -> Callable:
            self._edited_message_handlers.append(Handler(func, filters))
            logger.debug("EditedMessage handler: %s → %s", func.__name__, [type(f).__name__ for f in filters])
            return func

        return decorator

    def channel_post(self, *args: str | BaseFilter, **kwargs: Any) -> Callable:
        filters = self._build_message_filters(args, kwargs)

        def decorator(func: Callable) -> Callable:
            self._channel_post_handlers.append(Handler(func, filters))
            logger.debug("ChannelPost handler: %s → %s", func.__name__, [type(f).__name__ for f in filters])
            return func

        return decorator

    def edited_channel_post(self, *args: str | BaseFilter, **kwargs: Any) -> Callable:
        filters = self._build_message_filters(args, kwargs)

        def decorator(func: Callable) -> Callable:
            self._edited_channel_post_handlers.append(Handler(func, filters))
            logger.debug("EditedChannelPost handler: %s → %s", func.__name__, [type(f).__name__ for f in filters])
            return func

        return decorator

    def callback(self, *data: str, prefix: str | None = None) -> Callable:
        from gramix.filters import CallbackPrefixFilter

        filters: list[BaseFilter] = (
            [CallbackPrefixFilter(prefix)] if prefix
            else ([CallbackFilter(*data)] if data else [])
        )

        def decorator(func: Callable) -> Callable:
            self._callback_handlers.append(Handler(func, filters))
            return func

        return decorator

    def inline(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._inline_handlers.append(Handler(func, []))
            return func
        return decorator

    def chat_member(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._chat_member_handlers.append(func)
            return func
        return decorator

    def game_callback(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._game_callback_handlers.append(func)
            return func
        return decorator

    def poll_answer(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._poll_answer_handlers.append(func)
            return func
        return decorator

    def pre_checkout_query(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._pre_checkout_handlers.append(func)
            return func
        return decorator

    def successful_payment(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._successful_payment_handlers.append(func)
            return func
        return decorator

    def state(self, step: Step) -> Callable:
        key = f"{step._owner}.{step._name}"

        def decorator(func: Callable) -> Callable:
            self._state_handlers[key] = func
            logger.debug("FSM handler: %s → %s", key, func.__name__)
            return func

        return decorator

    def process_message(self, message: Message) -> bool:
        user_id = message.from_user.id if message.from_user else None

        if user_id:
            ctx = self.fsm.get(user_id)
            if ctx.is_active and ctx.current in self._state_handlers:
                self._call(self._state_handlers[ctx.current], message, ctx)
                return True

        for handler in self._message_handlers:
            if handler.matches(message):
                self._call(handler.func, message)
                return True

        return False

    def process_edited_message(self, message: Message) -> bool:
        for handler in self._edited_message_handlers:
            if handler.matches(message):
                self._call(handler.func, message)
                return True
        return False

    def process_channel_post(self, message: Message) -> bool:
        for handler in self._channel_post_handlers:
            if handler.matches(message):
                self._call(handler.func, message)
                return True
        return False

    def process_edited_channel_post(self, message: Message) -> bool:
        for handler in self._edited_channel_post_handlers:
            if handler.matches(message):
                self._call(handler.func, message)
                return True
        return False

    async def async_process_message(self, message: Message) -> bool:
        user_id = message.from_user.id if message.from_user else None

        if user_id:
            ctx = self.fsm.get(user_id)
            if ctx.is_active and ctx.current in self._state_handlers:
                await self._async_call(self._state_handlers[ctx.current], message, ctx)
                return True

        for handler in self._message_handlers:
            if handler.matches(message):
                await self._async_call(handler.func, message)
                return True

        return False

    async def async_process_edited_message(self, message: Message) -> bool:
        for handler in self._edited_message_handlers:
            if handler.matches(message):
                await self._async_call(handler.func, message)
                return True
        return False

    async def async_process_channel_post(self, message: Message) -> bool:
        for handler in self._channel_post_handlers:
            if handler.matches(message):
                await self._async_call(handler.func, message)
                return True
        return False

    async def async_process_edited_channel_post(self, message: Message) -> bool:
        for handler in self._edited_channel_post_handlers:
            if handler.matches(message):
                await self._async_call(handler.func, message)
                return True
        return False

    def process_callback(self, callback: CallbackQuery) -> bool:
        for handler in self._callback_handlers:
            if handler.matches(callback):
                self._call(handler.func, callback)
                return True
        return False

    async def async_process_callback(self, callback: CallbackQuery) -> bool:
        for handler in self._callback_handlers:
            if handler.matches(callback):
                await self._async_call(handler.func, callback)
                return True
        return False

    def process_inline(self, query: InlineQuery) -> bool:
        for handler in self._inline_handlers:
            if handler.matches(query):
                self._call(handler.func, query)
                return True
        return False

    async def async_process_inline(self, query: InlineQuery) -> bool:
        for handler in self._inline_handlers:
            if handler.matches(query):
                await self._async_call(handler.func, query)
                return True
        return False

    def process_chat_member(self, update: ChatMemberUpdated) -> bool:
        called = False
        for func in self._chat_member_handlers:
            self._call(func, update)
            called = True
        return called

    async def async_process_chat_member(self, update: ChatMemberUpdated) -> bool:
        called = False
        for func in self._chat_member_handlers:
            await self._async_call(func, update)
            called = True
        return called

    def process_game_callback(self, callback: "CallbackQuery") -> bool:
        for func in self._game_callback_handlers:
            self._call(func, callback)
            return True
        return False

    async def async_process_game_callback(self, callback: "CallbackQuery") -> bool:
        for func in self._game_callback_handlers:
            await self._async_call(func, callback)
            return True
        return False

    def process_poll_answer(self, answer: object) -> bool:
        for func in self._poll_answer_handlers:
            self._call(func, answer)
            return True
        return False

    async def async_process_poll_answer(self, answer: object) -> bool:
        for func in self._poll_answer_handlers:
            await self._async_call(func, answer)
            return True
        return False

    def process_pre_checkout_query(self, query: object) -> bool:
        for func in self._pre_checkout_handlers:
            self._call(func, query)
            return True
        return False

    async def async_process_pre_checkout_query(self, query: object) -> bool:
        for func in self._pre_checkout_handlers:
            await self._async_call(func, query)
            return True
        return False

    def process_successful_payment(self, message: object) -> bool:
        for func in self._successful_payment_handlers:
            self._call(func, message)
            return True
        return False

    async def async_process_successful_payment(self, message: object) -> bool:
        for func in self._successful_payment_handlers:
            await self._async_call(func, message)
            return True
        return False

    def _call(self, func: Callable, *args: Any) -> None:
        try:
            func(*args)
        except Exception:
            logger.exception("Ошибка в handler %s:", func.__name__)

    async def _async_call(self, func: Callable, *args: Any) -> None:
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args)
            else:
                func(*args)
        except Exception:
            logger.exception("Ошибка в handler %s:", func.__name__)

    def _build_message_filters(self, args: tuple, kwargs: dict) -> list[BaseFilter]:
        filters: list[BaseFilter] = []
        for arg in args:
            if isinstance(arg, str):
                filters.append(CommandFilter(arg) if arg.startswith("/") else TextFilter(arg))
            elif isinstance(arg, BaseFilter):
                filters.append(arg)
            else:
                raise TypeError(
                    f"Неподдерживаемый тип фильтра: {type(arg).__name__}. "
                    "Передавай str, BaseFilter или используй именованные аргументы: "
                    "regex=, text=, command="
                )

        known_kwargs = {"regex", "text", "command"}
        unknown = set(kwargs) - known_kwargs
        if unknown:
            raise TypeError(
                f"Неизвестные аргументы декоратора: {', '.join(sorted(unknown))}. "
                f"Допустимые: {', '.join(sorted(known_kwargs))}."
            )

        if "regex" in kwargs:
            filters.append(RegexFilter(kwargs["regex"]))
        if "text" in kwargs:
            filters.append(TextFilter(kwargs["text"]))
        if "command" in kwargs:
            filters.append(CommandFilter(kwargs["command"]))

        return filters
