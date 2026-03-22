# Phase 03: Export & Documentation

Implement polished Markdown export functionality and comprehensive documentation. This phase completes the core feature set with professional-grade export capabilities and documents the architecture, usage patterns, and future roadmap.

## Tasks

- [x] Create export formatter module `src/webgemini_cli/exporter.py`:
  - Implement `format_chat_as_markdown(messages: list[dict], title: str) -> str` function
  - Include YAML front matter with metadata (title, export_date, message_count)
  - Format user messages with `**User:**` prefix
  - Format assistant messages with `**Gemini:**` prefix
  - Handle code blocks with proper syntax highlighting hints
  - Add timestamps if available in message data
  - Add conversation ID as comment in header

- [x] Enhance export CLI command with options:
  - Add `--output` / `-o` for custom output file path
  - Add `--format` option supporting `markdown` (default) and `json`
  - Add `--include-metadata` flag to include full metadata in export
  - Default filename pattern: `gemini-chat-{conversation_id}-{date}.md`
  - Create output directory if it doesn't exist
  - Print success message with file path

- [x] Create batch export functionality:
  - Add `webgemini export-all` command with `--output-dir` option
  - Export all conversations to individual Markdown files
  - Create index file `_index.md` listing all exported chats with links
  - Add `--since` option to export only recent conversations
  - Display progress bar during batch export

- [x] Create comprehensive documentation:
  - Expand README.md with:
    - Prerequisites section (Python 3.11+, Chromium browser)
    - Step-by-step authentication guide
    - Detailed command reference with examples
    - Troubleshooting common issues
    - Configuration options and environment variables
  - Add architecture diagram (text-based) showing component relationships
  - Document the auth flow: Playwright → cookies → python-gemini-api

- [ ] Document future enhancement roadmap:
  - Create `docs/ROADMAP.md` with planned features:
    - **Interactive CLI Mode**: Menu-driven interface for browsing chats
    - **REPL Mode**: Continuous chat session with conversation history
    - **Search**: Full-text search across all conversations
    - **Sync**: Keep local cache of conversations for offline access
    - **Multi-account**: Support multiple Google accounts with profiles
  - Include estimated complexity and dependencies for each

- [ ] Create developer documentation:
  - Add `docs/DEVELOPMENT.md` with:
    - Project structure explanation
    - How to set up development environment
    - How to run tests
    - How to contribute
  - Document the cookie format expected by python-gemini-api
  - Document the GeminiModelOutput parsing approach

- [ ] Add example outputs:
  - Create `examples/` directory
  - Add sample exported Markdown file showing output format
  - Add sample JSON export for comparison
  - Add screenshots of CLI output (as text files) for documentation

- [ ] Create usage examples script:
  - Add `examples/usage_examples.sh` with commented command sequences
  - Cover common workflows: first-time setup, daily usage, export for backup
  - Include error scenarios and expected outputs
