from __future__ import annotations
import asyncio
import logging
import time
from typing import Any

import httpx

from gramix.constants import (
    API_BASE_URL,
    API_FILE_URL,
    DEFAULT_TIMEOUT,
    MAX_MESSAGE_LENGTH,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
    RETRY_BACKOFF,
    TOKEN_ENV_KEY,
    _SENTINEL,
)
from gramix.env import get_token
from gramix.exceptions import FileError, NetworkError, RetryAfterError, TelegramAPIError, TokenError
from gramix.types.keyboard import Inline, Reply, RemoveKeyboard
from gramix.types.message import Message
from gramix.types.user import User

logger = logging.getLogger(__name__)


class Bot:
    def __init__(
        self,
        token: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        parse_mode: str | None = None,
    ) -> None:
        resolved_token = token or get_token()
        if not resolved_token:
            raise TokenError(
                f"Токен не передан и не найден в '{TOKEN_ENV_KEY}'. "
                "Получи токен у @BotFather."
            )
        self._token = resolved_token
        self._timeout = timeout
        self._default_parse_mode = parse_mode
        self._me: User | None = None
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def __repr__(self) -> str:
        hint = f"{self._token[:8]}...{self._token[-4:]}"
        return f"<Bot token={hint}>"

    def _build_url(self, method: str) -> str:
        return API_BASE_URL.format(token=self._token, method=method)

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(timeout=self._timeout)
        return self._sync_client

    def _parse_response(self, response: httpx.Response) -> Any:
        data = response.json()
        if not data.get("ok"):
            code = data.get("error_code", 0)
            description = data.get("description", "Unknown error")
            if code == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 30)
                raise RetryAfterError(retry_after)
            raise TelegramAPIError(code, description)
        return data["result"]

    def _request(self, method: str, payload: dict) -> Any:
        url = self._build_url(method)
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        delay = RETRY_DELAY
        last_retry_after: RetryAfterError | None = None

        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                response = self._get_sync_client().post(url, json=clean_payload)
                return self._parse_response(response)
            except RetryAfterError as e:
                last_retry_after = e
                logger.warning("Flood control: ждём %ds.", e.retry_after)
                time.sleep(e.retry_after)
            except TelegramAPIError:
                raise
            except httpx.TransportError as e:
                if attempt == RETRY_ATTEMPTS:
                    raise NetworkError(f"Сетевая ошибка: {e}") from e
                logger.warning("Сетевая ошибка (попытка %d/%d): %s", attempt, RETRY_ATTEMPTS, e)
                time.sleep(delay)
                delay *= RETRY_BACKOFF

        if last_retry_after is not None:
            raise last_retry_after
        raise NetworkError(f"Запрос {method} не выполнен после {RETRY_ATTEMPTS} попыток.")

    async def _async_request(self, method: str, payload: dict) -> Any:
        url = self._build_url(method)
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        delay = RETRY_DELAY
        last_retry_after: RetryAfterError | None = None

        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=self._timeout)

        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                response = await self._async_client.post(url, json=clean_payload)
                return self._parse_response(response)
            except RetryAfterError as e:
                last_retry_after = e
                logger.warning("Flood control: ждём %ds.", e.retry_after)
                await asyncio.sleep(e.retry_after)
            except TelegramAPIError:
                raise
            except httpx.TransportError as e:
                if attempt == RETRY_ATTEMPTS:
                    raise NetworkError(f"Сетевая ошибка: {e}") from e
                logger.warning("Сетевая ошибка (попытка %d/%d): %s", attempt, RETRY_ATTEMPTS, e)
                await asyncio.sleep(delay)
                delay *= RETRY_BACKOFF

        if last_retry_after is not None:
            raise last_retry_after
        raise NetworkError(f"Запрос {method} не выполнен после {RETRY_ATTEMPTS} попыток.")

    def _keyboard_dict(self, keyboard: Inline | Reply | RemoveKeyboard | None) -> dict | None:
        return keyboard.to_dict() if keyboard is not None else None

    def _effective_parse_mode(self, parse_mode: Any) -> str | None:
        return self._default_parse_mode if parse_mode is _SENTINEL else parse_mode

    def get_me(self) -> User:
        if self._me is None:
            self._me = User.from_dict(self._request("getMe", {}))
        return self._me

    def refresh_me(self) -> User:
        """Принудительно обновить кэш данных бота (имя/username можно менять через BotFather)."""
        self._me = User.from_dict(self._request("getMe", {}))
        return self._me

    async def async_get_me(self) -> User:
        if self._me is None:
            self._me = User.from_dict(await self._async_request("getMe", {}))
        return self._me

    async def async_refresh_me(self) -> User:
        """Принудительно обновить кэш данных бота (async-версия)."""
        self._me = User.from_dict(await self._async_request("getMe", {}))
        return self._me

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_to_message_id: int | None = None,
        keyboard: Inline | Reply | RemoveKeyboard | None = None,
        parse_mode: str | None = _SENTINEL,
        disable_preview: bool = False,
        auto_split: bool = False,
    ) -> Message:
        if auto_split and len(text) > MAX_MESSAGE_LENGTH:
            chunks = [text[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
            last: Message | None = None
            for chunk in chunks:
                last = self.send_message(
                    chat_id, chunk,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=parse_mode,
                    disable_preview=disable_preview,
                )
            if last is None:
                raise ValueError("auto_split: текст пустой после разбивки.")
            return last

        data = self._request("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
            "reply_markup": self._keyboard_dict(keyboard),
            "parse_mode": self._effective_parse_mode(parse_mode),
            "disable_web_page_preview": disable_preview if disable_preview else None,
        })
        return Message.from_dict(data, self)

    async def async_send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_to_message_id: int | None = None,
        keyboard: Inline | Reply | RemoveKeyboard | None = None,
        parse_mode: str | None = _SENTINEL,
        disable_preview: bool = False,
        auto_split: bool = False,
    ) -> Message:
        if auto_split and len(text) > MAX_MESSAGE_LENGTH:
            chunks = [text[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
            last: Message | None = None
            for chunk in chunks:
                last = await self.async_send_message(
                    chat_id, chunk,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=parse_mode,
                    disable_preview=disable_preview,
                )
            if last is None:
                raise ValueError("auto_split: текст пустой после разбивки.")
            return last

        data = await self._async_request("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
            "reply_markup": self._keyboard_dict(keyboard),
            "parse_mode": self._effective_parse_mode(parse_mode),
            "disable_web_page_preview": disable_preview if disable_preview else None,
        })
        return Message.from_dict(data, self)

    def forward_message(
        self,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
        *,
        disable_notification: bool = False,
    ) -> Message:
        data = self._request("forwardMessage", {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification if disable_notification else None,
        })
        return Message.from_dict(data, self)

    def copy_message(
        self,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
        *,
        caption: str | None = None,
        parse_mode: str | None = _SENTINEL,
        keyboard: Inline | Reply | None = None,
    ) -> int:
        data = self._request("copyMessage", {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "caption": caption,
            "parse_mode": self._effective_parse_mode(parse_mode),
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return int(data["message_id"])

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        *,
        keyboard: Inline | None = None,
        parse_mode: str | None = _SENTINEL,
    ) -> Message:
        data = self._request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": self._keyboard_dict(keyboard),
            "parse_mode": self._effective_parse_mode(parse_mode),
        })
        return Message.from_dict(data, self)

    def edit_message_keyboard(
        self,
        chat_id: int | str,
        message_id: int,
        keyboard: Inline | None,
    ) -> bool:
        return self._request("editMessageReplyMarkup", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": self._keyboard_dict(keyboard),
        })

    def delete_message(self, chat_id: int | str, message_id: int) -> bool:
        return self._request("deleteMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    def pin_chat_message(
        self,
        chat_id: int | str,
        message_id: int,
        *,
        disable_notification: bool = False,
    ) -> bool:
        return self._request("pinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification if disable_notification else None,
        })

    def unpin_chat_message(self, chat_id: int | str, message_id: int) -> bool:
        return self._request("unpinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    def set_message_reaction(
        self,
        chat_id: int | str,
        message_id: int,
        reaction: str,
        *,
        is_big: bool = False,
    ) -> bool:
        return self._request("setMessageReaction", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": reaction}],
            "is_big": is_big if is_big else None,
        })

    def send_photo(
        self,
        chat_id: int | str,
        photo: str,
        *,
        caption: str | None = None,
        keyboard: Inline | Reply | None = None,
        parse_mode: str | None = _SENTINEL,
    ) -> Message:
        data = self._request("sendPhoto", {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "reply_markup": self._keyboard_dict(keyboard),
            "parse_mode": self._effective_parse_mode(parse_mode),
        })
        return Message.from_dict(data, self)

    def send_video(
        self,
        chat_id: int | str,
        video: str,
        *,
        caption: str | None = None,
        duration: int | None = None,
        width: int | None = None,
        height: int | None = None,
        keyboard: Inline | Reply | None = None,
        parse_mode: str | None = _SENTINEL,
    ) -> Message:
        data = self._request("sendVideo", {
            "chat_id": chat_id,
            "video": video,
            "caption": caption,
            "duration": duration,
            "width": width,
            "height": height,
            "reply_markup": self._keyboard_dict(keyboard),
            "parse_mode": self._effective_parse_mode(parse_mode),
        })
        return Message.from_dict(data, self)

    def send_audio(
        self,
        chat_id: int | str,
        audio: str,
        *,
        caption: str | None = None,
        duration: int | None = None,
        performer: str | None = None,
        title: str | None = None,
        keyboard: Inline | Reply | None = None,
    ) -> Message:
        data = self._request("sendAudio", {
            "chat_id": chat_id,
            "audio": audio,
            "caption": caption,
            "duration": duration,
            "performer": performer,
            "title": title,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def send_voice(
        self,
        chat_id: int | str,
        voice: str,
        *,
        caption: str | None = None,
        duration: int | None = None,
    ) -> Message:
        data = self._request("sendVoice", {
            "chat_id": chat_id,
            "voice": voice,
            "caption": caption,
            "duration": duration,
        })
        return Message.from_dict(data, self)

    def send_document(
        self,
        chat_id: int | str,
        document: str,
        *,
        caption: str | None = None,
        keyboard: Inline | Reply | None = None,
    ) -> Message:
        data = self._request("sendDocument", {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def send_sticker(self, chat_id: int | str, sticker: str) -> Message:
        data = self._request("sendSticker", {"chat_id": chat_id, "sticker": sticker})
        return Message.from_dict(data, self)

    def send_chat_action(self, chat_id: int | str, action: str) -> bool:
        return self._request("sendChatAction", {"chat_id": chat_id, "action": action})

    def get_file(self, file_id: str) -> dict:
        return self._request("getFile", {"file_id": file_id})

    def download_file(self, file_id: str) -> bytes:
        file_info = self.get_file(file_id)
        file_path = file_info.get("file_path")
        if not file_path:
            raise FileError("Файл не найден или недоступен для скачивания.")
        url = API_FILE_URL.format(token=self._token, path=file_path)
        response = self._get_sync_client().get(url)
        if response.status_code != 200:
            raise FileError(f"Не удалось скачать файл: HTTP {response.status_code}")
        return response.content

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        *,
        show_alert: bool = False,
        url: str | None = None,
        cache_time: int = 0,
    ) -> bool:
        return self._request("answerCallbackQuery", {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert if show_alert else None,
            "url": url,
            "cache_time": cache_time if cache_time else None,
        })

    def answer_inline_query(
        self,
        inline_query_id: str,
        results: list[dict],
        *,
        cache_time: int = 300,
        is_personal: bool = False,
        next_offset: str | None = None,
    ) -> bool:
        return self._request("answerInlineQuery", {
            "inline_query_id": inline_query_id,
            "results": results,
            "cache_time": cache_time,
            "is_personal": is_personal if is_personal else None,
            "next_offset": next_offset,
        })

    def get_chat(self, chat_id: int | str) -> dict:
        return self._request("getChat", {"chat_id": chat_id})

    def get_chat_member(self, chat_id: int | str, user_id: int) -> dict:
        return self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def get_chat_members_count(self, chat_id: int | str) -> int:
        return self._request("getChatMemberCount", {"chat_id": chat_id})

    def ban_chat_member(
        self,
        chat_id: int | str,
        user_id: int,
        *,
        until_date: int | None = None,
    ) -> bool:
        return self._request("banChatMember", {
            "chat_id": chat_id,
            "user_id": user_id,
            "until_date": until_date,
        })

    def unban_chat_member(self, chat_id: int | str, user_id: int) -> bool:
        return self._request("unbanChatMember", {
            "chat_id": chat_id,
            "user_id": user_id,
            "only_if_banned": True,
        })

    def restrict_chat_member(
        self,
        chat_id: int | str,
        user_id: int,
        permissions: dict,
        *,
        until_date: int | None = None,
    ) -> bool:
        return self._request("restrictChatMember", {
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": permissions,
            "until_date": until_date,
        })

    def leave_chat(self, chat_id: int | str) -> bool:
        return self._request("leaveChat", {"chat_id": chat_id})

    def set_my_commands(
        self,
        commands: list[dict],
        *,
        scope: dict | None = None,
    ) -> bool:
        return self._request("setMyCommands", {
            "commands": commands,
            "scope": scope,
        })

    def delete_my_commands(self) -> bool:
        return self._request("deleteMyCommands", {})

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
    ) -> list[dict]:
        return self._request("getUpdates", {
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": allowed_updates,
        })

    async def async_get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
    ) -> list[dict]:
        return await self._async_request("getUpdates", {
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": allowed_updates,
        })

    def set_webhook(
        self,
        url: str,
        *,
        secret_token: str | None = None,
        max_connections: int = 40,
        allowed_updates: list[str] | None = None,
    ) -> bool:
        return self._request("setWebhook", {
            "url": url,
            "secret_token": secret_token,
            "max_connections": max_connections,
            "allowed_updates": allowed_updates,
        })

    def delete_webhook(self) -> bool:
        return self._request("deleteWebhook", {})

    def get_webhook_info(self) -> dict:
        return self._request("getWebhookInfo", {})

    def send_poll(
        self,
        chat_id: int | str,
        question: str,
        options: list[str],
        *,
        is_anonymous: bool = True,
        poll_type: str = "regular",
        allows_multiple_answers: bool = False,
        correct_option_id: int | None = None,
        explanation: str | None = None,
        explanation_parse_mode: str | None = _SENTINEL,
        open_period: int | None = None,
        close_date: int | None = None,
        is_closed: bool = False,
        keyboard: Inline | Reply | RemoveKeyboard | None = None,
    ) -> Message:
        from gramix.types.poll import Poll as _Poll
        data = self._request("sendPoll", {
            "chat_id": chat_id,
            "question": question,
            "options": [{"text": o} for o in options],
            "is_anonymous": is_anonymous,
            "type": poll_type,
            "allows_multiple_answers": (
                allows_multiple_answers if poll_type == "regular" else None
            ),
            "correct_option_id": correct_option_id,
            "explanation": explanation,
            "explanation_parse_mode": self._effective_parse_mode(explanation_parse_mode),
            "open_period": open_period,
            "close_date": close_date,
            "is_closed": is_closed if is_closed else None,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def stop_poll(
        self,
        chat_id: int | str,
        message_id: int,
        *,
        keyboard: Inline | None = None,
    ) -> "Poll":
        from gramix.types.poll import Poll
        data = self._request("stopPoll", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Poll.from_dict(data)

    def send_location(
        self,
        chat_id: int | str,
        latitude: float,
        longitude: float,
        *,
        horizontal_accuracy: float | None = None,
        live_period: int | None = None,
        heading: int | None = None,
        proximity_alert_radius: int | None = None,
        keyboard: Inline | Reply | RemoveKeyboard | None = None,
    ) -> Message:
        from gramix.types.location import Location
        data = self._request("sendLocation", {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "horizontal_accuracy": horizontal_accuracy,
            "live_period": live_period,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def send_venue(
        self,
        chat_id: int | str,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        *,
        foursquare_id: str | None = None,
        foursquare_type: str | None = None,
        google_place_id: str | None = None,
        google_place_type: str | None = None,
        keyboard: Inline | Reply | RemoveKeyboard | None = None,
    ) -> Message:
        data = self._request("sendVenue", {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            "foursquare_id": foursquare_id,
            "foursquare_type": foursquare_type,
            "google_place_id": google_place_id,
            "google_place_type": google_place_type,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def edit_message_live_location(
        self,
        chat_id: int | str,
        message_id: int,
        latitude: float,
        longitude: float,
        *,
        horizontal_accuracy: float | None = None,
        heading: int | None = None,
        proximity_alert_radius: int | None = None,
        keyboard: Inline | None = None,
    ) -> Message:
        data = self._request("editMessageLiveLocation", {
            "chat_id": chat_id,
            "message_id": message_id,
            "latitude": latitude,
            "longitude": longitude,
            "horizontal_accuracy": horizontal_accuracy,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def stop_message_live_location(
        self,
        chat_id: int | str,
        message_id: int,
        *,
        keyboard: Inline | None = None,
    ) -> Message:
        data = self._request("stopMessageLiveLocation", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def send_invoice(
        self,
        chat_id: int | str,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: list,
        *,
        max_tip_amount: int | None = None,
        suggested_tip_amounts: list[int] | None = None,
        start_parameter: str | None = None,
        provider_data: str | None = None,
        photo_url: str | None = None,
        photo_size: int | None = None,
        photo_width: int | None = None,
        photo_height: int | None = None,
        need_name: bool = False,
        need_phone_number: bool = False,
        need_email: bool = False,
        need_shipping_address: bool = False,
        send_phone_number_to_provider: bool = False,
        send_email_to_provider: bool = False,
        is_flexible: bool = False,
        protect_content: bool = False,
        keyboard: Inline | None = None,
    ) -> Message:
        prices_raw = [
            p.to_dict() if hasattr(p, "to_dict") else p for p in prices
        ]
        data = self._request("sendInvoice", {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": provider_token,
            "currency": currency,
            "prices": prices_raw,
            "max_tip_amount": max_tip_amount,
            "suggested_tip_amounts": suggested_tip_amounts,
            "start_parameter": start_parameter,
            "provider_data": provider_data,
            "photo_url": photo_url,
            "photo_size": photo_size,
            "photo_width": photo_width,
            "photo_height": photo_height,
            "need_name": need_name if need_name else None,
            "need_phone_number": need_phone_number if need_phone_number else None,
            "need_email": need_email if need_email else None,
            "need_shipping_address": need_shipping_address if need_shipping_address else None,
            "send_phone_number_to_provider": send_phone_number_to_provider if send_phone_number_to_provider else None,
            "send_email_to_provider": send_email_to_provider if send_email_to_provider else None,
            "is_flexible": is_flexible if is_flexible else None,
            "protect_content": protect_content if protect_content else None,
            "reply_markup": self._keyboard_dict(keyboard),
        })
        return Message.from_dict(data, self)

    def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        *,
        error_message: str | None = None,
    ) -> bool:
        return self._request("answerPreCheckoutQuery", {
            "pre_checkout_query_id": pre_checkout_query_id,
            "ok": ok,
            "error_message": error_message,
        })

    def close(self) -> None:
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()

    async def async_close(self) -> None:
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
