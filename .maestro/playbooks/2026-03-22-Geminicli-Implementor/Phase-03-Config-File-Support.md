# Phase 03: Config File & Persistence

This phase adds configuration file support so users don't need to pass browser flags every time. Settings are persisted in a config file (webgemini.json or .webgeminirc) in the config directory.

## Tasks

- [x] Define config file structure:
  - File: `~/.config/webgemini-cli/config.json` (or webgemini.json)
  - Schema: `{ "browser": { "type": "chromium|lightpanda|remote", "chromiumPath": "/optional/path", "remoteHost": "ws://host:port" } }`
  - Support both JSON and YAML formats if possible

- [x] Create config-file.ts module:
  - `loadConfig()` - reads and parses config file, falls back to env vars
  - `saveConfig(config)` - writes config to file
  - `getConfigPath()` - returns config file path
  - `mergeConfigFileWithEnv()` - env vars override file settings

- [x] Update config.ts to use file-based config:
  - `getBrowserType()` now checks: CLI flag > env var > config file > default
  - `getChromiumPath()` now checks: env var > config file > default
  - Add `getRemoteHost()` for remote browser connection string

- [x] Add `config set` and `config get` CLI commands:
  - `webgemini config set browser.type chromium` - updates config file
  - `webgemini config set browser.chromiumPath /custom/path` - sets Chromium path
  - `webgemini config get browser.type` - displays current value
  - `webgemini config list` - shows all current settings with sources

- [x] Add `webgemini config init` command:
  - Creates default config file with current settings
  - Helpful for new users to see available options

- [x] Update status command to show config sources:
  - Display where each setting comes from (config file, env var, default)

- [x] Test config file scenarios:
  - Create config file, verify settings are read
  - Override file setting with env var
  - Override env var with CLI flag
  - Missing config file falls back gracefully
