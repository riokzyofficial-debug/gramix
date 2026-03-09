# Changelog

All notable changes to gramix are documented here.  
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.1.3] — 2025

### Added
- `SQLiteStorage` — persistent FSM storage that survives bot restarts
- `CallbackPrefixFilter` — route callbacks by prefix (`prefix="item:"`)
- `copy_message` / `forward_message` on `Bot`
- `pin_chat_message` / `unpin_chat_message` on `Bot`
- `set_message_reaction` on `Bot`
- `refresh_me()` / `async_refresh_me()` — force-refresh cached bot info
- `auto_split` parameter on `send_message` — automatically splits messages longer than 4096 characters
- `ChatMemberUpdated` type and `@rt.chat_member()` handler
- `InlineQueryResultGif`, `InlineQueryResultVideo`, `InlineQueryResultDocument`, `InlineQueryResultAudio` result types
- FastAPI + uvicorn webhook backend (`backend="fastapi"`)
- aiohttp webhook backend (`backend="aiohttp"`)
- Raw socket webhook backend (no extra dependencies)
- `py.typed` marker — full PEP 561 compliance
- Flood-control retry logic in `Bot._request` and `Bot._async_request`
- `POLLING_TIMEOUT` raised to 25 s — reduces idle HTTP traffic by ~12×

### Changed
- `FSMStorage` is now an alias for `MemoryStorage` (kept for backward compatibility)
- `MemoryStorage` evicts inactive contexts when size reaches 10 000 entries

### Fixed
- `MemoryStorage.delete` now calls `_reset()` instead of removing the key, preventing `KeyError` on rapid successive state transitions

---

## [0.1.2] — 2025

### Added
- `Dispatcher.run_async()` — native asyncio polling loop
- Async middleware support (`async def` middleware with `await call_next()`)
- Async lifecycle hooks (`@dp.on_startup` / `@dp.on_shutdown` support `async def`)
- `Bot.async_send_message` and corresponding async variants for all send methods
- `disable_preview` parameter on `send_message`

### Changed
- `DEFAULT_TIMEOUT` raised to 35 s to avoid httpx cutting long-poll connections
- Retry backoff is now exponential (`RETRY_BACKOFF = 2.0`)

---

## [0.1.1] — 2025

### Added
- `MemoryStorage` and FSM (`State`, `Step`, `StateContext`)
- `@rt.state()` handler decorator
- `ctx.next()`, `ctx.prev()`, `ctx.finish()` navigation
- `Inline` keyboard builder with `.button()`, `.row()`, `.url_button()`
- `Reply` keyboard builder with `resize` parameter
- `RemoveKeyboard` helper
- `F` filter shortcuts (`F.photo`, `F.document`, `F.text`, …)
- `RegexFilter` via `@rt.message(regex=r"...")`
- `InlineQuery` support with `@rt.inline()`
- `send_photo`, `send_video`, `send_audio`, `send_voice`, `send_document`, `send_sticker` on `Bot`
- `download_file` on `Bot`
- `send_chat_action` on `Bot`
- Middleware system (`@dp.middleware`)
- Lifecycle hooks (`@dp.on_startup`, `@dp.on_shutdown`)
- `load_env()` — zero-dependency `.env` loader
- `ParseMode` constants (`HTML`, `MARKDOWN`, `MARKDOWN_LEGACY`)
- Global `parse_mode` on `Bot` — inherited by all send/edit calls

---

## [0.1.0] — 2025

### Added
- Initial release
- `Bot` with `send_message`, `edit_message_text`, `delete_message`, `answer_callback_query`
- `Dispatcher` with long-polling loop
- `Router` with `@rt.message()` and `@rt.callback()` decorators
- `CommandFilter` and `TextFilter`
- `CallbackQuery` type
- `Message` type with `answer()` and `reply()` helpers
- `User` and `Chat` types
