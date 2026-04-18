---
type: development
title: Developer Documentation
created: 2026-03-21
tags:
  - development
  - contributing
  - setup
related:
  - '[[ROADMAP]]'
  - '[[README]]'
---

# Developer Documentation

This guide covers development setup, project structure, and contribution guidelines.

## Project Structure

```
gemiterm/
├── src/
│   └── gemiterm/
│       ├── __init__.py          # Package init
│       ├── __main__.py          # Entry point
│       ├── cli.py               # CLI commands (Click)
│       ├── gemini_client.py     # Gemini API client
│       ├── auth_manager.py      # Playwright auth handling
│       ├── exporter.py          # Markdown/JSON export
│       ├── config.py            # Path configuration
│       ├── exceptions.py       # Custom exceptions
│       └── logging_config.py    # Logging setup
├── tests/
│   ├── __init__.py
│   ├── test_exporter.py         # Export tests
│   └── test_export_all.py       # Batch export tests
├── scripts/
│   └── demo.py                  # Demo script
├── docs/
│   ├── ROADMAP.md               # Feature roadmap
│   └── DEVELOPMENT.md           # This file
├── examples/
│   ├── sample_markdown_export.md
│   ├── sample_json_export.json
│   └── usage_examples.sh
└── pyproject.toml
```

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Chromium browser (for Playwright)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/expert-vision-software/gemiterm.git
cd gemiterm
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
playwright install chromium
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_exporter.py

# Run with coverage
pytest --cov=src
```

### Linting and Formatting

```bash
# Run ruff linter
ruff check src/

# Format code
ruff format src/
```

## Key Components

### GeminiClient (`gemini_client.py`)

The `GeminiClient` class wraps the python-gemini-api library with retry logic and error handling.

**Cookie Format**

The client expects cookies as a dictionary:
```python
cookies = {
    "__Secure-1PSID": "your_value_here",
    "__Secure-1PSIDTS": "your_value_here",
}
```

These are loaded from `storage_state.json` which stores them in the format:
```json
{
  "cookies": [
    {
      "name": "__Secure-1PSID",
      "value": "...",
      "domain": ".google.com",
      ...
    }
  ]
}
```

**API Endpoints Used**

- `GET /_/BardChatUi/data/assistant.lamda.BardFrontendService/GetChats` - List all chats
- `POST /_/BardChatUi/data/assistant.lamda.BardFrontendService/GetChat` - Fetch single chat

### GeminiModelOutput Parsing

When calling `continue_chat()`, the python-gemini-api returns a response object. The text extraction pattern:

```python
def _extract_text(self, response: Any) -> str:
    if hasattr(response, "text"):
        return response.text
    return str(response)
```

This handles the varied response types from the library gracefully.

### Exporter Module (`exporter.py`)

The exporter provides Markdown formatting with YAML front matter:

```python
from gemiterm.exporter import format_chat_as_markdown

markdown = format_chat_as_markdown(
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "model", "content": "Hi there!"},
    ],
    title="My Chat",
    conversation_id="abc123",
    include_metadata=True
)
```

**Output Structure:**
```markdown
<!-- conversation_id: abc123 -->
---
title: "My Chat"
export_date: "2026-03-21 10:30:00"
message_count: 2
---

# My Chat

**User:**

Hello

**Gemini:**

Hi there!
```

## Writing Tests

Place tests in the `tests/` directory following the `test_*.py` naming convention:

```python
from gemiterm.exporter import format_chat_as_markdown

class TestFormatChatAsMarkdown:
    def test_basic_conversation(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi!"},
        ]
        result = format_chat_as_markdown(messages, "Test")
        assert "**User:**" in result
        assert "**Gemini:**" in result
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes with tests
4. Run linting: `ruff check src/`
5. Run tests: `pytest`
6. Commit with a clear message: `git commit -m "Add feature description"`
7. Push and create a pull request

### Commit Message Format

```
MAESTRO: <description>

<optional body with more detail>
```

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for function signatures
- Docstrings for public functions
- 100 character line length

## Debugging

### Enable Verbose Logging

```bash
gemiterm -v list
```

### Check Authentication State

```bash
gemiterm status
```

### Manual Cookie Inspection

Cookies are stored in: `~/.config/gemiterm/storage_state.json`

## Architecture Decisions

### Why Click?

Click was chosen for the CLI framework because:
- Built-in subcommand support
- Automatic help generation
- Type validation for arguments
- Lightweight with no required dependencies beyond stdlib

### Why Rich?

Rich is used for formatted output because:
- Table formatting for chat lists
- Progress bars for batch operations
- Styled text output
- Already a dependency of python-gemini-api

### Cookie Storage

Cookies are stored in a JSON file rather than a database for:
- Simplicity
- Easy manual editing
- No database dependencies
- Easy export/backup