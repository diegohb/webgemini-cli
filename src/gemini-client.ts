import type { GeminiChat, GeminiMessage } from "./types/gemini.js";
import { spawnPythonWrapper, mapResponseToError } from "./python-wrapper.ts";
import type { PythonWrapperRequest } from "./python-wrapper.ts";

/**
 * Client for interacting with the Gemini web API via Python subprocess wrapper.
 * Handles authentication cookies and delegates API operations to the Python layer.
 */
export class GeminiClient {
    private cookies: Record<string, string>;

    /**
     * Creates a new GeminiClient instance.
     * @param cookies - Dictionary of cookie name-value pairs for Gemini API authentication
     */
    constructor(cookies: Record<string, string>) {
        this.cookies = cookies;
    }

    /**
     * Lists all available Gemini conversations.
     * @returns Promise resolving to array of GeminiChat objects containing id and title
     * @throws {SubprocessError} If Python subprocess communication fails
     * @throws {GeminiAPIError} If the API returns an error
     */
    async listChats(): Promise<GeminiChat[]> {
        const request: PythonWrapperRequest = {
            command: "list_chats",
            cookies: this.cookies,
            params: {},
        };

        const response = await spawnPythonWrapper(request);

        if (!response.success) {
            throw mapResponseToError(response);
        }

        return response.data as GeminiChat[];
    }

    /**
     * Fetches the message history of a specific conversation.
     * @param conversationId - The unique identifier of the conversation to fetch
     * @returns Promise resolving to array of GeminiMessage objects with role and content
     * @throws {ConversationNotFoundError} If the conversation does not exist
     * @throws {SubprocessError} If Python subprocess communication fails
     * @throws {GeminiAPIError} If the API returns an error
     */
    async fetchChat(conversationId: string): Promise<GeminiMessage[]> {
        const request: PythonWrapperRequest = {
            command: "fetch_chat",
            cookies: this.cookies,
            params: { conversation_id: conversationId },
        };

        const response = await spawnPythonWrapper(request);

        if (!response.success) {
            throw mapResponseToError(response);
        }

        return response.data as GeminiMessage[];
    }

    /**
     * Sends a message to an existing conversation and returns the model's response.
     * @param conversationId - The unique identifier of the conversation to continue
     * @param message - The message text to send to the conversation
     * @returns Promise resolving to the model's response text
     * @throws {ConversationNotFoundError} If the conversation does not exist
     * @throws {CookieExpiredError} If the authentication cookies have expired
     * @throws {SubprocessError} If Python subprocess communication fails
     * @throws {GeminiAPIError} If the API returns an error
     */
    async continueChat(conversationId: string, message: string): Promise<string> {
        const request: PythonWrapperRequest = {
            command: "continue_chat",
            cookies: this.cookies,
            params: { conversation_id: conversationId, message },
        };

        const response = await spawnPythonWrapper(request);

        if (!response.success) {
            throw mapResponseToError(response);
        }

        return response.data as string;
    }
}
