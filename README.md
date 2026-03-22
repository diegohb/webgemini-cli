# webgemini-cli

A Python CLI tool that bridges Playwright-based Google authentication with the python-gemini-api library.

## Installation

```bash
pip install -e .
playwright install chromium
```

## Usage

### Authentication

Before using the CLI, you need to authenticate with your Google account:

```bash
webgemini auth
```

This will open a browser window for you to log in with your Google account. Cookies will be saved for future use.

### List Chats

Display all your Gemini chats in a table:

```bash
webgemini list
```

### Fetch Chat History

Fetch and display the message history of a specific conversation:

```bash
webgemini fetch <conversation_id>
```

### Continue a Chat

Send a message to an existing conversation:

```bash
webgemini continue <conversation_id> <message>
```

### Export Chat

Export a conversation to a Markdown file:

```bash
webgemini export <conversation_id> <output_file.md>
```

## Demo Script

A demo script is available at `scripts/demo.py` that demonstrates the library's functionality by listing 5 most recent chats and appending "Hello from the API" to the most recent chat.

## Configuration

- Config directory: `~/.config/webgemini-cli/` (configurable via `WEBGEMINI_CONFIG_DIR` environment variable)
- Storage file: `storage_state.json` (contains authentication cookies)

## Troubleshooting

### Authentication Issues

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

### Verbose Logging

Use the `-v` or `--verbose` flag to enable detailed logging for debugging:
```bash
webgemini -v list
```

## Future Enhancements

- Interactive CLI mode with menu-driven navigation
- REPL mode for conversational interaction
- Support for conversation creation and deletion
- Export to multiple formats (HTML, PDF)
