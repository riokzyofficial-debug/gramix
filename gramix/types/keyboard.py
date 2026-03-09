from __future__ import annotations
from dataclasses import dataclass

from gramix.constants import MAX_CALLBACK_DATA_LENGTH
from gramix.exceptions import FilterError


@dataclass(slots=True)
class InlineButton:
    text: str
    callback_data: str | None = None
    url: str | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: str | None = None

    def to_dict(self) -> dict:
        btn: dict = {"text": self.text}
        if self.callback_data is not None:
            if len(self.callback_data) > MAX_CALLBACK_DATA_LENGTH:
                raise FilterError(
                    f"callback_data не должен превышать {MAX_CALLBACK_DATA_LENGTH} символов."
                )
            btn["callback_data"] = self.callback_data
        elif self.url is not None:
            btn["url"] = self.url
        elif self.switch_inline_query is not None:
            btn["switch_inline_query"] = self.switch_inline_query
        elif self.switch_inline_query_current_chat is not None:
            btn["switch_inline_query_current_chat"] = self.switch_inline_query_current_chat
        return btn


class Inline:
    def __init__(self) -> None:
        self._rows: list[list[InlineButton]] = [[]]

    def button(
        self,
        text: str,
        *,
        callback: str | None = None,
        url: str | None = None,
        switch_inline: str | None = None,
        switch_inline_current: str | None = None,
    ) -> Inline:
        self._rows[-1].append(
            InlineButton(
                text=text,
                callback_data=callback,
                url=url,
                switch_inline_query=switch_inline,
                switch_inline_query_current_chat=switch_inline_current,
            )
        )
        return self

    def row(self) -> Inline:
        if self._rows[-1]:
            self._rows.append([])
        return self

    def to_dict(self) -> dict:
        rows = [row for row in self._rows if row]
        return {"inline_keyboard": [[btn.to_dict() for btn in row] for row in rows]}


@dataclass(slots=True)
class ReplyButton:
    text: str
    request_contact: bool = False
    request_location: bool = False

    def to_dict(self) -> dict:
        btn: dict = {"text": self.text}
        if self.request_contact:
            btn["request_contact"] = True
        if self.request_location:
            btn["request_location"] = True
        return btn


class Reply:
    def __init__(
        self,
        *,
        resize: bool = True,
        one_time: bool = False,
        placeholder: str | None = None,
    ) -> None:
        self._rows: list[list[ReplyButton]] = [[]]
        self._resize = resize
        self._one_time = one_time
        self._placeholder = placeholder

    def button(self, text: str, *, contact: bool = False, location: bool = False) -> Reply:
        self._rows[-1].append(
            ReplyButton(text=text, request_contact=contact, request_location=location)
        )
        return self

    def row(self) -> Reply:
        if self._rows[-1]:
            self._rows.append([])
        return self

    def to_dict(self) -> dict:
        rows = [row for row in self._rows if row]
        result: dict = {
            "keyboard": [[btn.to_dict() for btn in row] for row in rows],
            "resize_keyboard": self._resize,
            "one_time_keyboard": self._one_time,
        }
        if self._placeholder:
            result["input_field_placeholder"] = self._placeholder
        return result


class RemoveKeyboard:
    def to_dict(self) -> dict:
        return {"remove_keyboard": True}
