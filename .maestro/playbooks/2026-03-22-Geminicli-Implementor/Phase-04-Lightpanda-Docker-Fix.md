# Phase 04: LightPanda Docker Fix & Fallback Logic

This phase fixes the LightPanda Docker implementation bug and adds intelligent fallback behavior when LightPanda fails. Chromium becomes the reliable fallback.

## Tasks

- [x] Investigate LightPanda Docker bug:
  - Check docker.ts to understand current Docker provisioning
  - Identify what specifically is failing (container start, CDP connection, etc.)
  - Look at LightPanda Docker logs for clues
  - Check if @lightpanda/browser has Docker-specific API changes

- [x] Fix Docker container provisioning in docker.ts:
  - Ensure container is removed/recreated properly on each run
  - Fix port mapping to avoid conflicts
  - Add proper wait time for container to be ready
  - Verify WS endpoint is correctly exposed

- [x] Add browser fallback logic to browser.ts:
  - If LightPanda fails (not found, port issues, connection error), automatically try Chromium
  - Log which browser is being attempted and why
  - If user explicitly chose lightpanda and it fails, still try chromium as fallback
  - Add `BROWSER_FALLBACK=true|false` env var to disable fallback if desired

- [x] Add verbose logging for browser selection:
  - Log when switching browsers due to failure
  - Log CDP connection details for debugging
  - Add `--debug-browser` flag for detailed browser debugging

- [x] Update error messages to be more helpful:
  - When LightPanda fails, suggest Chromium as alternative
  - Provide clear instructions on how to install Chromium if missing
  - Show which browser was successfully used if fallback occurred

- [x] Test fallback scenarios:
  - Force LightPanda failure by setting wrong port, verify Chromium fallback works
  - Verify Chromium is default when LightPanda Docker bug occurs
  - Test that `--browser=chromium` never triggers fallback
  - Test that `BROWSER_FALLBACK=false` disables automatic fallback
