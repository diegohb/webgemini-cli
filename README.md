# webgemini-cli

A TypeScript CLI tool that bridges LightPanda browser automation with Gemini web API.

## Prerequisites

- **Bun**: Version 1.0 or higher ([Install](https://bun.sh))
- **Chromium**: Required for authentication (system-installed or specify custom path)
- **Python**: Version 3.11 or higher (for the Python wrapper)
- **Google Account**: A Google account with access to Gemini (https://gemini.google.com)

### Browser Installation

Chromium is used by default for authentication. Install it via your system's package manager:

```bash
# macOS (Homebrew)
brew install chromium

# Ubuntu/Debian
sudo apt install chromium

# Windows (Scoop)
scoop install chromium
```

Or specify a custom path to an existing Chromium-based browser (Chrome, Edge, etc.) via the `CHROMIUM_PATH` environment variable.

### Alternative: LightPanda Browser

LightPanda is a lightweight headless browser alternative. Install it via npm:

```bash
npm install -g @lightpanda/browser
```

Or visit https://lightpanda.dev for alternative installation methods. Use `--browser lightpanda` to switch.

### Docker Installation (LightPanda)

You can also run LightPanda in Docker:

```bash
# Install and run LightPanda
docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly

# Start existing container
docker start lightpanda

# Stop container
docker stop lightpanda
```

For automatic Docker provisioning, set `LIGHTPANDA_DOCKER=true` when running the auth command with `--browser lightpanda`.

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
│         │                    │            │   Chromium   │    │
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
| **GeminiClient** | `src/gemini-client.ts` | Gemini API client |
| **AuthManager** | `src/auth.ts` | Browser automation for login (Chromium/LightPanda) |
| **CookieStore** | `src/cookie-store.ts` | Persistent cookie storage |

### Architecture

The CLI is written in TypeScript using Bun for fast startup and type safety. Gemini API calls are delegated to a Python subprocess wrapper via JSON over stdin/stdout.

## Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. User runs 'webgemini auth'                                   │
│            │                                                      │
│            ▼                                                      │
│   2. Chromium browser launches (headless=False)                  │
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
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Cookie Format

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

#### Alternative Browsers

Use LightPanda or connect to a remote browser:

```bash
# Using LightPanda
webgemini auth --browser lightpanda

# Using Docker auto-provisioning for LightPanda
LIGHTPANDA_DOCKER=true webgemini auth --browser lightpanda

# Using a specific remote host
webgemini auth --browser remote --remote-host ws://localhost:9222

# Using environment variable
LIGHTPANDA_HOST=ws://localhost:9222 webgemini auth --browser remote
```

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
| `BROWSER_TYPE` | Browser to use (`chromium`, `lightpanda`, `remote`) | `chromium` |
| `CHROMIUM_PATH` | Custom Chromium executable path | none |
| `LIGHTPANDA_HOST` | Remote LightPanda WebSocket URL | none |
| `LIGHTPANDA_DOCKER` | Auto-provision Docker container | `false` |
| `REMOTE_HOST` | Remote browser WebSocket URL (alternative to LIGHTPANDA_HOST) | none |
| `BROWSER_FALLBACK` | Fall back to Chromium if selected browser fails | `true` |

### Browser Configuration

The CLI supports multiple browser types with flexible configuration:

#### Browser Types

| Type | Description |
|------|-------------|
| `chromium` | Use Chromium (system-installed or Chromium-based browser) - **default** |
| `lightpanda` | Use LightPanda browser |
| `remote` | Connect to a remote browser via WebSocket |

#### CLI Flag

```bash
# Use Chromium
webgemini auth --browser chromium

# Use LightPanda
webgemini auth --browser lightpanda

# Use remote browser
webgemini auth --browser remote --remote-host ws://localhost:9222
```

#### Environment Variables

```bash
# Set browser type
export BROWSER_TYPE=chromium

# Set custom Chromium path
export CHROMIUM_PATH=/path/to/chromium

# Set remote browser
export LIGHTPANDA_HOST=ws://localhost:9222

# Disable fallback to Chromium on failure
export BROWSER_FALLBACK=false
```

#### Config File

Create `~/.config/webgemini-cli/config.json` or `~/.config/webgemini-cli/.webgeminirc`:

```json
{
  "browser": {
    "type": "chromium",
    "chromiumPath": "/custom/path/to/chromium",
    "remoteHost": "ws://localhost:9222"
  }
}
```

#### Precedence

Configuration values are resolved in this order (highest to lowest):

1. **CLI flags** (e.g., `--browser chromium`)
2. **Environment variables** (e.g., `BROWSER_TYPE=chromium`)
3. **Config file** (e.g., `~/.config/webgemini-cli/config.json`)
4. **Default values** (`chromium`, no custom path)

Example: If `BROWSER_TYPE=lightpanda` is set in the environment but `--browser chromium` is passed via CLI, the CLI value takes precedence.

## Python Wrapper

The CLI delegates Gemini API operations to a Python subprocess (`python/wrapper.py`) using JSON over stdin/stdout.

## Troubleshooting

### Docker LightPanda Not Running

If you're using Docker LightPanda and authentication fails:

1. Check if Docker is running:
   ```bash
   docker ps -a | grep lightpanda
   ```

2. Start the container:
   ```bash
   docker start lightpanda
   ```

3. Or recreate the container:
   ```bash
   docker stop lightpanda
   docker rm lightpanda
   docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly
   ```

4. Use automatic provisioning:
   ```bash
   LIGHTPANDA_DOCKER=true webgemini auth
   ```

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

### Chromium Not Found

If you see "Chromium not found" errors:

1. Install Chromium or use an existing installation:
   ```bash
   # On macOS with Homebrew
   brew install chromium

   # On Ubuntu/Debian
   sudo apt install chromium
   ```

2. Or specify a custom Chromium path:
   ```bash
   export CHROMIUM_PATH=/path/to/your/chromium
   webgemini auth --browser chromium
   ```

### Remote Browser Connection Failed

If you see "Remote browser connection failed" errors:

1. Ensure the remote browser is running and accessible:
   ```bash
   # Check if remote browser is reachable
   curl -I http://localhost:9222
   ```

2. Verify the WebSocket URL is correct:
   ```bash
   webgemini auth --browser remote --remote-host ws://localhost:9222
   ```

3. For Docker-based remote browsers, ensure the container is running:
   ```bash
   docker ps | grep lightpanda
   docker logs lightpanda
   ```

### Wrong Browser Type

If the wrong browser is being used:

1. Check current configuration:
   ```bash
   webgemini status
   ```

2. Override with CLI flag (takes highest precedence):
   ```bash
   webgemini auth --browser chromium
   ```

3. Or set environment variable:
   ```bash
   export BROWSER_TYPE=chromium
   ```

4. Check config file if CLI/env not set:
   ```bash
   cat ~/.config/webgemini-cli/config.json
   ```

### Session Expired

If you see "Session expired" errors:

1. Run `bun run src/cli.ts auth` to re-authenticate
2. If the issue persists, delete `storage_state.json` and run `bun run src/cli.ts auth` again

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
├── python/                 # Python wrapper (Gemini API)
├── tests/                  # TypeScript tests
├── dist/                   # Build output
└── README.md
```

## Future Enhancements

- Interactive CLI mode with menu-driven navigation
- REPL mode for conversational interaction
- Support for conversation creation and deletion
- Export to multiple formats (HTML, PDF)
