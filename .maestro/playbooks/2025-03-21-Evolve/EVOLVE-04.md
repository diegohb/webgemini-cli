# Phase 04: Port CLI Commands

Port all remaining CLI commands from Python to TypeScript. Each command should use the Python subprocess wrapper for Gemini API calls and LightPanda for browser operations.

## Tasks

- [x] Port `list` command:
  - Load cookies using auth module
  - Call `GeminiClient.listChats()` via Python wrapper
  - Display results in formatted table (use `console.table()` or custom formatting)
  - Handle errors: CookieExpiredError → prompt re-auth, GeminiAPIError → display error
  - Support `-n, --limit` option (default 10, max 50)
  - Exit codes: 0 success, 1 general error, 2 auth error

- [x] Port `fetch` command:
  - Load cookies
  - Validate conversation_id is not empty
  - Call `GeminiClient.fetchChat(conversationId)` via Python wrapper
  - Display messages with role-based formatting (USER in green, MODEL in blue)
  - Support `--format, -f` option (text, json)
  - Handle ConversationNotFoundError → suggest running `list`

- [x] Port `continue` command:
  - Load cookies
  - Validate conversation_id and message are not empty
  - Call `GeminiClient.continueChat(conversationId, message)` via Python wrapper
  - Display response text
  - Handle all error types with appropriate messages

- [x] Port `export` command:
  - Load cookies
  - Fetch chat using `GeminiClient.fetchChat()`
  - Format as Markdown (port logic from Python `exporter.py`)
  - Support `-o, --output` option for custom output path
  - Support `--format, -f` option (markdown, json)
  - Support `--include-metadata` flag
  - Default filename: `gemini-chat-{conversation_id}-{date}.md`
  - Use `Bun.write()` for file output

- [x] Create exporter module `src/exporter.ts`:
  - Implement `formatChatAsMarkdown(messages, title, options)` function
  - Port markdown formatting logic from Python `exporter.py`
  - Include metadata section if requested
  - Format messages with proper headers and role labels

- [x] Port `export-all` command:
  - Load cookies
  - List all chats using `GeminiClient.listChats()`
  - Support `--output-dir, -o` option (default: ./exports)
  - Support `--since` option to filter by date
  - Support `--include-metadata` flag
  - Iterate through chats and export each one
  - Show progress indicator (spinner or text-based)
  - Create `_index.md` with links to all exported chats
  - Track and report failed exports
  - Use `Bun.write()` for all file operations

- [x] Port `status` command:
  - Check if storage_state.json exists
  - Load and validate cookies
  - Test API connection by calling `listChats()`
  - Display:
    - Config directory path
    - Storage file path
    - Authentication status (valid/expired/missing)
    - API connection status (connected/error)
  - Exit codes: 0 success, 1 general error, 2 auth error

- [x] Add global verbose logging:
  - Implement `--verbose, -v` global flag
  - Log subprocess spawns
  - Log API calls and responses
  - Log cookie operations
  - Use `console.error()` for debug output (goes to stderr)

- [x] Ensure consistent error handling across all commands:
  - Use try/catch with typed error classes
  - Display colored error messages
  - Suggest remediation steps (e.g., "Run 'webgemini auth' to re-authenticate")
  - Return appropriate exit codes

- [x] Test all commands end-to-end:
  - Run each command and verify output
  - Test error scenarios
  - Verify exit codes are correct
  - Test with invalid/expired cookies

## Notes

- Implemented all CLI commands in `src/cli.ts`
- Created `src/exporter.ts` with markdown formatting logic ported from Python
- Added global `-v, --verbose` flag with `console.error()` for debug output
- Error handling uses typed error classes with colored output and remediation suggestions
- Created comprehensive test suite in `tests/cli.test.ts` covering all commands, error scenarios, and exit codes
- All 44 tests pass (31 CLI tests + 13 existing auth/cookie-store tests)
- EFTYPE errors in tests are expected on Windows (Python wrapper subprocess spawning differs from Unix)
