# Phase 02: CLI Browser Flag & Global Config

This phase adds CLI flag support for browser selection and makes browser configuration consistent across all commands. Users can now specify `--browser chromium|lightpanda|remote` on any command, not just auth.

## Tasks

- [x] Add global `--browser` flag to CLI in cli.ts:
  - Add to main program options after `--verbose`: `.option("-b, --browser <type>", "Browser type (chromium|lightpanda|remote)")`
  - Pass browser option through command context
  - Create helper `getBrowserFromFlags()` that checks CLI flag first, then env var

- [x] Update auth command to use browser flag:
  - Replace `--lightpanda-host` and `--lightpanda-docker` options with unified `--browser` flag
  - If user passes `--browser remote`, require additional `--remote-host <ws://host:port>` flag
  - Remove deprecated `--lightpanda-host` and `--lightpanda-docker` (keep for backward compat but deprecate)

- [x] Add browser selection to status command:
  - Display currently configured browser type
  - Show which browser would be used for auth

- [x] Create browser-service.ts for consistent browser management:
  - `getBrowserConnection(cookies?: Record<string, string>)` - starts browser and returns CDP connection
  - `releaseBrowserConnection(conn)` - closes browser properly
  - Handles cleanup on errors
  - This becomes the single source of truth for browser lifecycle

- [x] Update all commands (list, fetch, continue, export, export-all) to use browser-service:
  - These commands don't need headed browser, but should respect configured default
  - For now, they only need cookie-based API access (no browser needed)

- [x] Test browser flag variations:
  - `webgemini auth --browser chromium` - should launch Chromium headed
  - `webgemini auth --browser lightpanda` - should use LightPanda
  - `webgemini auth --browser remote --remote-host ws://localhost:9222` - should connect remotely
  - `BROWSER_TYPE=chromium webgemini auth` - should respect env var
  - Flag should override env var when both are set

- [x] Update error messages in cli.ts:
  - Add Chromium-specific error messages in handleAuthError()
  - Display helpful message if Chromium is not installed
