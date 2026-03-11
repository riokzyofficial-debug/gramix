class GramixError(Exception):
    pass

class TokenError(GramixError):
    pass

class TelegramAPIError(GramixError):
    def __init__(self, code: int, description: str) -> None:
        self.code = code
        self.description = description
        super().__init__(f"Telegram API error {code}: {description}")

class NetworkError(GramixError):
    pass

class RetryAfterError(TelegramAPIError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(429, f"Flood control. Retry after {retry_after}s.")

class MessageError(GramixError):
    pass

class FSMError(GramixError):
    pass

class FilterError(GramixError):
    pass

class MiddlewareError(GramixError):
    pass

class WebhookError(GramixError):
    pass

class FileError(GramixError):
    pass
