# Phase 02: Python Wrapper Subprocess

Create a well-encapsulated Python subprocess wrapper for the python-gemini-api library. This enables TypeScript code to communicate with the Gemini API via JSON over stdin/stdout, spawning a new Python process per command.

## Tasks

- [x] Create Python wrapper entry point `python/wrapper.py`:
  - Read JSON request from stdin
  - Parse command type: "auth", "list_chats", "fetch_chat", "continue_chat"
  - Route to appropriate handler function
  - Write JSON response to stdout
  - Handle errors and return structured error responses

- [x] Define JSON protocol for stdin/stdout communication:
  - Request format:
    ```json
    {
      "command": "list_chats" | "fetch_chat" | "continue_chat",
      "cookies": { "name": "value", ... },
      "params": { ...command-specific params... }
    }
    ```
  - Response format:
    ```json
    {
      "success": true | false,
      "data": { ...result data... },
      "error": { "type": "ErrorClass", "message": "..." } | null
    }
    ```

- [x] Implement Python wrapper handlers:
  - `handle_list_chats(cookies, params)` → returns list of {id, title}
  - `handle_fetch_chat(cookies, params)` → returns list of messages
  - `handle_continue_chat(cookies, params)` → returns response text
  - Each handler uses existing `GeminiClient` from `gemini_client.py`

- [x] Create TypeScript subprocess wrapper `src/python-wrapper.ts`:
  - Implement `spawnPythonWrapper(request: PythonWrapperRequest): Promise<PythonWrapperResponse>`
  - Use `Bun.spawn()` to launch Python process
  - Write JSON request to child's stdin
  - Read JSON response from child's stdout
  - Handle process errors and timeouts
  - Parse response and return typed result

- [x] Create TypeScript GeminiClient class `src/gemini-client.ts`:
  - Wrap Python subprocess communication
  - Methods mirror Python GeminiClient:
    - `listChats(): Promise<GeminiChat[]>`
    - `fetchChat(conversationId: string): Promise<GeminiMessage[]>`
    - `continueChat(conversationId: string, message: string): Promise<string>`
  - Each method constructs request, calls python wrapper, returns typed result

- [x] Implement error mapping in TypeScript:
  - Map Python exception types to TypeScript error classes
  - Create error classes in `src/errors.ts`:
    - `AuthenticationError`
    - `CookieExpiredError`
    - `GeminiAPIError`
    - `ConversationNotFoundError`
  - Throw appropriate TypeScript errors based on Python response

- [x] Add subprocess timeout handling:
  - Default 30 second timeout for Python subprocess
  - Kill process if timeout exceeded
  - Return appropriate error to caller

- [x] Test Python wrapper in isolation:
  - Run `echo '{"command": "list_chats", "cookies": {...}}' | python python/wrapper.py`
  - Verify JSON output is valid and parseable
  - Test error cases return proper error format

- [x] Test TypeScript wrapper integration:
  - Create test script that calls GeminiClient methods
  - Verify end-to-end communication works
  - Test error handling and timeout scenarios
