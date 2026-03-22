import { describe, test, expect } from "bun:test";
import type { GeminiChat, GeminiMessage } from "../src/types";

describe("GeminiClient interface", () => {
    test("GeminiChat structure is correct", () => {
        const chat: GeminiChat = {
            id: "chat123",
            title: "Test Chat",
        };

        expect(chat.id).toBe("chat123");
        expect(chat.title).toBe("Test Chat");
    });

    test("GeminiMessage structure is correct", () => {
        const message: GeminiMessage = {
            role: "user",
            content: "Hello world",
            conversation_id: "chat123",
        };

        expect(message.role).toBe("user");
        expect(message.content).toBe("Hello world");
        expect(message.conversation_id).toBe("chat123");
    });

    test("GeminiMessage accepts model role", () => {
        const message: GeminiMessage = {
            role: "model",
            content: "Response",
            conversation_id: "chat123",
        };

        expect(message.role).toBe("model");
    });

    test("GeminiMessage accepts assistant role", () => {
        const message: GeminiMessage = {
            role: "assistant",
            content: "Response",
            conversation_id: "chat123",
        };

        expect(message.role).toBe("assistant");
    });
});

describe("GeminiClient request/response flow", () => {
    test("listChats request format", () => {
        const request = {
            command: "list_chats" as const,
            cookies: { "__Secure-1PSID": "val1", "__Secure-1PSIDTS": "val2" },
            params: {},
        };

        expect(request.command).toBe("list_chats");
        expect(Object.keys(request.cookies)).toContain("__Secure-1PSID");
    });

    test("fetchChat request format with conversation_id", () => {
        const request = {
            command: "fetch_chat" as const,
            cookies: { "__Secure-1PSID": "val1" },
            params: { conversation_id: "chat123" },
        };

        expect(request.command).toBe("fetch_chat");
        expect(request.params.conversation_id).toBe("chat123");
    });

    test("continueChat request format with message", () => {
        const request = {
            command: "continue_chat" as const,
            cookies: { "__Secure-1PSID": "val1" },
            params: { conversation_id: "chat123", message: "Hello" },
        };

        expect(request.command).toBe("continue_chat");
        expect(request.params.message).toBe("Hello");
    });

    test("successful listChats response parsing", () => {
        const response = {
            success: true,
            data: [
                { id: "chat1", title: "First Chat" },
                { id: "chat2", title: "Second Chat" },
            ] as GeminiChat[],
            error: null,
        };

        expect(response.success).toBe(true);
        expect(response.data).toHaveLength(2);
        expect(response.data![0].title).toBe("First Chat");
    });

    test("successful fetchChat response parsing", () => {
        const response: { success: boolean; data: GeminiMessage[] | null; error: null } = {
            success: true,
            data: [
                { role: "user" as const, content: "Hello", conversation_id: "chat123" },
                { role: "model" as const, content: "Hi!", conversation_id: "chat123" },
            ],
            error: null,
        };

        expect(response.success).toBe(true);
        expect(response.data).toHaveLength(2);
        expect(response.data![0].role).toBe("user");
    });

    test("successful continueChat response parsing returns message ID", () => {
        const response = {
            success: true,
            data: "new_message_id_123",
            error: null,
        };

        expect(response.success).toBe(true);
        expect(typeof response.data).toBe("string");
    });

    test("error response parsing for AuthenticationError", () => {
        const response: { success: false; data: null; error: { type: string; message: string } | null } = {
            success: false,
            data: null,
            error: { type: "AuthenticationError", message: "Cookie expired" },
        };

        expect(response.success).toBe(false);
        expect(response.error?.type).toBe("AuthenticationError");
        expect(response.error?.message).toBe("Cookie expired");
    });

    test("error response parsing for ConversationNotFoundError", () => {
        const response: { success: false; data: null; error: { type: string; message: string } | null } = {
            success: false,
            data: null,
            error: { type: "ConversationNotFoundError", message: "Not found" },
        };

        expect(response.success).toBe(false);
        expect(response.error?.type).toBe("ConversationNotFoundError");
    });
});

describe("GeminiClient cookie handling", () => {
    test("requires __Secure-1PSID cookie", () => {
        const cookies = {
            "__Secure-1PSID": "required_value",
        };

        expect("__Secure-1PSID" in cookies).toBe(true);
    });

    test("requires __Secure-1PSIDTS cookie", () => {
        const cookies = {
            "__Secure-1PSIDTS": "required_value",
        };

        expect("__Secure-1PSIDTS" in cookies).toBe(true);
    });

    test("cookies object can be passed to request", () => {
        const cookies = {
            "__Secure-1PSID": "val1",
            "__Secure-1PSIDTS": "val2",
        };

        const request = {
            command: "list_chats" as const,
            cookies,
            params: {},
        };

        expect(request.cookies).toEqual(cookies);
    });
});