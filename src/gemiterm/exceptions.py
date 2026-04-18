class GemitermError(Exception):
    pass


class AuthenticationError(GemitermError):
    pass


class CookieExpiredError(AuthenticationError):
    pass


class GeminiAPIError(GemitermError):
    pass


class ConversationNotFoundError(GemitermError):
    pass
