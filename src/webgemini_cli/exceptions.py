class WebGeminiError(Exception):
    pass


class AuthenticationError(WebGeminiError):
    pass


class CookieExpiredError(AuthenticationError):
    pass


class GeminiAPIError(WebGeminiError):
    pass


class ConversationNotFoundError(WebGeminiError):
    pass
