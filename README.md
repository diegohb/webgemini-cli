# gemiterm

A Python CLI tool that bridges Playwright-based Google authentication with the python-gemini-api library.

## Prerequisites

- **Python**: Version 3.11 or higher
- **Chromium Browser**: Required by Playwright for authentication
- **Google Account**: A Google account with access to Gemini (https://gemini.google.com)

### Installation

```bash
pip install -e .
playwright install chromium
```

> **Note**: If you encounter issues with Playwright, ensure you have the necessary system dependencies:
> ```bash
> playwright install-deps
> ```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         gemiterm                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │     CLI      │────▶│   Gemini     │────▶│    Auth      │    │
│  │   (click)    │     │   Client     │     │   Manager    │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │            │
│         │                    │                    ▼            │
│         │                    │            ┌──────────────┐    │
│         │                    │            │   Playwright │    │
│         │                    │            │   (Browser)  │    │
│         │                    │            └──────────────┘    │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Rich UI    │     │    python    │     │   Cookie     │    │
│  │  (tables,    │     │   -gemini    │     │    Store     │    │
│  │   progress)  │     │     -api     │     │  (JSON file) │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | File | Purpose |
|-----------|------|---------|
| **CLI** | `cli.py` | Command-line interface using Click framework |
| **GeminiClient** | `gemini_client.py` | Interacts with Gemini API using cookies |
| **AuthManager** | `auth_manager.py` | Handles Playwright browser automation for login |
| **Exporter** | `exporter.py` | Formats conversations as Markdown/JSON |
| **Config** | `config.py` | Manages configuration directories and paths |

## Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. User runs 'gemiterm auth'                                   │
│            │                                                      │
│            ▼                                                      │
│   2. Playwright launches Chromium browser (headless=False)       │
│            │                                                      │
│            ▼                                                      │
│   3. Navigate to https://gemini.google.com                        │
│            │                                                      │
│            ▼                                                      │
│   4. User manually logs in with Google credentials               │
│            │                                                      │
│            ▼                                                      │
│   5. Script polls for required cookies:                          │
│       - __Secure-1PSID                                            │
│       - __Secure-1PSIDTS                                          │
│            │                                                      │
│            ▼                                                      │
│   6. Cookies captured and saved to storage_state.json             │
│            │                                                      │
│            ▼                                                      │
│   7. GeminiClient uses cookies for API requests                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Cookie Format

The python-gemini-api library expects cookies in a specific JSON format:

```json
{
  "cookies": [
    {
      "name": "__Secure-1PSID",
      "value": "your_value_here",
      "domain": ".google.com",
      "path": "/",
      "expires": -1,
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    },
    {
      "name": "__Secure-1PSIDTS",
      "value": "your_value_here",
      "domain": ".google.com",
      "path": "/",
      "expires": 1234567890,
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    }
  ]
}
```

### Session Expiry

Sessions typically expire when the `__Secure-1PSIDTS` cookie expires. The CLI checks cookie freshness and will prompt you to re-authenticate when the session is close to expiry (within 7 days of expiration).

## Usage

### Authentication

Before using the CLI, you need to authenticate with your Google account:

```bash
gemiterm auth
```

This will open a browser window for you to log in with your Google account. Cookies will be saved for future use.

### Check Status

Verify your authentication status:

```bash
gemiterm status
```

### List Chats

Display all your Gemini chats in a table:

```bash
gemiterm list
```

Options:
- `-n, --limit N`: Maximum number of chats to display (default: 10, max: 50)

### Fetch Chat History

Fetch and display the message history of a specific conversation:

```bash
gemiterm fetch <conversation_id>
```

Options:
- `--format, -f`: Output format - `text` (default) or `json`

### Continue a Chat

Send a message to an existing conversation:

```bash
gemiterm continue <conversation_id> <message>
```

### Export Chat

Export a conversation to a Markdown file:

```bash
gemiterm export <conversation_id>
```

Options:
- `-o, --output PATH`: Custom output file path
- `-f, --format FORMAT`: Export format - `markdown` (default) or `json`
- `--include-metadata`: Include full metadata in export

Default filename pattern: `gemini-chat-{conversation_id}-{date}.md`

### Export All Chats

Export all conversations to a directory with an index file:

```bash
gemiterm export-all
```

Options:
- `-o, --output-dir PATH`: Directory to export to (default: `./exports`)
- `--since ISO_DATE`: Export only conversations newer than this date
- `--include-metadata`: Include full metadata in each export

This creates:
- Individual Markdown files for each conversation
- An `_index.md` file with links to all exported chats

### Verbose Logging

Enable detailed logging for debugging:

```bash
gemiterm -v <command>
```

## Configuration

### Configuration Directory

Default location: `~/.config/gemiterm/`

Override with environment variable:
```bash
export GEMITERM_CONFIG_DIR=/custom/path
```

### Storage File

The storage file (`storage_state.json`) contains your authentication cookies. It is located in the configuration directory.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMITERM_CONFIG_DIR` | Configuration directory | `~/.config/gemiterm/` |
| `GEMITERM_VERBOSE` | Enable verbose logging | `false` |

## Demo Script

A demo script is available at `scripts/demo.py` that demonstrates the library's functionality by listing 5 most recent chats and appending "Hello from the API" to the most recent chat.

```bash
python scripts/demo.py
```

## Troubleshooting

### Browser Automation Issues

If browser automation fails or is unavailable, you can manually extract cookies from your browser:

1. Install the "EditThisCookie" extension or similar in your browser
2. Go to https://gemini.google.com and log in
3. Export the cookies in JSON format
4. Save them to `~/.config/gemiterm/storage_state.json` with the following format:
   ```json
   {
     "cookies": [
       {"name": "__Secure-1PSID", "value": "your_value_here", ...},
       {"name": "__Secure-1PSIDTS", "value": "your_value_here", ...}
     ]
   }
   ```

### Session Expired

If you see "Session expired" errors:

1. Run `gemiterm auth` to re-authenticate
2. If the issue persists, delete `storage_state.json` and run `gemiterm auth` again

### API Errors

If you encounter API errors:

1. Run `gemiterm status` to check your authentication state
2. Ensure you have a valid Google account with Gemini access
3. Try re-authenticating with `gemiterm auth`

### Verbose Logging

Use the `-v` or `--verbose` flag to enable detailed logging for debugging:

```bash
gemiterm -v list
```

## Future Enhancements

- Interactive CLI mode with menu-driven navigation
- REPL mode for conversational interaction
- Support for conversation creation and deletion
- Export to multiple formats (HTML, PDF)