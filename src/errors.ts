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

export class LightPandaNotFoundError extends WebGeminiError {
    constructor(message: string = "LightPanda browser not found. Please ensure LightPanda is installed.") {
        super(message);
        this.name = "LightPandaNotFoundError";
    }
}

export class BrowserConnectionError extends WebGeminiError {
    constructor(message: string = "Could not connect to browser.") {
        super(message);
        this.name = "BrowserConnectionError";
    }
}

export class BrowserClosedError extends WebGeminiError {
    constructor(message: string = "Browser was closed before authentication completed.") {
        super(message);
        this.name = "BrowserClosedError";
    }
}

export class PortInUseError extends WebGeminiError {
    constructor(port: number, message?: string) {
        super(message || `Port ${port} is already in use. Tried alternate ports without success.`);
        this.name = "PortInUseError";
        this.port = port;
    }
    port: number;
}

export class DockerNotAvailableError extends WebGeminiError {
    constructor(message: string = "Docker is not available. Please install Docker to use this feature.") {
        super(message);
        this.name = "DockerNotAvailableError";
    }
}

export class DockerContainerError extends WebGeminiError {
    constructor(message: string = "Docker container error occurred.") {
        super(message);
        this.name = "DockerContainerError";
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
    LightPandaNotFoundError,
    BrowserConnectionError,
    BrowserClosedError,
    DockerNotAvailableError,
    DockerContainerError,
};

export function getErrorClass(errorType: string): new (message: string) => WebGeminiError {
    return ERROR_TYPE_MAP[errorType] ?? WebGeminiError;
}
