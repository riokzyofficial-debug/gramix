# Changelog

All notable changes to gramix are documented here.  
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.1.6] — 2026-03-09

### Added
- `send_poll(chat_id, question, options, *, poll_type, is_anonymous, allows_multiple_answers, correct_option_id, explanation, open_period, close_date, is_closed, keyboard)` — send regular polls and quizzes
- `stop_poll(chat_id, message_id, *, keyboard)` — close an open poll; returns a typed `Poll` object
- `Poll`, `PollOption`, `PollAnswer` types in `gramix.types.poll`; all three exported from the top-level `gramix` package
- `PollAnswer.voter_chat` field — handles anonymous poll answers introduced in Bot API 7.3 (previously caused `KeyError`)
- `PollAnswer.retracted` property — `True` when `option_ids` is empty (user withdrew their vote)
- `poll` field on `Message` — populated when a message contains a forwarded poll
- `@rt.poll_answer()` decorator and `process_poll_answer` / `async_process_poll_answer` on `Router`
- `F.poll` filter — matches messages that contain a forwarded poll
- `F.quiz` filter — matches messages that contain a forwarded quiz
- `examples/poll_bot.py` — full working example covering all poll features

### Fixed
- `send_poll`: parameter renamed from `type` to `poll_type` — avoids shadowing the Python built-in `type`
- `stop_poll`: now returns a typed `Poll` instead of a raw `dict`, consistent with the rest of the Bot API

---

## [0.1.5] — 2026-03-09

### Changed
- README: all Table of Contents links replaced with absolute GitHub URLs — resolves 404 errors on PyPI
- README: added explicit repository link below the project description
- README: `file_id` placeholders in Sending Media examples replaced with `"<file_id>"` for clarity

---

## [0.1.4] — 2026-03-09

### Changed
- `pyproject.toml`: description updated from Russian placeholder to English (`"A fast, fully-typed Python framework for building Telegram bots."`)
- `pyproject.toml`: removed `License :: OSI Approved :: MIT License` classifier — superseded by the `license` field per PEP 639
- `pyproject.toml`: expanded `keywords` with `fsm`, `finite-state-machine`, `middleware`, `webhooks`, `typed`
- `pyproject.toml`: added missing classifiers — `Operating System :: OS Independent`, `Programming Language :: Python :: 3 :: Only`, `Topic :: Software Development :: Libraries :: Python Modules`, `Framework :: AsyncIO`
- `pyproject.toml`: added `Documentation` and `Changelog` URLs; renamed `Issues` to `Bug Tracker`
- `pyproject.toml`: added `black` and `mypy` to `[dev]` optional dependencies

---

## [0.1.3] — 2026-03-09

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

## [0.1.2] — 2026-03-09

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

## [0.1.1] — 2026-03-09

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

## [0.1.0] — 2026-03-09

### Added
- Initial release
- `Bot` with `send_message`, `edit_message_text`, `delete_message`, `answer_callback_query`
- `Dispatcher` with long-polling loop
- `Router` with `@rt.message()` and `@rt.callback()` decorators
- `CommandFilter` and `TextFilter`
- `CallbackQuery` type
- `Message` type with `answer()` and `reply()` helpers
- `User` and `Chat` types
