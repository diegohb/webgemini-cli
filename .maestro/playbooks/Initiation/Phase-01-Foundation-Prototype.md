# Phase 01: Foundation & Working Prototype

Build the complete foundation for webgemini-cli - a Python CLI tool that bridges Playwright-based Google authentication with the python-gemini-api library. This phase delivers a fully functional prototype with all 5 commands working end-to-end.

## Tasks

- [x] Initialize Python project structure:
  - Create `src/webgemini_cli/` package directory
  - Create `pyproject.toml` with project metadata (name: webgemini-cli, version: 0.1.0)
  - Configure dependencies: `python-gemini-api`, `playwright`, `click`, `rich` (for CLI output)
  - Add optional dev dependencies: `pytest`, `ruff`
  - Create `.python-version` file (3.11+)
  - NOTE: First task completed - project structure initialized

- [x] Create configuration module `src/webgemini_cli/config.py`:
  - Define `CONFIG_DIR` default: `~/.config/webgemini-cli/`
  - Define `STORAGE_STATE_FILE` default: `storage_state.json`
  - Create `get_storage_state_path()` function returning full path
  - Create `ensure_config_dir()` function to create directory if missing
  - Support `WEBGEMINI_CONFIG_DIR` environment variable override

- [x] Create auth manager `src/webgemini_cli/auth_manager.py`:
  - Import Playwright async API
  - Implement `login()` async function that:
    - Launches Chromium browser with `headless=False`
    - Navigates to `https://gemini.google.com`
    - Waits for user to complete Google login (detect successful auth)
    - Extracts `__Secure-1PSID` and `__Secure-1PSIDTS` cookies
    - Saves cookies to `storage_state.json` in Playwright format
    - Closes browser immediately after cookie capture
  - Implement `load_cookies()` function that reads `storage_state.json` and returns dict

- [ ] Create Gemini client wrapper `src/webgemini_cli/gemini_client.py`:
  - Import `Gemini` from `python_gemini_api`
  - Implement `GeminiClient` class with:
    - `__init__(self, cookies: dict)` - initialize Gemini client with cookies
    - `list_chats(self) -> list[dict]` - return list of {id, title} for all chats
    - `fetch_chat(self, conversation_id: str) -> list[dict]` - return full message history
    - `continue_chat(self, conversation_id: str, message: str) -> str` - send message, return response text
    - `_extract_text(self, response) -> str` - helper to extract `.text` from `GeminiModelOutput`

- [ ] Create CLI application `src/webgemini_cli/cli.py`:
  - Use Click for CLI framework with `@click.group()`
  - Implement `auth` command: runs Playwright login flow, prints success message
  - Implement `list` command: loads cookies, calls `list_chats()`, displays table with Rich
  - Implement `fetch <conversation_id>` command: loads cookies, fetches history, prints messages
  - Implement `continue <conversation_id> <message>` command: sends message, prints response
  - Implement `export <conversation_id>` command: fetches chat, saves to Markdown file

- [ ] Create entry point `src/webgemini_cli/__main__.py`:
  - Import cli group from cli.py
  - Call `cli()` when run as module

- [ ] Configure pyproject.toml entry points:
  - Add `[project.scripts]` section with `webgemini = "webgemini_cli.cli:cli"`
  - Ensure package is installable with `pip install -e .`

- [ ] Create initial test script `scripts/demo.py`:
  - Script that demonstrates the deliverable: list 5 most recent chats
  - Append "Hello from the API" to the most recent chat
  - Print confirmation of actions taken

- [ ] Install dependencies and verify:
  - Run `pip install -e .`
  - Run `playwright install chromium`
  - Test `webgemini --help` shows all commands
  - Create `requirements.txt` for non-editable installs

- [ ] Create basic README.md:
  - Project description and purpose
  - Installation instructions
  - Usage examples for all 5 commands
  - Note about future interactive CLI and REPL modes as potential enhancements
