from __future__ import annotations
import logging
import os
from pathlib import Path

from gramix.constants import TOKEN_ENV_KEY, DEBUG_ENV_KEY, WEBHOOK_URL_ENV_KEY

logger = logging.getLogger(__name__)


def load_env(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        logger.debug(".env не найден: %s", env_path.resolve())
        return

    with env_path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                logger.warning(".env строка %d пропущена (нет '='): %s", line_number, line)
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

    logger.debug(".env загружен: %s", env_path.resolve())


def get_token() -> str | None:
    return os.environ.get(TOKEN_ENV_KEY)


def is_debug() -> bool:
    return os.environ.get(DEBUG_ENV_KEY, "").lower() in ("1", "true", "yes")


def get_webhook_url() -> str | None:
    return os.environ.get(WEBHOOK_URL_ENV_KEY)
