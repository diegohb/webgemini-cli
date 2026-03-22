import type { GeminiChat, GeminiMessage } from "./types/index.ts";
import { spawnPythonWrapper, mapResponseToError } from "./python-wrapper.ts";
import type { PythonWrapperRequest } from "./python-wrapper.ts";

export class GeminiClient {
    private cookies: Record<string, string>;

    constructor(cookies: Record<string, string>) {
        this.cookies = cookies;
    }

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
