from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gramix.types.message import Message
    from gramix.types.callback import CallbackQuery


class BaseFilter(ABC):
    @abstractmethod
    def check(self, update: object) -> bool:
        pass


class CommandFilter(BaseFilter):
    def __init__(self, *commands: str) -> None:
        self._commands = frozenset(cmd.lstrip("/").lower() for cmd in commands)

    def check(self, update: Message) -> bool:
        if not update.text or not update.text.startswith("/"):
            return False
        command = update.text.split()[0].lstrip("/").split("@")[0].lower()
        return command in self._commands


class TextFilter(BaseFilter):
    def __init__(self, *texts: str, case_sensitive: bool = False) -> None:
        self._case_sensitive = case_sensitive
        self._texts = frozenset(texts if case_sensitive else (t.lower() for t in texts))

    def check(self, update: Message) -> bool:
        if not update.text:
            return False
        text = update.text if self._case_sensitive else update.text.lower()
        return text in self._texts


class RegexFilter(BaseFilter):
    def __init__(self, pattern: str, flags: int = 0) -> None:
        self._pattern = re.compile(pattern, flags)

    def check(self, update: Message) -> bool:
        return bool(update.text and self._pattern.search(update.text))


class CallbackFilter(BaseFilter):
    def __init__(self, *data: str) -> None:
        self._data = frozenset(data)

    def check(self, update: CallbackQuery) -> bool:
        return update.data in self._data


class CallbackPrefixFilter(BaseFilter):
    def __init__(self, *prefixes: str) -> None:
        self._prefixes = tuple(prefixes)

    def check(self, update: CallbackQuery) -> bool:
        return bool(update.data and update.data.startswith(self._prefixes))


class HasPhotoFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.photo is not None


class HasDocumentFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.document is not None


class HasVideoFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.video is not None


class HasAudioFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.audio is not None


class HasVoiceFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.voice is not None


class HasStickerFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.sticker is not None


class HasTextFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return bool(update.text)


class IsForwardFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.forward_from is not None


class IsReplyFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.reply_to_message is not None


class ChatTypeFilter(BaseFilter):
    def __init__(self, *types: str) -> None:
        self._types = frozenset(types)

    def check(self, update: Message) -> bool:
        return update.chat.type.value in self._types


class PrivateChatFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.chat.is_private


class GroupChatFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.chat.is_group


class HasPollFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.poll is not None


class HasQuizFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.poll is not None and update.poll.poll_type == "quiz"


class HasLocationFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.location is not None


class HasVenueFilter(BaseFilter):
    def check(self, update: Message) -> bool:
        return update.venue is not None


class F:
    photo = HasPhotoFilter()
    document = HasDocumentFilter()
    video = HasVideoFilter()
    audio = HasAudioFilter()
    voice = HasVoiceFilter()
    sticker = HasStickerFilter()
    text = HasTextFilter()
    forward = IsForwardFilter()
    reply = IsReplyFilter()
    private = PrivateChatFilter()
    group = GroupChatFilter()
    poll = HasPollFilter()
    quiz = HasQuizFilter()
    location = HasLocationFilter()
    venue = HasVenueFilter()
