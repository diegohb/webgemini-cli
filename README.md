# webgemini-cli

A TypeScript CLI tool that bridges LightPanda browser automation with Gemini web API via a Python subprocess wrapper.

## Prerequisites

- **Bun**: Version 1.0 or higher ([Install](https://bun.sh))
- **LightPanda Browser**: Required for authentication ([Install](https://lightpanda.dev))
- **Python**: Version 3.11 or higher (for the Python wrapper)
- **Google Account**: A Google account with access to Gemini (https://gemini.google.com)

### Browser Installation

LightPanda is required for authentication. Install it via npm:

```bash
npm install -g @lightpanda/browser
```

Or visit https://lightpanda.dev for alternative installation methods.

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/webgemini-cli.git
cd webgemini-cli

# Install dependencies
bun install

# Build the CLI (optional, for faster startup)
bun run build
```

The CLI can be run directly with `bun run src/cli.ts` or via the built binary at `dist/webgemini-cli`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         webgemini-cli                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │     CLI      │────▶│   Gemini     │────▶│    Auth      │    │
│  │  (TypeScript)│     │   Client     │     │   Manager    │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │            │
│         │                    │                    ▼            │
│         │                    │            ┌──────────────┐    │
│         │                    │            │  LightPanda  │    │
│         │                    │            │   Browser    │    │
│         │                    │            └──────────────┘    │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Console     │     │   Python     │     │    Cookie    │   │
│  │    Output     │     │  Subprocess  │     │    Store     │   │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | File | Purpose |
|-----------|------|---------|
| **CLI** | `src/cli.ts` | Command-line interface using Commander.js |
| **GeminiClient** | `src/gemini-client.ts` | TypeScript wrapper for Python subprocess |
| **AuthManager** | `src/auth.ts` | LightPanda browser automation for login |
| **PythonWrapper** | `python/wrapper.py` | JSON-based subprocess protocol for Gemini API |
| **CookieStore** | `src/cookie-store.ts` | Persistent cookie storage |

### TypeScript + Python Architecture

The CLI is written in TypeScript for:
- Fast startup with Bun
- Modern async/await patterns
- Type safety

Python is used for the Gemini API interaction layer because:
- The python-gemini-api library handles complex API semantics
- Existing robust implementation in the `webgemini_cli` Python package

Communication happens via JSON over stdin/stdout subprocess protocol.

## Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. User runs 'webgemini auth'                                   │
│            │                                                      │
│            ▼                                                      │
│   2. LightPanda launches Chromium browser (headless=False)       │
│            │                                                      │
│            ▼                                                      │
│   3. Navigate to https://gemini.google.com                       │
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
│   6. Cookies captured and saved to storage_state.json            │
│            │                                                      │
│            ▼                                                      │
│   7. GeminiClient sends cookies to Python wrapper for API calls  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Cookie Format

The Python Gemini API expects cookies in a specific JSON format:

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
bun run src/cli.ts auth
```

Or with the built binary:

```bash
./dist/webgemini.exe auth  # Windows
./dist/webgemini auth      # Unix/macOS
```

This will open a browser window for you to log in with your Google account. Cookies will be saved for future use.

### Check Status

Verify your authentication status:

```bash
bun run src/cli.ts status
```

### List Chats

Display all your Gemini chats in a table:

```bash
bun run src/cli.ts list
```

Options:
- `-n, --limit <number>`: Maximum number of chats to display (default: 10, max: 50)

### Fetch Chat History

Fetch and display the message history of a specific conversation:

```bash
bun run src/cli.ts fetch <conversation-id>
```

Options:
- `-f, --format <format>`: Output format - `text` (default) or `json`

### Continue a Chat

Send a message to an existing conversation:

```bash
bun run src/cli.ts continue <conversation-id> <message>
```

### Export Chat

Export a conversation to a Markdown file:

```bash
bun run src/cli.ts export <conversation-id>
```

Options:
- `-o, --output <path>`: Custom output file path
- `-f, --format <format>`: Export format - `markdown` (default) or `json`
- `--include-metadata`: Include full metadata in export

Default filename pattern: `gemini-chat-{conversation_id}-{date}.md`

### Export All Chats

Export all conversations to a directory with an index file:

```bash
bun run src/cli.ts export-all
```

Options:
- `-o, --output-dir <directory>`: Directory to export to (default: `./exports`)
- `--since <date>`: Export only conversations newer than this date
- `--include-metadata`: Include full metadata in each export

This creates:
- Individual Markdown files for each conversation
- An `_index.md` file with links to all exported chats

### Verbose Logging

Enable detailed logging for debugging:

```bash
bun run src/cli.ts -v <command>
```

## Configuration

### Configuration Directory

Default location: `~/.config/webgemini-cli/`

Override with environment variable:
```bash
export WEBGEMINI_CONFIG_DIR=/custom/path
```

### Storage File

The storage file (`storage_state.json`) contains your authentication cookies. It is located in the configuration directory.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBGEMINI_CONFIG_DIR` | Configuration directory | `~/.config/webgemini-cli/` |
| `WEBGEMINI_VERBOSE` | Enable verbose logging | `false` |
| `PYTHON_WRAPPER_PATH` | Path to Python wrapper script | `<project>/python/wrapper.py` |

## Python Wrapper Protocol

The Python wrapper communicates via JSON over stdin/stdout. This allows the TypeScript CLI to delegate Gemini API operations to Python.

### Request Format

```json
{
  "command": "list_chats" | "fetch_chat" | "continue_chat",
  "cookies": { "cookie_name": "cookie_value", ... },
  "params": { ... }
}
```

### Commands

#### list_chats
```json
{
  "command": "list_chats",
  "cookies": { "__Secure-1PSID": "...", "__Secure-1PSIDTS": "..." },
  "params": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    { "id": "abc123", "title": "Chat Title" }
  ],
  "error": null
}
```

#### fetch_chat
```json
{
  "command": "fetch_chat",
  "cookies": { "__Secure-1PSID": "...", "__Secure-1PSIDTS": "..." },
  "params": { "conversation_id": "abc123" }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    { "role": "user", "content": "Hello", "conversation_id": "abc123" },
    { "role": "model", "content": "Hi there!", "conversation_id": "abc123" }
  ],
  "error": null
}
```

#### continue_chat
```json
{
  "command": "continue_chat",
  "cookies": { "__Secure-1PSID": "...", "__Secure-1PSIDTS": "..." },
  "params": { "conversation_id": "abc123", "message": "Hello!" }
}
```

**Response:**
```json
{
  "success": true,
  "data": "Model response text",
  "error": null
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "AuthenticationError",
    "message": "Missing required cookies"
  }
}
```

## Troubleshooting

### LightPanda Not Found

If you see "LightPanda not found" errors:

1. Install LightPanda globally:
   ```bash
   npm install -g @lightpanda/browser
   ```

2. Or visit https://lightpanda.dev for alternative installation methods

### Browser Automation Issues

If browser automation fails or is unavailable, you can manually extract cookies from your browser:

1. Install the "EditThisCookie" extension or similar in your browser
2. Go to https://gemini.google.com and log in
3. Export the cookies in JSON format
4. Save them to `~/.config/webgemini-cli/storage_state.json` with the following format:
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

1. Run `bun run src/cli.ts auth` to re-authenticate
2. If the issue persists, delete `storage_state.json` and run `bun run src/cli.ts auth` again

### Python Wrapper Errors

If you see Python-related errors:

1. Ensure Python 3.11+ is installed:
   ```bash
   python --version
   ```

2. Ensure the Python dependencies are available. The wrapper uses the `webgemini_cli` package from `python/`

### API Errors

If you encounter API errors:

1. Run `bun run src/cli.ts status` to check your authentication state
2. Ensure you have a valid Google account with Gemini access
3. Try re-authenticating with `bun run src/cli.ts auth`

### Verbose Logging

Use the `-v` or `--verbose` flag to enable detailed logging for debugging:

```bash
bun run src/cli.ts -v list
```

## Building

Build a standalone executable:

```bash
bun run build
```

The output will be in `dist/webgemini.exe` (Windows) or `dist/webgemini` (Unix/macOS). The standalone executable is a single file containing the Bun runtime and all dependencies, approximately 110 MB in size.

## Testing

Run tests with:

```bash
bun test
```

## Project Structure

```
webgemini-cli/
├── src/                    # TypeScript source
│   ├── cli.ts              # CLI entry point
│   ├── index.ts            # Module exports
│   ├── auth.ts             # Authentication manager
│   ├── browser.ts          # Browser process management
│   ├── cdp-client.ts       # Chrome DevTools Protocol client
│   ├── config.ts           # Configuration utilities
│   ├── cookie-store.ts     # Cookie persistence
│   ├── errors.ts           # Error classes
│   ├── exporter.ts         # Export formatting
│   ├── gemini-client.ts    # Gemini API client wrapper
│   ├── python-wrapper.ts   # Python subprocess protocol
│   └── types/
│       └── index.ts        # TypeScript type definitions
├── python/                 # Python wrapper
│   ├── wrapper.py          # JSON protocol entry point
│   ├── webgemini_cli/      # Python package
│   │   ├── __init__.py
│   │   ├── gemini_client.py
│   │   ├── exceptions.py
│   │   ├── auth_manager.py
│   │   ├── config.py
│   │   ├── exporter.py
│   │   └── logging_config.py
│   ├── pyproject.toml
│   └── requirements.txt
├── tests/                  # TypeScript tests
├── dist/                   # Build output
├── package.json
├── tsconfig.json
└── README.md
```

## Future Enhancements

- Interactive CLI mode with menu-driven navigation
- REPL mode for conversational interaction
- Support for conversation creation and deletion
- Export to multiple formats (HTML, PDF)
