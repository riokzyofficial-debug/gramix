# gramix

[![PyPI](https://img.shields.io/pypi/v/gramix?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/gramix)
[![Python](https://img.shields.io/pypi/pyversions/gramix?logo=python&logoColor=white)](https://pypi.org/project/gramix)
[![Downloads](https://img.shields.io/pypi/dm/gramix?color=brightgreen)](https://pypi.org/project/gramix)
[![License](https://img.shields.io/badge/license-MIT-informational)](https://github.com/riokzyofficial-debug/gramix/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![Typed](https://img.shields.io/badge/typing-typed-brightgreen?logo=mypy)](https://mypy-lang.org)
[![GitHub stars](https://img.shields.io/github/stars/riokzyofficial-debug/gramix?style=flat&logo=github)](https://github.com/riokzyofficial-debug/gramix/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/riokzyofficial-debug/gramix)](https://github.com/riokzyofficial-debug/gramix/issues)

A fast, clean, fully-typed Python framework for building Telegram bots. Supports synchronous and asynchronous execution, finite state machines, middleware, inline keyboards, webhooks, and file handling — with zero boilerplate.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Examples](#examples)
  - [Commands & Text Filters](#commands--text-filters)
  - [Reply Keyboards](#reply-keyboards)
  - [Inline Keyboards & Callbacks](#inline-keyboards--callbacks)
  - [Finite State Machine (FSM)](#finite-state-machine-fsm)
  - [SQLite FSM Storage](#sqlite-fsm-storage)
  - [Media Handling](#media-handling)
  - [Sending Media](#sending-media)
  - [File Download](#file-download)
  - [Middleware](#middleware)
  - [Inline Queries](#inline-queries)
  - [Chat Member Events](#chat-member-events)
  - [Polls & Quiz](#polls--quiz)
  - [Location & Venue](#location--venue)
  - [Payments](#payments)
  - [Parse Mode & HTML Formatting](#parse-mode--html-formatting)
  - [Async Mode](#async-mode)
  - [Webhook Mode](#webhook-mode)
  - [Lifecycle Hooks](#lifecycle-hooks)
  - [Telegram Games](#telegram-games)
  - [Rate Limiting](#rate-limiting)
- [API Reference](#api-reference)
- [License](#license)

---

## Installation

```bash
pip install gramix
```

Optional extras for webhook support:

```bash
pip install gramix[aiohttp]   # aiohttp webhook backend
pip install gramix[fastapi]   # FastAPI + uvicorn webhook backend
```

**Requirements:** Python 3.10+

---

## Quick Start

Create a `.env` file:

```env
BOT_TOKEN=your_token_here
```

Create `bot.py`:

```python
from gramix import Bot, Dispatcher, Router, load_env

load_env()

bot = Bot()
dp  = Dispatcher(bot)
rt  = Router()
dp.include(rt)

@rt.message("/start")
def on_start(msg):
    msg.answer(f"Hello, {msg.from_user.full_name}!")

dp.run()
```

```bash
python bot.py
```

---

## Core Concepts

**`Bot`** handles all direct Telegram API calls. Pass `parse_mode=ParseMode.HTML` once at initialization and every subsequent `answer()`, `reply()`, `edit()`, `send_photo()`, etc. will inherit it automatically — no need to repeat it per call.

**`Dispatcher`** drives the polling or webhook loop, dispatches incoming updates to routers, and manages middleware and lifecycle hooks.

**`Router`** declares handlers for messages, callbacks, inline queries, and FSM states. Multiple routers can be included in one dispatcher.

**`F`** is a filter shortcut object for common conditions: `F.photo`, `F.document`, `F.sticker`, `F.voice`, `F.text`, `F.reply`, `F.forward`, `F.private`, `F.group`.

**`State` / `Step`** define FSM flows. Steps are declared as class attributes and traversed with `ctx.next()`, `ctx.prev()`, or `ctx.finish()`.

---

## Examples

### Commands & Text Filters

```python
from gramix import Bot, Dispatcher, Router, load_env, F

load_env()
bot = Bot()
dp  = Dispatcher(bot)
rt  = Router()
dp.include(rt)

@rt.message("/start")
def on_start(msg):
    msg.answer("Welcome! Send me anything.")

@rt.message("/help")
def on_help(msg):
    msg.answer("Commands: /start, /help, /about")

@rt.message("/about")
def on_about(msg):
    msg.answer("gramix — Telegram bot framework.")

# Exact text match (case-insensitive by default)
@rt.message("ping")
def on_ping(msg):
    msg.answer("pong")

# Regex filter — matches any 4-digit number
@rt.message(regex=r"^\d{4}$")
def on_four_digits(msg):
    msg.answer(f"You sent a 4-digit number: {msg.text}")

# Catch all text messages
@rt.message(F.text)
def on_text(msg):
    msg.answer(f"You said: {msg.text}")

dp.run()
```

---

### Reply Keyboards

```python
from gramix import Reply, RemoveKeyboard

@rt.message("/start")
def on_start(msg):
    kb = (
        Reply(resize=True)
        .button("📋 Menu")
        .button("ℹ️ Info")
        .row()
        .button("⚙️ Settings")
    )
    msg.answer("Choose an option:", keyboard=kb)

@rt.message("📋 Menu")
def on_menu(msg):
    msg.answer("Here is the menu.")

@rt.message("ℹ️ Info")
def on_info(msg):
    msg.answer("This is the info section.")

@rt.message("⚙️ Settings")
def on_settings(msg):
    msg.answer("Settings are not configured yet.")

@rt.message("/remove")
def on_remove(msg):
    msg.answer("Keyboard removed.", keyboard=RemoveKeyboard())
```

---

### Inline Keyboards & Callbacks

```python
from gramix import Inline

@rt.message("/vote")
def on_vote(msg):
    kb = (
        Inline()
        .button("👍 Like", callback="vote:like")
        .button("👎 Dislike", callback="vote:dislike")
        .row()
        .button("🔗 Source", url="https://github.com/riokzyofficial-debug/gramix")
    )
    msg.answer("Cast your vote:", keyboard=kb)

# Handle exact callback data values
@rt.callback("vote:like", "vote:dislike")
def on_vote_result(cb):
    label = "👍 Like" if cb.data == "vote:like" else "👎 Dislike"
    cb.answer(f"You chose {label}", show_alert=True)
    cb.message.edit(f"You voted: {label}")

# Handle callbacks by prefix
@rt.callback(prefix="item:")
def on_item(cb):
    item_id = cb.data.split(":")[1]
    cb.answer(f"Selected item #{item_id}")
    cb.message.edit(f"You picked item #{item_id}.")

@rt.message("/catalog")
def on_catalog(msg):
    kb = (
        Inline()
        .button("Item 1", callback="item:1")
        .button("Item 2", callback="item:2")
        .row()
        .button("Item 3", callback="item:3")
        .button("Item 4", callback="item:4")
    )
    msg.answer("Pick an item:", keyboard=kb)

# Confirm/cancel pattern
@rt.message("/confirm")
def on_confirm(msg):
    kb = (
        Inline()
        .button("✅ Confirm", callback="confirmed")
        .button("❌ Cancel", callback="cancelled")
    )
    msg.answer("Are you sure?", keyboard=kb)

@rt.callback("confirmed")
def on_confirmed(cb):
    cb.answer("Done!")
    cb.message.edit("✅ Action confirmed.", keyboard=None)

@rt.callback("cancelled")
def on_cancelled(cb):
    cb.answer("Cancelled.")
    cb.message.edit("❌ Action cancelled.", keyboard=None)
```

---

### Finite State Machine (FSM)

```python
from gramix import State, Step, MemoryStorage, Router, RemoveKeyboard

rt = Router(storage=MemoryStorage())

class Registration(State):
    name = Step()
    age  = Step()
    city = Step()

@rt.message("/register")
def on_register(msg):
    ctx = rt.fsm.get(msg.from_user.id)
    ctx.set(Registration.name)
    msg.answer("What is your name?", keyboard=RemoveKeyboard())

@rt.state(Registration.name)
def get_name(msg, ctx):
    ctx.data["name"] = msg.text
    ctx.next()
    msg.answer("How old are you?")

@rt.state(Registration.age)
def get_age(msg, ctx):
    if not msg.text.isdigit():
        msg.answer("Please enter a valid number.")
        return
    ctx.data["age"] = int(msg.text)
    ctx.next()
    msg.answer("Which city are you from?")

@rt.state(Registration.city)
def get_city(msg, ctx):
    ctx.data["city"] = msg.text
    name = ctx.data["name"]
    age  = ctx.data["age"]
    city = ctx.data["city"]
    ctx.finish()
    msg.answer(
        f"Registration complete!\n"
        f"Name: {name}\nAge: {age}\nCity: {city}"
    )

@rt.message("/cancel")
def on_cancel(msg):
    ctx = rt.fsm.get(msg.from_user.id)
    if ctx.is_active:
        ctx.finish()
        msg.answer("Cancelled.", keyboard=RemoveKeyboard())
    else:
        msg.answer("Nothing to cancel.")
```

---

### SQLite FSM Storage

Use `SQLiteStorage` to persist FSM state across bot restarts:

```python
from gramix import SQLiteStorage, Router

rt = Router(storage=SQLiteStorage("state.db"))

# All @rt.state() handlers work identically — storage is transparent.
```

---

### Media Handling

```python
from gramix import F

@rt.message(F.photo)
def on_photo(msg):
    largest = msg.photo[-1]  # Telegram provides multiple sizes; last is largest
    msg.answer(f"Photo: {largest.width}×{largest.height}px")

@rt.message(F.document)
def on_document(msg):
    msg.answer(f"Document: {msg.document.file_name} ({msg.document.file_size} bytes)")

@rt.message(F.video)
def on_video(msg):
    msg.answer(f"Video: {msg.video.duration}s, {msg.video.width}×{msg.video.height}px")

@rt.message(F.voice)
def on_voice(msg):
    msg.answer(f"Voice message: {msg.voice.duration}s")

@rt.message(F.sticker)
def on_sticker(msg):
    msg.answer(f"Sticker: {msg.sticker.emoji}")

@rt.message(F.audio)
def on_audio(msg):
    title = msg.audio.title or "Unknown"
    msg.answer(f"Audio: {title} by {msg.audio.performer or 'Unknown'}")
```

---

### Sending Media

```python
@rt.message("/photo")
def on_send_photo(msg):
    msg.reply_photo(
        "https://picsum.photos/800/600",
        caption="A random photo",
    )

@rt.message("/video")
def on_send_video(msg):
    msg.reply_video(
        "https://example.com/sample.mp4",
        caption="Sample video",
    )

@rt.message("/document")
def on_send_document(msg):
    msg.reply_document(
        "BQACAgIAAxkB...",  # file_id
        caption="Here is your file",
    )

@rt.message("/sticker")
def on_send_sticker(msg):
    bot.send_sticker(msg.chat.id, "CAACAgIAAxkB...")
```

---

### File Download

```python
@rt.message(F.document)
def on_document(msg):
    file_bytes = bot.download_file(msg.document.file_id)
    with open(msg.document.file_name, "wb") as f:
        f.write(file_bytes)
    msg.answer(f"Saved: {msg.document.file_name}")
```

---

### Middleware

Middleware runs before every handler. It must call `call_next()` to continue the chain.

```python
import time

@dp.middleware
def timing_middleware(msg, call_next):
    start = time.monotonic()
    call_next()
    elapsed = time.monotonic() - start
    print(f"[{msg.from_user.id}] handled in {elapsed:.3f}s")

@dp.middleware
def auth_middleware(msg, call_next):
    ALLOWED = {123456789, 987654321}
    if msg.from_user.id not in ALLOWED:
        msg.answer("Access denied.")
        return  # Do not call call_next() — stops the chain
    call_next()

# Async middleware — works with run_async() and webhook
@dp.middleware
async def logging_middleware(msg, call_next):
    print(f"Update from @{msg.from_user.username}: {msg.text}")
    await call_next()
```

---

### Inline Queries

```python
from gramix import InlineQueryResultArticle, InlineQueryResultPhoto

@rt.inline()
def on_inline(query):
    results = [
        InlineQueryResultArticle(
            id="1",
            title="gramix",
            message_text="gramix — Telegram bot framework: https://pypi.org/project/gramix",
            description="Python Telegram bot framework",
        ),
        InlineQueryResultArticle(
            id="2",
            title=f"Search: {query.query}",
            message_text=f"You searched for: {query.query}",
        ),
        InlineQueryResultPhoto(
            id="3",
            photo_url="https://picsum.photos/400/300",
            thumb_url="https://picsum.photos/100/75",
            title="Random photo",
            caption="Sent via gramix inline",
        ),
    ]
    query.answer(results, cache_time=10)
```

---

### Chat Member Events

Detect users joining or leaving a chat:

```python
@rt.chat_member()
def on_member_update(update):
    if update.joined:
        print(f"{update.user.full_name} joined {update.chat.display_name}")
    elif update.left:
        print(f"{update.user.full_name} left {update.chat.display_name}")
```

---

### Polls & Quiz

Send a regular poll:

```python
@rt.message("/poll")
def send_poll(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="What is your favourite language?",
        options=["Python", "TypeScript", "Rust", "Go"],
        is_anonymous=True,
    )
```

Send a quiz with a correct answer and explanation:

```python
@rt.message("/quiz")
def send_quiz(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="What does GIL stand for?",
        options=["Global Import Loader", "Global Interpreter Lock", "Garbage Index Layer"],
        poll_type="quiz",
        correct_option_id=1,
        explanation="The Global Interpreter Lock allows only one thread to run at a time.",
    )
```

Handle votes in non-anonymous polls:

```python
@rt.poll_answer()
def on_vote(answer: PollAnswer):
    if answer.retracted:
        print(f"{answer.user.full_name} retracted their vote")
    else:
        print(f"{answer.user.full_name} chose options {answer.option_ids}")
```

Stop a poll early and read the final result:

```python
poll = bot.stop_poll(chat_id=msg.chat.id, message_id=msg.reply_to_message.message_id)
print(f"Final votes: {poll.total_voter_count}")
```

Filter messages that contain a forwarded poll or quiz:

```python
@rt.message(F.quiz)   # register specific filter first
def on_quiz(msg):
    print(f"Correct answer: {msg.poll.options[msg.poll.correct_option_id].text}")

@rt.message(F.poll)
def on_poll(msg):
    print(f"Poll: {msg.poll.question} ({msg.poll.total_voter_count} votes)")
```

---

### Location & Venue

Send a point on the map:

```python
@rt.message("/location")
def cmd_location(msg):
    bot.send_location(chat_id=msg.chat.id, latitude=55.7558, longitude=37.6173)
```

Send a named place with address:

```python
@rt.message("/venue")
def cmd_venue(msg):
    bot.send_venue(
        chat_id=msg.chat.id,
        latitude=55.7558,
        longitude=37.6173,
        title="Красная площадь",
        address="Красная площадь, Москва",
    )
```

Send a live location that updates in real time:

```python
bot.send_location(chat_id=msg.chat.id, latitude=55.7558, longitude=37.6173, live_period=300)
```

Handle incoming location and venue messages from users:

```python
@rt.message(F.location)
def on_location(msg):
    loc = msg.location
    msg.answer(f"Получена точка: {loc.latitude}, {loc.longitude}")

@rt.message(F.venue)
def on_venue(msg):
    msg.answer(f"Получено место: {msg.venue.title} — {msg.venue.address}")
```

---

### Payments

Send an invoice:

```python
from gramix import LabeledPrice

@rt.message("/buy")
def cmd_buy(msg):
    bot.send_invoice(
        chat_id=msg.chat.id,
        title="Premium доступ",
        description="30 дней Premium.",
        payload="premium_30d",
        provider_token="YOUR_PROVIDER_TOKEN",
        currency="RUB",
        prices=[LabeledPrice(label="Premium", amount=29900)],
    )
```

Confirm the payment before it is charged (required by Telegram):

```python
@rt.pre_checkout_query()
def on_pre_checkout(query: PreCheckoutQuery):
    bot.answer_pre_checkout_query(query.id, ok=True)
```

Handle successful payments:

```python
@rt.successful_payment()
def on_payment(msg):
    p = msg.successful_payment
    msg.answer(f"Оплата прошла! {p.amount_decimal} {p.currency}")
```

---

### Parse Mode & HTML Formatting

Set `parse_mode` once at `Bot` initialization — all `answer()`, `reply()`, `edit()`, `send_photo()`, and `send_video()` calls inherit it automatically:

```python
from gramix import Bot, ParseMode

bot = Bot(parse_mode=ParseMode.HTML)

@rt.message("/start")
def on_start(msg):
    msg.answer(
        "<b>Bold</b>, <i>italic</i>, <code>inline code</code>\n"
        "<a href='https://github.com/riokzyofficial-debug/gramix'>Link</a>\n"
        f"Hello, <b>{msg.from_user.full_name}</b>!"
    )

# Override per-call if needed
@rt.message("/markdown")
def on_markdown(msg):
    msg.answer("*bold* _italic_", parse_mode=ParseMode.MARKDOWN)
```

---

### Async Mode

All handlers, middleware, and lifecycle hooks support `async def`. Use `dp.run_async()` instead of `dp.run()`:

```python
from gramix import Bot, Dispatcher, Router, load_env, F, ParseMode

load_env()
bot = Bot(parse_mode=ParseMode.HTML)
dp  = Dispatcher(bot)
rt  = Router()
dp.include(rt)

@rt.message("/start")
async def on_start(msg):
    msg.answer("Hello from async!")

@rt.message(F.photo)
async def on_photo(msg):
    msg.answer("Photo received!")

@dp.on_startup
async def on_startup():
    print("Bot started.")

dp.run_async()
```

---

### Webhook Mode

```python
# Raw socket backend (no extra dependencies)
dp.run(webhook=True, webhook_url="https://yourdomain.com/", port=8080)

# aiohttp backend — pip install gramix[aiohttp]
dp.run(webhook=True, webhook_url="https://yourdomain.com/", backend="aiohttp", port=8080)

# FastAPI + uvicorn backend — pip install gramix[fastapi]
dp.run(webhook=True, webhook_url="https://yourdomain.com/", backend="fastapi", port=8080)
```

Alternatively, set `WEBHOOK_URL` in `.env` and omit the parameter:

```env
WEBHOOK_URL=https://yourdomain.com/
```

```python
dp.run(webhook=True, backend="aiohttp", port=8080)
```

---

### Lifecycle Hooks

```python
@dp.on_startup
def on_startup():
    print("Bot is online.")

@dp.on_shutdown
def on_shutdown():
    print("Bot is shutting down.")

# Async variants are supported in both sync and async mode
@dp.on_startup
async def async_startup():
    await db.connect()

@dp.on_shutdown
async def async_shutdown():
    await db.disconnect()
```

---

### Telegram Games

Send a Telegram game and track scores:

```python
from gramix import Inline

@rt.message("/game")
def on_game(msg):
    kb = Inline().button("🎮 Play", callback="game_play")
    bot.send_game(chat_id=msg.chat.id, game_short_name="mygame", keyboard=kb)

# Triggered when the user presses the Play button
@rt.game_callback()
def on_game_play(cb):
    cb.answer(url=f"https://yourdomain.com/game?user={cb.from_user.id}")

@rt.message("/setscore")
def on_set_score(msg):
    bot.set_game_score(
        user_id=msg.from_user.id,
        score=42,
        chat_id=msg.chat.id,
        message_id=msg.reply_to_message.message_id,
    )

@rt.message("/scores")
def on_scores(msg):
    scores = bot.get_game_high_scores(
        user_id=msg.from_user.id,
        chat_id=msg.chat.id,
        message_id=msg.reply_to_message.message_id,
    )
    for entry in scores:
        msg.answer(f"#{entry.position} {entry.user.full_name}: {entry.score}")
```

---

### Rate Limiting

Prevent users from flooding your bot using the built-in `ThrottlingMiddleware`:

```python
from gramix import ThrottlingMiddleware

# Allow one message per second per user (silent drop)
dp.middleware(ThrottlingMiddleware(rate=1.0))

# With a custom response when throttled
def on_throttle(msg):
    msg.answer("⚠️ Too many requests. Please wait a moment.")

dp.middleware(ThrottlingMiddleware(rate=1.0, on_throttle=on_throttle))

# Async on_throttle is supported too
async def on_throttle_async(msg):
    await msg.answer("⚠️ Slow down!")

dp.middleware(ThrottlingMiddleware(rate=0.5, on_throttle=on_throttle_async))
```

`ThrottlingMiddleware` works transparently in both `dp.run()` (sync) and `dp.run_async()` (async) modes.

---

## API Reference

### `Bot`

| Method | Description |
|---|---|
| `get_me()` | Returns bot's `User` object (cached). Use `refresh_me()` to force-refresh. |
| `send_message(chat_id, text, *, keyboard, parse_mode, disable_preview, auto_split)` | Send a text message. |
| `send_photo(chat_id, photo, *, caption, keyboard, parse_mode)` | Send a photo by `file_id` or URL. |
| `send_video(chat_id, video, *, caption, keyboard, parse_mode)` | Send a video. |
| `send_audio(chat_id, audio, *, caption, performer, title)` | Send an audio file. |
| `send_voice(chat_id, voice, *, caption)` | Send a voice message. |
| `send_document(chat_id, document, *, caption, keyboard)` | Send a document. |
| `send_sticker(chat_id, sticker)` | Send a sticker. |
| `send_chat_action(chat_id, action)` | Send a chat action (e.g. `"typing"`). |
| `edit_message_text(chat_id, message_id, text, *, keyboard, parse_mode)` | Edit a message. |
| `edit_message_keyboard(chat_id, message_id, keyboard)` | Edit only the inline keyboard of a message. |
| `delete_message(chat_id, message_id)` | Delete a message. |
| `forward_message(chat_id, from_chat_id, message_id)` | Forward a message. |
| `copy_message(chat_id, from_chat_id, message_id, *, caption)` | Copy a message without the forward header. |
| `pin_chat_message(chat_id, message_id)` | Pin a message. |
| `unpin_chat_message(chat_id, message_id)` | Unpin a message. |
| `set_message_reaction(chat_id, message_id, reaction)` | Set an emoji reaction. |
| `get_file(file_id)` | Get file metadata. |
| `download_file(file_id)` | Download file content as `bytes`. |
| `get_chat(chat_id)` | Get raw chat info. |
| `get_chat_member(chat_id, user_id)` | Get raw chat member info. |
| `get_chat_members_count(chat_id)` | Get member count. |
| `ban_chat_member(chat_id, user_id)` | Ban a user. |
| `unban_chat_member(chat_id, user_id)` | Unban a user. |
| `restrict_chat_member(chat_id, user_id, permissions)` | Restrict a user. |
| `leave_chat(chat_id)` | Leave a chat. |
| `set_my_commands(commands)` | Set the bot command list. |
| `delete_my_commands()` | Delete the bot command list. |
| `answer_callback_query(callback_query_id, text, *, show_alert)` | Answer a callback query. |
| `answer_inline_query(inline_query_id, results)` | Answer an inline query. |
| `send_poll(chat_id, question, options, *, is_anonymous, poll_type, allows_multiple_answers, correct_option_id, explanation, open_period, close_date, is_closed, keyboard)` | Send a regular poll or quiz. |
| `stop_poll(chat_id, message_id, *, keyboard)` | Close an open poll and return the final `Poll` object. |
| `send_location(chat_id, latitude, longitude, *, horizontal_accuracy, live_period, heading, proximity_alert_radius, keyboard)` | Send a point on the map. Pass `live_period` for a live location. |
| `send_venue(chat_id, latitude, longitude, title, address, *, foursquare_id, google_place_id, keyboard)` | Send a named place with address. |
| `edit_message_live_location(chat_id, message_id, latitude, longitude)` | Update a live location. |
| `stop_message_live_location(chat_id, message_id)` | Stop a live location broadcast. |
| `send_invoice(chat_id, title, description, payload, provider_token, currency, prices, *, keyboard)` | Send a payment invoice. |
| `answer_pre_checkout_query(pre_checkout_query_id, ok, *, error_message)` | Confirm or reject a pre-checkout query. |
| `send_game(chat_id, game_short_name, *, keyboard)` | Send a Telegram game. |
| `set_game_score(user_id, score, *, chat_id, message_id, inline_message_id, force, disable_edit_return)` | Set a user's score in a game. |
| `get_game_high_scores(user_id, *, chat_id, message_id, inline_message_id)` | Get the high score table; returns `list[GameHighScore]`. |
| `set_webhook(url, *, secret_token)` | Register a webhook URL. |
| `delete_webhook()` | Remove the webhook. |
| `get_webhook_info()` | Get current webhook status. |
| `close()` | Close the HTTP client. |

### `ThrottlingMiddleware`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rate` | `float` | `1.0` | Minimum seconds between accepted messages per user. |
| `on_throttle` | `Callable \| None` | `None` | Optional callback `(update) -> None` (sync or async) invoked when a message is throttled. If `None`, throttled messages are silently dropped. |

Register it like any other middleware:

```python
dp.middleware(ThrottlingMiddleware(rate=1.0))
```

Works in both `dp.run()` (sync) and `dp.run_async()` (async) modes without any changes.

### `ParseMode`

| Constant | Value |
|---|---|
| `ParseMode.HTML` | `"HTML"` |
| `ParseMode.MARKDOWN` | `"MarkdownV2"` |
| `ParseMode.MARKDOWN_LEGACY` | `"Markdown"` |

### `F` — Filter Shortcuts

| Filter | Matches when |
|---|---|
| `F.text` | Message has text |
| `F.photo` | Message has a photo |
| `F.document` | Message has a document |
| `F.video` | Message has a video |
| `F.audio` | Message has an audio file |
| `F.voice` | Message has a voice message |
| `F.sticker` | Message has a sticker |
| `F.reply` | Message is a reply |
| `F.forward` | Message is forwarded |
| `F.private` | Chat type is private |
| `F.group` | Chat type is group or supergroup |
| `F.supergroup` | Chat type is supergroup |
| `F.channel` | Chat type is channel |
| `F.poll` | Message contains a forwarded poll |
| `F.quiz` | Message contains a forwarded quiz |
| `F.location` | Message contains a location |
| `F.venue` | Message contains a venue |

---

## License

MIT © [riokzy](https://github.com/riokzyofficial-debug)
