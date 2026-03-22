import { describe, test, expect } from "bun:test";
import { mapResponseToError } from "../src/python-wrapper";
import type { PythonWrapperResponse } from "../src/python-wrapper";
import { SubprocessError, AuthenticationError, ConversationNotFoundError, GeminiAPIError, CookieExpiredError } from "../src/errors";

describe("mapResponseToError", () => {
    test("throws when response is successful", () => {
        const successfulResponse: PythonWrapperResponse = {
            success: true,
            data: {},
            error: null,
        };

        expect(() => mapResponseToError(successfulResponse)).toThrow(
            "mapResponseToError called with successful response"
        );
    });

    test("creates AuthenticationError", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "AuthenticationError", message: "Auth failed" },
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(AuthenticationError);
        expect(error.message).toBe("Auth failed");
    });

    test("creates ConversationNotFoundError", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "ConversationNotFoundError", message: "Not found" },
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(ConversationNotFoundError);
        expect(error.message).toBe("Not found");
    });

    test("creates GeminiAPIError", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "GeminiAPIError", message: "API error" },
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(GeminiAPIError);
        expect(error.message).toBe("API error");
    });

    test("creates CookieExpiredError", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "CookieExpiredError", message: "Cookie expired" },
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(CookieExpiredError);
        expect(error.message).toBe("Cookie expired");
    });

    test("creates SubprocessError for unknown error type", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "UnknownErrorType", message: "Unknown error" },
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(Error);
        expect(error.message).toBe("Unknown error");
    });

    test("handles null error info", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: null,
        };

        const error = mapResponseToError(response);
        expect(error).toBeInstanceOf(SubprocessError);
        expect(error.message).toBe("Unknown error occurred");
    });
});

describe("PythonWrapperRequest interface", () => {
    test("accepts valid list_chats request structure", () => {
        const request = {
            command: "list_chats",
            cookies: { "__Secure-1PSID": "value1", "__Secure-1PSIDTS": "value2" },
            params: {},
        };

        expect(request.command).toBe("list_chats");
        expect(Object.keys(request.cookies)).toHaveLength(2);
    });

    test("accepts valid fetch_chat request structure", () => {
        const request = {
            command: "fetch_chat",
            cookies: { "__Secure-1PSID": "value1" },
            params: { conversation_id: "chat123" },
        };

        expect(request.command).toBe("fetch_chat");
        expect(request.params.conversation_id).toBe("chat123");
    });

    test("accepts valid continue_chat request structure", () => {
        const request = {
            command: "continue_chat",
            cookies: { "__Secure-1PSID": "value1" },
            params: { conversation_id: "chat123", message: "Hello" },
        };

        expect(request.command).toBe("continue_chat");
        expect(request.params.message).toBe("Hello");
    });
});

describe("PythonWrapperResponse interface", () => {
    test("parses successful list_chats response", () => {
        const response: PythonWrapperResponse = {
            success: true,
            data: [
                { id: "chat1", title: "Test Chat" },
                { id: "chat2", title: "Another Chat" },
            ],
            error: null,
        };

        expect(response.success).toBe(true);
        expect(Array.isArray(response.data)).toBe(true);
        expect(response.error).toBeNull();
    });

    test("parses successful fetch_chat response", () => {
        const response: PythonWrapperResponse = {
            success: true,
            data: [
                { role: "user" as const, content: "Hello", conversation_id: "chat123" },
                { role: "model" as const, content: "Hi!", conversation_id: "chat123" },
            ],
            error: null,
        };

        expect(response.success).toBe(true);
        expect(Array.isArray(response.data)).toBe(true);
        expect((response.data as any)[0].role).toBe("user");
    });

    test("parses error response", () => {
        const response: PythonWrapperResponse = {
            success: false,
            data: null,
            error: { type: "AuthenticationError", message: "Auth failed" },
        };

        expect(response.success).toBe(false);
        expect(response.data).toBeNull();
        expect(response.error?.type).toBe("AuthenticationError");
    });
});

describe("JSON Protocol serialization", () => {
    test("serializes request to JSON correctly", () => {
        const request = {
            command: "list_chats",
            cookies: { "__Secure-1PSID": "test", "__Secure-1PSIDTS": "test2" },
            params: {},
        };

        const json = JSON.stringify(request);
        const parsed = JSON.parse(json);

        expect(parsed.command).toBe("list_chats");
        expect(parsed.cookies["__Secure-1PSID"]).toBe("test");
    });

    test("serializes response to JSON correctly", () => {
        const response: PythonWrapperResponse = {
            success: true,
            data: [{ id: "chat1", title: "Test" }],
            error: null,
        };

        const json = JSON.stringify(response);
        const parsed = JSON.parse(json);

        expect(parsed.success).toBe(true);
        expect(parsed.data[0].id).toBe("chat1");
    });

    test("handles JSON parse errors gracefully in response parsing", () => {
        const invalidJson = "not valid json {";
        
        expect(() => JSON.parse(invalidJson)).toThrow();
    });
});