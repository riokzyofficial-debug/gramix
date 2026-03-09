# Async Mode

gramix supports async handlers natively. Every handler, middleware function, and lifecycle hook can be declared as `async def` and awaited correctly. No special configuration is required — mix sync and async freely within the same bot.

## Starting in async mode

Replace `dp.run()` with `dp.run_async()`:

```python
from gramix import Bot, Dispatcher, Router, load_env

load_env()
bot = Bot()
dp  = Dispatcher(bot)
rt  = Router()
dp.include(rt)

@rt.message("/start")
async def on_start(msg):
    await msg.answer("Hello from async!")

@dp.on_startup
async def on_startup():
    print("Bot started.")

dp.run_async()
```

`dp.run_async()` runs `asyncio.run()` internally, so there is no need to manage the event loop manually.

## Async handlers

Async handlers work identically to sync handlers from a feature standpoint. All message, callback, inline query, chat member, and FSM state handlers support `async def`:

```python
@rt.message("/info")
async def on_info(msg):
    await msg.answer(f"Your ID: {msg.from_user.id}")

@rt.callback("refresh")
async def on_refresh(cb):
    await cb.answer("Refreshed!")
    await cb.message.edit("Updated content.")

@rt.state(Form.email)
async def get_email(msg, ctx):
    ctx.data["email"] = msg.text
    ctx.next()
    await msg.answer("Thanks! Processing...")
```

## Async middleware

```python
@dp.middleware
async def log_middleware(msg, call_next):
    print(f"Incoming: {msg.text!r}")
    await call_next()
```

## Async lifecycle hooks

```python
@dp.on_startup
async def startup():
    await db.connect()
    print("Database connected.")

@dp.on_shutdown
async def shutdown():
    await db.disconnect()
    print("Database disconnected.")
```

## Mixing sync and async

You can mix sync and async handlers freely. gramix detects whether a function is a coroutine at dispatch time and handles it accordingly. For example, a synchronous startup hook and async handlers can coexist:

```python
@dp.on_startup
def setup():
    print("Sync startup.")

@rt.message("/start")
async def on_start(msg):
    await msg.answer("Hello!")
```

## When to use async

Use `dp.run_async()` when your handlers need to perform I/O — database queries, HTTP requests to external APIs, or file reads — without blocking other updates. For bots with purely CPU-bound or quick handlers, synchronous mode with `dp.run()` is simpler and equally performant.

For webhook deployments with aiohttp or FastAPI backends, async mode is used automatically regardless of how handlers are declared.
