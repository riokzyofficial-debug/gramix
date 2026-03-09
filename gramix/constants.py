API_BASE_URL: str = "https://api.telegram.org/bot{token}/{method}"
API_FILE_URL: str = "https://api.telegram.org/file/bot{token}/{path}"

DEFAULT_TIMEOUT: float = 30.0
POLLING_TIMEOUT: int = 5
RETRY_ATTEMPTS: int = 3
RETRY_DELAY: float = 1.0
RETRY_BACKOFF: float = 2.0

MAX_MESSAGE_LENGTH: int = 4096
MAX_CAPTION_LENGTH: int = 1024
MAX_CALLBACK_DATA_LENGTH: int = 64

TOKEN_ENV_KEY: str = "BOT_TOKEN"
DEBUG_ENV_KEY: str = "DEBUG"
WEBHOOK_URL_ENV_KEY: str = "WEBHOOK_URL"


class ParseMode:
    HTML = "HTML"
    MARKDOWN = "MarkdownV2"
    MARKDOWN_LEGACY = "Markdown"
