# Phase 02: Robustness & Error Handling

Enhance the prototype with production-ready error handling, retry mechanisms, and resilience features. This phase transforms the basic prototype into a reliable CLI tool that gracefully handles authentication failures, network issues, and API errors.

## Tasks

- [x] Create exceptions module `src/webgemini_cli/exceptions.py`:
  - Define `WebGeminiError` base exception class
  - Define `AuthenticationError` for cookie/auth failures
  - Define `CookieExpiredError` subclass for expired session detection
  - Define `GeminiAPIError` for API communication failures
  - Define `ConversationNotFoundError` for invalid conversation IDs

- [x] Enhance `auth_manager.py` with validation:
  - Add `validate_cookies(cookies: dict) -> bool` function checking required cookie names
  - Add `check_cookie_freshness(cookies: dict) -> bool` to detect expired sessions
  - Modify `load_cookies()` to raise `AuthenticationError` if file missing
  - Modify `load_cookies()` to raise `CookieExpiredError` if cookies appear stale
  - Add `refresh_cookies()` function that re-runs login flow if needed

- [x] Implement retry mechanism in `gemini_client.py`:
  - Add `@retry_on_auth_failure` decorator that catches auth errors and triggers cookie refresh
  - Wrap all API methods with retry logic (max 2 retries)
  - Add exponential backoff for network errors (1s, 2s delays)
  - Log retry attempts to stderr for visibility
  - Raise appropriate exceptions after retries exhausted

- [x] Add comprehensive error handling to CLI commands in `cli.py`:
  - Wrap all command handlers in try/except blocks
  - Catch `CookieExpiredError` and prompt user to run `webgemini auth`
  - Catch `GeminiAPIError` and display user-friendly error message
  - Catch `ConversationNotFoundError` with suggestion to run `webgemini list`
  - Use Rich's error styling for consistent error display
  - Return appropriate exit codes (0 success, 1 general error, 2 auth error)

- [x] Create logging module `src/webgemini_cli/logging_config.py`:
  - Configure logging with `--verbose` / `-v` flag support
  - Add `setup_logging(verbose: bool)` function
  - Log to stderr with timestamps
  - Add `--verbose` global option to CLI group
  - Log cookie operations, API calls, and retry attempts

- [x] Add input validation to CLI commands:
  - Validate `conversation_id` format (non-empty string)
  - Validate `message` is not empty for continue command
  - Add `--output` / `-o` option to export command for custom output path
  - Add `--limit` / `-n` option to list command (default 10, max 50)
  - Add `--format` option to fetch command (text, json)

- [x] Create session health check utility:
  - Add `webgemini status` command that validates cookies and tests API connection
  - Display cookie expiration status and last known good connection
  - Print configuration paths and settings summary

- [x] Add graceful degradation for missing optional features:
  - Handle cases where Rich is not installed (fallback to plain text)
  - Handle cases where browser automation fails (suggest manual cookie extraction)
  - Document manual cookie extraction as fallback in README

(End of file - total 58 lines)