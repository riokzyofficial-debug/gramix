# Contributing to gramix

Thank you for your interest in contributing! This document explains how to get started, what the project expects from contributors, and how pull requests are reviewed.

---

## Getting Started

Fork the repository and clone your fork:

```bash
git clone https://github.com/your-username/gramix.git
cd gramix
```

Create a virtual environment and install the development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Running the Tests

The test suite lives in the `tests/` directory. Run it with:

```bash
pytest
```

All tests must pass before a pull request can be merged. If you are adding a new feature, please include tests that cover the new behaviour.

---

## Code Style

gramix uses [black](https://github.com/psf/black) for formatting. Before committing, format your changes:

```bash
pip install black
black gramix/ tests/
```

The project is fully type-annotated. New public API must include type hints. You can verify types with [mypy](https://mypy-lang.org):

```bash
pip install mypy
mypy gramix/
```

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add SQLiteStorage persistence
fix: handle empty photo array in F.photo filter
docs: add webhook example to README
test: cover MemoryStorage eviction logic
refactor: extract _build_message_filters to Router
```

---

## Opening an Issue

Before opening an issue, please search the [existing issues](https://github.com/riokzyofficial-debug/gramix/issues) to avoid duplicates.

Use the provided issue templates:

- **Bug report** — something is broken or behaves unexpectedly
- **Feature request** — a new capability you would like to see

Please include a minimal reproducible example where applicable.

---

## Opening a Pull Request

1. Create a feature branch from `main`:

   ```bash
   git checkout -b feat/my-feature
   ```

2. Make your changes, add tests, and verify that `pytest` passes.

3. Push the branch and open a pull request against `main`.

4. Fill in the pull request template. Describe what changed and why.

5. A maintainer will review the PR and may request changes before merging.

---

## Project Structure

```
gramix/
├── gramix/              # Core library
│   ├── __init__.py      # Public API exports
│   ├── bot.py           # Bot class — all Telegram API calls
│   ├── dispatcher.py    # Polling, webhook, and update dispatch
│   ├── router.py        # Handler registration and routing
│   ├── filters.py       # Filter classes and F shortcut
│   ├── fsm.py           # State, Step, MemoryStorage, SQLiteStorage
│   ├── middleware.py    # MiddlewareManager
│   ├── constants.py     # API URLs, timeouts, ParseMode
│   ├── env.py           # load_env() and token helpers
│   ├── exceptions.py    # Exception hierarchy
│   └── types/           # Telegram object types
├── examples/            # Runnable example bots
├── tests/               # Pytest test suite
├── pyproject.toml
└── README.md
```

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/riokzyofficial-debug/gramix/blob/main/LICENSE).
