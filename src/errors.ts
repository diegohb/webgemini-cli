export class WebGeminiError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "WebGeminiError";
    }
}

export class AuthenticationError extends WebGeminiError {
    constructor(message: string = "Authentication failed. Please re-authenticate.") {
        super(message);
        this.name = "AuthenticationError";
    }
}

export class CookieExpiredError extends AuthenticationError {
    constructor(message: string = "Cookie has expired. Please re-authenticate.") {
        super(message);
        this.name = "CookieExpiredError";
    }
}

export class GeminiAPIError extends WebGeminiError {
    constructor(message: string = "Gemini API error occurred.") {
        super(message);
        this.name = "GeminiAPIError";
    }
}

export class ConversationNotFoundError extends WebGeminiError {
    constructor(message: string = "Conversation not found.") {
        super(message);
        this.name = "ConversationNotFoundError";
    }
}

export class SubprocessError extends WebGeminiError {
    constructor(message: string = "Subprocess error occurred.") {
        super(message);
        this.name = "SubprocessError";
    }
}

export class SubprocessTimeoutError extends SubprocessError {
    constructor(message: string = "Subprocess timed out.") {
        super(message);
        this.name = "SubprocessTimeoutError";
    }
}

const ERROR_TYPE_MAP: Record<string, new (message: string) => WebGeminiError> = {
    AuthenticationError,
    CookieExpiredError,
    GeminiAPIError,
    ConversationNotFoundError,
    WebGeminiError,
    SubprocessError,
    SubprocessTimeoutError,
};

export function getErrorClass(errorType: string): new (message: string) => WebGeminiError {
    return ERROR_TYPE_MAP[errorType] ?? WebGeminiError;
}
