# API Reference

Complete reference for all public classes and methods in gramix.

---

## Bot

The HTTP client for the Telegram Bot API. One instance per process.

### Constructor

```python
Bot(
    token: str | None = None,
    *,
    timeout: float = 35.0,
    parse_mode: str | None = None,
)
```

`token` — bot token. If omitted, reads `BOT_TOKEN` from the environment.  
`timeout` — HTTP request timeout in seconds. Default accounts for the 25-second long-polling window.  
`parse_mode` — default parse mode applied to all send/edit calls when none is specified per call.

### Methods

**Identity**

| Method | Returns | Description |
|---|---|---|
| `get_me()` | `User` | Returns bot's User object (cached). |
| `refresh_me()` | `User` | Clears cache and fetches fresh bot data. |

**Sending messages**

| Method | Returns | Description |
|---|---|---|
| `send_message(chat_id, text, *, reply_to_message_id, keyboard, parse_mode, disable_preview, auto_split)` | `Message` | Send a text message. Set `auto_split=True` to split texts longer than 4096 characters automatically. |
| `send_photo(chat_id, photo, *, caption, keyboard, parse_mode)` | `Message` | Send a photo by `file_id` or URL. |
| `send_video(chat_id, video, *, caption, duration, width, height, keyboard, parse_mode)` | `Message` | Send a video. |
| `send_audio(chat_id, audio, *, caption, duration, performer, title, keyboard)` | `Message` | Send an audio file. |
| `send_voice(chat_id, voice, *, caption)` | `Message` | Send a voice message. |
| `send_document(chat_id, document, *, caption, keyboard)` | `Message` | Send a document. |
| `send_sticker(chat_id, sticker)` | `Message` | Send a sticker by `file_id`. |
| `send_chat_action(chat_id, action)` | `bool` | Send a chat action (e.g. `"typing"`, `"upload_photo"`). |

**Editing and deleting**

| Method | Returns | Description |
|---|---|---|
| `edit_message_text(chat_id, message_id, text, *, keyboard, parse_mode)` | `Message` | Edit message text and optionally its inline keyboard. |
| `edit_message_keyboard(chat_id, message_id, keyboard)` | `bool` | Edit only the inline keyboard without changing text. |
| `delete_message(chat_id, message_id)` | `bool` | Delete a message. |

**Forwarding and copying**

| Method | Returns | Description |
|---|---|---|
| `forward_message(chat_id, from_chat_id, message_id)` | `Message` | Forward a message (shows the forward header). |
| `copy_message(chat_id, from_chat_id, message_id, *, caption, parse_mode, keyboard)` | `int` | Copy a message without the forward header. Returns the new `message_id`. |

**Pinning**

| Method | Returns | Description |
|---|---|---|
| `pin_chat_message(chat_id, message_id, *, disable_notification)` | `bool` | Pin a message in a chat. |
| `unpin_chat_message(chat_id, message_id)` | `bool` | Unpin a specific message. |

**Reactions**

| Method | Returns | Description |
|---|---|---|
| `set_message_reaction(chat_id, message_id, reaction)` | `bool` | Set an emoji reaction on a message. |

**Files**

| Method | Returns | Description |
|---|---|---|
| `get_file(file_id)` | `dict` | Get file metadata from Telegram. |
| `download_file(file_id)` | `bytes` | Download a file and return its raw bytes. |

**Chat administration**

| Method | Returns | Description |
|---|---|---|
| `get_chat(chat_id)` | `dict` | Get raw chat information. |
| `get_chat_member(chat_id, user_id)` | `dict` | Get raw chat member info. |
| `get_chat_members_count(chat_id)` | `int` | Get the number of members in a chat. |
| `ban_chat_member(chat_id, user_id)` | `bool` | Ban a user from a chat. |
| `unban_chat_member(chat_id, user_id)` | `bool` | Unban a user. |
| `restrict_chat_member(chat_id, user_id, permissions)` | `bool` | Restrict a user's permissions. |
| `leave_chat(chat_id)` | `bool` | Leave a group or channel. |

**Commands**

| Method | Returns | Description |
|---|---|---|
| `set_my_commands(commands)` | `bool` | Set the bot's command list (shown in the Telegram menu). |
| `delete_my_commands()` | `bool` | Remove the bot's command list. |

**Callbacks and inline**

| Method | Returns | Description |
|---|---|---|
| `answer_callback_query(callback_query_id, text, *, show_alert)` | `bool` | Answer a callback query. `show_alert=True` shows a modal popup instead of a toast. |
| `answer_inline_query(inline_query_id, results, *, cache_time)` | `bool` | Answer an inline query with a list of results. |

**Webhooks**

| Method | Returns | Description |
|---|---|---|
| `set_webhook(url)` | `bool` | Register a webhook URL with Telegram. |
| `delete_webhook()` | `bool` | Remove the registered webhook. |
| `get_webhook_info()` | `dict` | Get current webhook status and metadata. |

**Lifecycle**

