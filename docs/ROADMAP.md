---
type: roadmap
title: Future Enhancement Roadmap
created: 2026-03-21
tags:
  - planning
  - features
related:
  - '[[DEVELOPMENT]]'
  - '[[README]]'
---

# Future Enhancement Roadmap

This document outlines planned features and enhancements for webgemini-cli.

## Interactive CLI Mode

Menu-driven interface for browsing and managing chats without remembering commands.

**Status:** Planned  
**Estimated Complexity:** Medium  
**Dependencies:** Click framework, Rich library (already in use)

**Features:**
- Interactive menu to browse chat history
- Keyboard navigation support
- Preview chat messages before selection
- Quick actions: export, continue, delete

**Implementation Approach:**
```python
# Pseudocode for menu structure
@cli.command()
def interactive():
    """Launch interactive chat browser"""
    while True:
        display_menu()
        choice = get_input()
        if choice == 'q': break
        handle_selection(choice)
```

---

## REPL Mode

Continuous chat session with full conversation history maintained locally.

**Status:** Planned  
**Estimated Complexity:** High  
**Dependencies:** python-gemini-api, conversation state management

**Features:**
- Persistent conversation context across messages
- Command history (up/down arrows)
- Ability to switch between conversations
- Session timeout handling
- Markdown rendering of responses

**Implementation Approach:**
```python
# Pseudocode for REPL structure
async def repl_mode(client: GeminiClient):
    """Interactive REPL for continuous chat"""
    conversation_id = None
    while True:
        user_input = await prompt_async(">>> ")
        if user_input.startswith("/"):
            handle_command(user_input)
        else:
            response = client.continue_chat(conversation_id, user_input)
            print(response)
```

---

## Full-Text Search

Search across all conversations with indexing for fast retrieval.

**Status:** Planned  
**Estimated Complexity:** Medium  
**Dependencies:** SQLite with FTS5, Whoosh, or Elasticsearch

**Features:**
- Index all conversation content
- Search by keywords, date range, or both
- Highlight matching text in results
- Rank results by relevance
- Support for regex patterns

**Implementation Approach:**
```python
# Conceptual search implementation
class ConversationSearch:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS "
                          "conversations USING fts5(content, title)")

    def index_conversation(self, chat_id: str, content: str):
        """Index a conversation for searching"""

    def search(self, query: str) -> list[SearchResult]:
        """Search indexed conversations"""
```

---

## Offline Sync

Keep local cache of conversations for offline access and faster loading.

**Status:** Planned  
**Estimated Complexity:** High  
**Dependencies:** SQLite, polling机制 or Webhooks

**Features:**
- Sync conversations on startup
- Background sync at configurable intervals
- Conflict resolution for concurrent edits
- Compressed storage for large histories
- Export/import functionality for migration

**Implementation Approach:**
```python
# Conceptual sync implementation
class ConversationCache:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._create_tables()

    def sync_all(self, client: GeminiClient):
        """Sync all conversations to local cache"""
        remote_chats = client.list_chats()
        for chat in remote_chats:
            self._upsert_chat(chat)

    def get_cached_messages(self, chat_id: str) -> list[dict]:
        """Retrieve from cache, refresh if stale"""
```

---

## Multi-Account Support

Support multiple Google accounts with isolated profiles.

**Status:** Planned  
**Estimated Complexity:** Medium  
**Dependencies:** Keyring or encrypted config storage

**Features:**
- Named profiles (e.g., `webgemini --profile work list`)
- Separate cookie storage per profile
- Easy profile switching
- Profile-specific configuration options
- Secure credential storage

**Implementation Approach:**
```python
# Conceptual multi-account structure
@dataclass
class Profile:
    name: str
    cookie_path: Path
    config_dir: Path

class ProfileManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def switch_profile(self, name: str) -> Profile:
        """Switch to named profile"""

    def list_profiles(self) -> list[Profile]:
        """List all available profiles"""
```

---

## Priority Order

1. **Interactive CLI Mode** - Lowest barrier to entry, improves UX significantly
2. **REPL Mode** - Core use case enhancement for power users
3. **Full-Text Search** - Essential for users with large chat histories
4. **Offline Sync** - Reliability and performance improvement
5. **Multi-Account** - Complex due to security considerations

---

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for guidance on contributing to webgemini-cli.
