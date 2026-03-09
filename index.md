# gramix

**gramix** is a fast, clean, fully-typed Python framework for building Telegram bots. It provides a straightforward, decorator-based API that works in both synchronous and asynchronous modes with zero boilerplate.

## Why gramix?

Most Telegram bot frameworks require `async def` everywhere, even for simple scripts. gramix takes a different approach: your handlers are plain functions by default, and async support is opt-in. You can build a production-ready bot without ever writing `await`.

## Key Features

- **Sync & async** — handlers, middleware, and lifecycle hooks all work with both `def` and `async def`
- **FSM built-in** — finite state machine with `MemoryStorage` or persistent `SQLiteStorage`
- **Zero boilerplate** — a working bot in 8 lines of code
- **Fully typed** — complete type annotations and a `py.typed` marker
- **Inline & Reply keyboards** — fluent builder API with method chaining
- **Middleware** — chainable pre-handler functions with `call_next()`
- **Webhooks** — raw socket, aiohttp, and FastAPI backends

## Installation

```bash
pip install gramix
```

Optional webhook backends:

```bash
pip install gramix[aiohttp]   # aiohttp backend
pip install gramix[fastapi]   # FastAPI + uvicorn backend
```

**Requirements:** Python 3.10 or higher.

## Quick Example

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

## Documentation

| Guide | Description |
|---|---|
| [Getting Started](getting-started.md) | Installation, project setup, first bot |
| [Core Concepts](core-concepts.md) | Bot, Dispatcher, Router explained |
| [Filters](filters.md) | Commands, text, regex, media, and custom filters |
| [Keyboards](keyboards.md) | Inline and Reply keyboard builders |
| [FSM](fsm.md) | Finite state machine for multi-step flows |
| [Middleware](middleware.md) | Pre-handler middleware chain |
| [Async Mode](async.md) | Async handlers and `run_async()` |
| [Webhooks](webhook.md) | Running in webhook mode |
| [API Reference](api-reference.md) | Full method and class reference |

## Links

- **Repository:** https://github.com/riokzyofficial-debug/gramix
- **PyPI:** https://pypi.org/project/gramix
- **Issues:** https://github.com/riokzyofficial-debug/gramix/issues

## License

MIT © [riokzy](https://github.com/riokzyofficial-debug)