| Method | Returns | Description |
|---|---|---|
| `close()` | `None` | Close the synchronous HTTP client. |
| `async_close()` | `None` | Close the asynchronous HTTP client (async). |

---

## Dispatcher

Manages the update loop, middleware, and lifecycle hooks.

```python
Dispatcher(bot: Bot)
```

| Method / Decorator | Description |
|---|---|
| `include(router)` | Register a router. Routers are checked in inclusion order. |
| `run(*, webhook, host, port, webhook_url, backend, drop_pending)` | Start synchronous polling or webhook server. |
| `run_async(*, drop_pending)` | Start asynchronous polling via `asyncio.run()`. |
| `@dp.middleware` | Register a middleware function. |
| `@dp.on_startup` | Register a startup lifecycle hook. |
| `@dp.on_shutdown` | Register a shutdown lifecycle hook. |

---

## Router

Declares message, callback, and FSM state handlers.

```python
Router(storage: BaseStorage | None = None)
```

If `storage` is omitted, `MemoryStorage` is used.

| Decorator | Arguments | Description |
|---|---|---|
| `@rt.message(*args, **kwargs)` | Strings, `BaseFilter` instances, `regex=`, `text=`, `command=` | Register a message handler. |
| `@rt.callback(*data, prefix=None)` | Exact data strings or a prefix string | Register a callback query handler. |
| `@rt.state(step)` | A `Step` instance | Register an FSM state handler. Receives `(msg, ctx)`. |
| `@rt.inline()` | None | Register an inline query handler. |
| `@rt.chat_member()` | None | Register a chat member update handler. |

---

## ParseMode

```python
ParseMode.HTML             # "HTML"
ParseMode.MARKDOWN         # "MarkdownV2"
ParseMode.MARKDOWN_LEGACY  # "Markdown"
```

---

## F — Filter shortcuts

| Attribute | Type | Matches when |
|---|---|---|
| `F.text` | `HasTextFilter` | Message has non-empty text |
| `F.photo` | `HasPhotoFilter` | Message contains a photo |
| `F.document` | `HasDocumentFilter` | Message contains a document |
| `F.video` | `HasVideoFilter` | Message contains a video |
| `F.audio` | `HasAudioFilter` | Message contains audio |
| `F.voice` | `HasVoiceFilter` | Message contains a voice message |
| `F.sticker` | `HasStickerFilter` | Message contains a sticker |
| `F.reply` | `IsReplyFilter` | Message is a reply |
| `F.forward` | `IsForwardFilter` | Message is a forward |
| `F.private` | `PrivateChatFilter` | Chat type is private |
| `F.group` | `GroupChatFilter` | Chat type is group or supergroup |

---

## Inline

```python
Inline()
    .button(text, *, callback=None, url=None, switch_inline=None, switch_inline_current=None) → Inline
    .row() → Inline
    .to_dict() → dict
```

---

## Reply

```python
Reply(*, resize=True, one_time=False, placeholder=None)
    .button(text, *, contact=False, location=False) → Reply
    .row() → Reply
    .to_dict() → dict
```

---

## RemoveKeyboard

```python
RemoveKeyboard()
    .to_dict() → {"remove_keyboard": True}
```

---

## FSM

### State and Step

```python
class MyState(State):
    step_one = Step()
    step_two = Step()
```

### StateContext

| Member | Description |
|---|---|
| `ctx.is_active` | `True` if the user is in an active state |
| `ctx.current` | Current step as `"ClassName.step_name"` or `None` |
| `ctx.data` | Per-user mutable dict, persists for the flow's lifetime |
| `ctx.set(step)` | Set the user to a specific step |
| `ctx.next()` | Advance one step; returns `False` and calls `finish()` at the last step |
| `ctx.prev()` | Go back one step; returns `False` at the first step |
| `ctx.finish()` | Clear state and data |
| `ctx.matches(step)` | Returns `True` if current step equals the given step |

### MemoryStorage

In-process storage. Data is lost on bot restart. Thread-safe. Automatically evicts inactive contexts when the pool exceeds 10,000 entries.

### SQLiteStorage

```python
SQLiteStorage(path: str = "gramix_fsm.db")
```

Persistent storage backed by a local SQLite file. Thread-safe. Survives bot restarts. State and data are serialised as JSON.

---

## Exceptions

All exceptions inherit from `GramixError`, which inherits from `Exception`.

| Exception | When raised |
|---|---|
| `TokenError` | Bot token is missing or invalid |
| `TelegramAPIError(code, description)` | Telegram API returned an error response |
| `RetryAfterError(retry_after)` | Rate limit hit (HTTP 429). `retry_after` contains the wait time in seconds |
| `NetworkError` | HTTP request failed (connection error, timeout) |
| `MessageError` | Message text or caption exceeds Telegram's length limits |
| `FSMError` | FSM operation failed (unregistered state, uninitialised step) |
| `FilterError` | `callback_data` exceeds 64-character limit |
| `WebhookError` | Webhook URL missing or backend dependency not installed |
| `FileError` | File download or upload failed |
