# Phase 03: LightPanda Browser Integration

Replace Playwright/Chromium with LightPanda for browser-based authentication. LightPanda is a lightweight headless browser that can be controlled via Playwright's CDP (Chrome DevTools Protocol) interface.

## Tasks

- [x] Create LightPanda browser module `src/browser.ts`:
  - Import `@lightpanda/browser`
  - Implement `startBrowser()` function:
    - Configure LightPanda options (host: '127.0.0.1', port: 9222)
    - Call `lightpanda.serve()` to start browser process
    - Return process handle for later cleanup
  - Implement `stopBrowser(proc)` function:
    - Destroy stdout/stderr streams
    - Kill the browser process

- [x] Create Playwright CDP connection module `src/cdp-client.ts`:
  - Connect Playwright to LightPanda via CDP endpoint
  - Use `chromium.connectOverCDP('http://127.0.0.1:9222')`
  - Create browser context and page
  - Handle connection errors gracefully

- [x] Create auth module `src/auth.ts`:
  - Implement `login()` async function:
    - Start LightPanda browser
    - Connect Playwright via CDP
    - Create new page and navigate to `https://gemini.google.com`
    - Wait for user to complete Google login (non-headless for auth)
    - Poll for required cookies: `__Secure-1PSID`, `__Secure-1PSIDTS`
    - Extract cookies from browser context
    - Save cookies to storage_state.json
    - Close browser and stop LightPanda process
  - Implement `loadCookies()` function:
    - Read cookies from storage_state.json
    - Return typed GeminiCookie array
  - Implement `validateCookies(cookies)` function:
    - Check required cookie names are present
  - Implement `checkCookieFreshness(cookies)` function:
    - Check `__Secure-1PSIDTS` expiration date
    - Return false if within 7 days of expiry

- [x] Create cookie storage module `src/cookie-store.ts`:
  - Implement `saveCookies(cookies: GeminiCookie[]): Promise<void>`
    - Write cookies to storage_state.json in Playwright format
    - Use `Bun.write()` for file operations
  - Implement `loadCookies(): Promise<GeminiCookie[]>`
    - Read and parse storage_state.json
    - Throw `AuthenticationError` if file missing
    - Throw `CookieExpiredError` if cookies stale

- [x] Port auth CLI command in `src/cli.ts`:
  - Import auth module
  - Implement `auth` command:
    - Call `login()` function
    - Display success message with cookie count
    - Handle and display errors with Rich-like styling
    - Use console colors (use `console.style` or a simple library)

- [x] Add auth command error handling:
  - Catch browser startup failures
  - Catch CDP connection errors
  - Catch timeout errors (user took too long to login)
  - Display user-friendly error messages

- [ ] Test auth flow end-to-end:
  - Run `bun run src/cli.ts auth`
  - Verify LightPanda starts
  - Verify browser opens and navigates to Gemini
  - Complete login and verify cookies are saved
  - Verify cookies file format is correct

- [ ] Handle edge cases:
  - LightPanda binary not found (provide install instructions)
  - Port 9222 already in use (try alternate ports)
  - Browser crashes during auth (cleanup and retry)
  - User closes browser before login completes
