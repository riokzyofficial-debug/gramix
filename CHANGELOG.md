# Changelog

All notable changes to gramix are documented here.  
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.1.8] — 2026-03-10

> First official release on PyPI. Consolidates all development from 0.1.0–0.1.7 with polling performance improvements and full Telegram Bot API coverage.

### Added

**Polling performance**
- `_CHUNK`-based polling loop — each `getUpdates` cycle uses a short timeout, enabling fast bot shutdown (≤1 s in async mode, ≤3 s in sync mode)
- `http_timeout` parameter on `Bot._request` / `Bot._async_request` — httpx timeout now dynamically matches the long-poll timeout + 2 s buffer, eliminating stale connection hangs
- `threading.Event`-based stop signal in sync polling — all pauses are now interruptible, preventing delays on shutdown
- `DEFAULT_TIMEOUT` reduced to `10.0` s; `POLLING_TIMEOUT` reduced to `3` s

**Telegram Games API**
- `send_game(chat_id, game_short_name, *, keyboard)` — send a Telegram game
- `set_game_score(user_id, score, *, chat_id, message_id, inline_message_id, force, disable_edit_return)` — set a user's score in a game
- `get_game_high_scores(user_id, *, chat_id, message_id, inline_message_id)` — fetch the high score table; returns a list of `GameHighScore` objects
- `GameHighScore` type with fields `position`, `user` (`User`), `score`
- `game_short_name` field on `CallbackQuery` — populated when the user presses a Play button
- `@rt.game_callback()` decorator on `Router` — routes callback queries that carry `game_short_name`

**Rate Limiting**
- `ThrottlingMiddleware(rate, *, on_throttle)` — built-in per-user rate limiter; works in both sync and async mode; optional `on_throttle` callback invoked instead of silently dropping throttled messages

### Fixed
- `send_message` / `async_send_message`: `keyboard` parameter is now correctly forwarded in recursive calls when `auto_split=True`
- Webhook (raw backend): incoming requests are now validated against the `X-Telegram-Bot-Api-Secret-Token` header; mismatches return HTTP 403
- `Message.reply_photo` / `Message.reply_video`: `parse_mode` default changed from `None` to `_SENTINEL` — correctly inherits the bot's global `parse_mode`
- `Dispatcher._call_handlers`: replaced deprecated `asyncio.get_event_loop().run_until_complete()` with `asyncio.run()` (Python 3.10+)
- `SQLiteStorage`: added `close()` method and context manager support (`__enter__` / `__exit__`)
- `InlineButton.to_dict`: over-length `callback_data` now raises `ValueError` instead of the semantically incorrect `FilterError`
- `Router.process_chat_member` / `async_process_chat_member`: all registered handlers are now called, not only the first one
- `MemoryStorage.delete`: fixed memory leak — the user entry is now fully removed from the storage dict (the 0.1.3 fix only reset the state object without deleting the key)

---

## [0.1.7] — 2026-03-09

### Added

**Location & Venue**
- `send_location(chat_id, latitude, longitude, *, horizontal_accuracy, live_period, heading, proximity_alert_radius, keyboard)` — send a static or live location
- `send_venue(chat_id, latitude, longitude, title, address, *, foursquare_id, foursquare_type, google_place_id, google_place_type, keyboard)` — send a named place with address
- `edit_message_live_location(chat_id, message_id, latitude, longitude, ...)` — update a live location in-place
- `stop_message_live_location(chat_id, message_id, ...)` — stop a live location broadcast
- `Location` type — latitude, longitude, horizontal_accuracy, live_period, heading, proximity_alert_radius
- `Venue` type — location, title, address, foursquare_id, foursquare_type, google_place_id, google_place_type
- `location` and `venue` fields on `Message`
- `F.location` filter — matches messages that contain a location
- `F.venue` filter — matches messages that contain a venue
- `examples/location_bot.py` — full working example

**Payments**
- `send_invoice(chat_id, title, description, payload, provider_token, currency, prices, *, ...)` — send a Telegram payment invoice
- `answer_pre_checkout_query(pre_checkout_query_id, ok, *, error_message)` — confirm or reject payment before charging
- `PreCheckoutQuery` type with `amount_decimal` property
- `SuccessfulPayment` type with `amount_decimal` property
- `LabeledPrice` helper with `to_dict()`
- `OrderInfo` type for shipping details
- `@rt.pre_checkout_query()` decorator and `process_pre_checkout_query` / `async_process_pre_checkout_query` on `Router`
- `@rt.successful_payment()` decorator and `process_successful_payment` / `async_process_successful_payment` on `Router`
- `successful_payment` field on `Message`
- `examples/payment_bot.py` — full working example

**Badges**
- PyPI version badge is now fully dynamic — always shows the latest published version automatically

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
