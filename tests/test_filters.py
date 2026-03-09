"""Tests for gramix.filters — no Telegram connection required."""
from gramix.filters import (
    CallbackPrefixFilter,
    CommandFilter,
    F,
    GroupChatFilter,
    HasDocumentFilter,
    HasPhotoFilter,
    HasTextFilter,
    PrivateChatFilter,
    RegexFilter,
    TextFilter,
)


# ---------------------------------------------------------------------------
# Minimal stubs — avoid importing heavy types that require a Bot instance
# ---------------------------------------------------------------------------

class _Chat:
    def __init__(self, chat_type: str) -> None:
        self.type = _ChatType(chat_type)
        self.is_private = chat_type == "private"
        self.is_group = chat_type in ("group", "supergroup")


class _ChatType:
    def __init__(self, value: str) -> None:
        self.value = value


class _Msg:
    def __init__(
        self,
        *,
        text: str | None = None,
        photo=None,
        document=None,
        chat_type: str = "private",
    ) -> None:
        self.text = text
        self.photo = photo
        self.document = document
        self.video = None
        self.audio = None
        self.voice = None
        self.sticker = None
        self.forward_from = None
        self.reply_to_message = None
        self.chat = _Chat(chat_type)


class _Callback:
    def __init__(self, data: str) -> None:
        self.data = data


# ---------------------------------------------------------------------------
# CommandFilter
# ---------------------------------------------------------------------------

def test_command_filter_matches_exact():
    f = CommandFilter("/start")
    assert f.check(_Msg(text="/start"))


def test_command_filter_matches_with_bot_mention():
    f = CommandFilter("/start")
    assert f.check(_Msg(text="/start@my_bot"))


def test_command_filter_case_insensitive():
    f = CommandFilter("/START")
    assert f.check(_Msg(text="/start"))


def test_command_filter_no_match_plain_text():
    f = CommandFilter("/start")
    assert not f.check(_Msg(text="start"))


def test_command_filter_no_match_other_command():
    f = CommandFilter("/start")
    assert not f.check(_Msg(text="/help"))


def test_command_filter_no_text():
    f = CommandFilter("/start")
    assert not f.check(_Msg())


# ---------------------------------------------------------------------------
# TextFilter
# ---------------------------------------------------------------------------

def test_text_filter_exact_match():
    f = TextFilter("ping")
    assert f.check(_Msg(text="ping"))


def test_text_filter_case_insensitive_default():
    f = TextFilter("Ping")
    assert f.check(_Msg(text="ping"))


def test_text_filter_case_sensitive():
    f = TextFilter("Ping", case_sensitive=True)
    assert not f.check(_Msg(text="ping"))
    assert f.check(_Msg(text="Ping"))


def test_text_filter_multiple_values():
    f = TextFilter("yes", "no", "maybe")
    assert f.check(_Msg(text="yes"))
    assert f.check(_Msg(text="no"))
    assert not f.check(_Msg(text="unsure"))


def test_text_filter_no_text():
    f = TextFilter("ping")
    assert not f.check(_Msg())


# ---------------------------------------------------------------------------
# RegexFilter
# ---------------------------------------------------------------------------

def test_regex_filter_matches():
    f = RegexFilter(r"^\d{4}$")
    assert f.check(_Msg(text="1234"))


def test_regex_filter_no_match():
    f = RegexFilter(r"^\d{4}$")
    assert not f.check(_Msg(text="123"))
    assert not f.check(_Msg(text="hello"))


def test_regex_filter_partial_match():
    f = RegexFilter(r"\d+")
    assert f.check(_Msg(text="abc 42 xyz"))


def test_regex_filter_no_text():
    f = RegexFilter(r"\d+")
    assert not f.check(_Msg())


# ---------------------------------------------------------------------------
# CallbackPrefixFilter
# ---------------------------------------------------------------------------

def test_callback_prefix_matches():
    f = CallbackPrefixFilter("item:")
    assert f.check(_Callback("item:42"))


def test_callback_prefix_no_match():
    f = CallbackPrefixFilter("item:")
    assert not f.check(_Callback("menu:back"))


def test_callback_prefix_multiple_prefixes():
    f = CallbackPrefixFilter("item:", "page:")
    assert f.check(_Callback("item:1"))
    assert f.check(_Callback("page:3"))
    assert not f.check(_Callback("vote:like"))


def test_callback_prefix_empty_data():
    f = CallbackPrefixFilter("item:")
    cb = _Callback("")
    assert not f.check(cb)


# ---------------------------------------------------------------------------
# F shortcuts (smoke tests)
# ---------------------------------------------------------------------------

def test_f_photo():
    assert F.photo.check(_Msg(photo=object()))
    assert not F.photo.check(_Msg())


def test_f_document():
    assert F.document.check(_Msg(document=object()))
    assert not F.document.check(_Msg())


def test_f_text():
    assert F.text.check(_Msg(text="hello"))
    assert not F.text.check(_Msg())


def test_f_private():
    assert F.private.check(_Msg(chat_type="private"))
    assert not F.private.check(_Msg(chat_type="group"))


def test_f_group():
    assert F.group.check(_Msg(chat_type="group"))
    assert F.group.check(_Msg(chat_type="supergroup"))
    assert not F.group.check(_Msg(chat_type="private"))
