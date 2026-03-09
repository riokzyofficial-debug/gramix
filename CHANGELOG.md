# Changelog

All notable changes to gramix are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gramix uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.3] — 2026-03-09

### Added
- `auto_split` parameter on `Bot.send_message()` — automatically splits messages longer than 4096 characters into multiple sends
- `copy_message()` method on `Bot` — copies a message without the forward header
- `set_message_reaction()` method on `Bot` — sets an emoji reaction on a message
- `refresh_me()` method on `Bot` — force-refreshes the cached `getMe` result
- `unpin_chat_message()` method on `Bot`
- `restrict_chat_member()` method on `Bot`
- `leave_chat()` method on `Bot`
- `get_chat_members_count()` method on `Bot`
- `send_chat_action()` method on `Bot`
- FastAPI webhook backend — `dp.run(webhook=True, backend="fastapi")`
- aiohttp webhook backend — `dp.run(webhook=True, backend="aiohttp")`
- Raw socket webhook backend (built-in, no extra dependencies)
- `SQLiteStorage` — persistent FSM storage backed by SQLite
- `FSMStorage` alias for `MemoryStorage` (backward-compatible)
- `ctx.prev()` on `StateContext` — navigate backward in FSM flows
- `ctx.matches(step)` on `StateContext` — check current step without string comparison
- `switch_inline` and `switch_inline_current` button types on `Inline`
- `placeholder` parameter on `Reply` keyboard
- `contact` and `location` button types on `Reply`
- `CallbackPrefixFilter` — exported in top-level `gramix` namespace
- `InlineQueryResultGif`, `InlineQueryResultVideo`, `InlineQueryResultDocument`, `InlineQueryResultAudio` result types
- `Dispatcher._print_banner()` — startup info log with version, bot username, mode, and timestamp
- `drop_pending` parameter on `dp.run()` and `dp.run_async()` — skip stale updates on startup
- Async variants for all `Bot` methods: `async_send_message`, `async_get_me`, etc.
- Async `Dispatcher.run_async()` polling mode
- Async lifecycle hooks (`on_startup`, `on_shutdown`) support both `def` and `async def`
- `py.typed` marker for PEP 561 compliance

### Changed
- `MemoryStorage` now evicts inactive contexts when the pool exceeds 10,000 entries to prevent unbounded memory growth
- Polling loop moved to a daemon thread; `dp.run()` blocks on `thread.join()` instead of a busy loop
- `POLLING_TIMEOUT` increased from 5 s to 25 s (recommended Telegram value); `DEFAULT_TIMEOUT` set to 35 s to avoid httpx cutting the connection
- `SQLiteStorage` uses `INSERT OR REPLACE` (`ON CONFLICT DO UPDATE`) for atomic upserts
- Middleware `call_next` in async mode is now a proper coroutine; sync middlewares in an async chain are wrapped transparently

### Fixed
- `CommandFilter` now correctly strips `@botname` suffixes from commands
- `StateContext.set()` raises `FSMError` for uninitialised `Step` instances instead of `AttributeError`
- `Inline.row()` silently ignores empty rows instead of adding blank keyboard rows
- `Reply.row()` behaves consistently with `Inline.row()`
- Lifecycle handlers that raise exceptions no longer crash the bot startup/shutdown sequence

---

## [0.1.2] — 2026-03-08

### Added
- Initial release on PyPI
- `Bot`, `Dispatcher`, `Router` core components
- Synchronous polling via `dp.run()`
- `@rt.message()`, `@rt.callback()`, `@rt.state()`, `@rt.inline()`, `@rt.chat_member()` decorators
- `F` filter shortcuts: `F.text`, `F.photo`, `F.document`, `F.video`, `F.voice`, `F.sticker`, `F.audio`, `F.reply`, `F.forward`, `F.private`, `F.group`
- `CommandFilter`, `TextFilter`, `RegexFilter`, `CallbackFilter`
- `Inline`, `Reply`, `RemoveKeyboard` keyboard builders
- `State`, `Step`, `MemoryStorage` FSM components
- `MiddlewareManager` with `call_next` chain
- `load_env()` for `.env` file loading
- `ParseMode` with `HTML`, `MARKDOWN`, `MARKDOWN_LEGACY` constants
- HTML and MarkdownV2 parse mode support
- Typed message objects: `Message`, `User`, `Chat`, `CallbackQuery`, `InlineQuery`, `ChatMemberUpdated`
- Media types: `PhotoSize`, `Document`, `Audio`, `Video`, `Voice`, `Sticker`
- Exception hierarchy: `GramixError`, `TokenError`, `TelegramAPIError`, `RetryAfterError`, `NetworkError`, `MessageError`, `FSMError`, `FilterError`, `MiddlewareError`, `WebhookError`, `FileError`
- `on_startup` and `on_shutdown` lifecycle hooks
- Automatic retry with exponential back-off on `RetryAfterError` (flood control)

---

## Versioning policy

gramix uses Semantic Versioning. Until version `1.0.0`, minor version bumps (`0.x.0`) may include breaking changes. Patch bumps (`0.x.y`) are backwards-compatible bug fixes and additions only.
