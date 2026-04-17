# Plan: Replace python-gemini-api with gemini-webapi

## Summary

Replace deprecated `python-gemini-api` (v2.4.12) with `gemini-webapi` (v1.21.0) which has active reverse-engineered support for Google's current Gemini API endpoints. Preserve existing functionality and enhance export fidelity.

**Status:** Pending implementation

---

## Background

The `python-gemini-api` library uses Google's deprecated BardChatUi endpoints (`/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate`) which now return 404. Google has shut down these old endpoints.

**Reference:** notebooklm-py (by teng-lin) uses the same approach - reverse-engineered Google APIs with cookie-based auth and direct HTTP calls to undocumented endpoints. This project follows that same pattern for Gemini.

---

## Research Findings

### gemini-webapi Library (HanaokaYuzu)
- **PyPI:** `gemini-webapi>=1.21.0`
- **GitHub:** 2.4k stars, active development
- **Authentication:** Cookie-based (`__Secure-1PSID`, `__Secure-1PSIDTS`)
- **API:** Fully async using `asyncio`

### Key Classes
- `GeminiClient` - Main async client
- `ChatSession` - Multi-turn conversation
- `ChatHistory` - Conversation history with rich `ChatTurn` objects
- `ChatInfo` - Chat metadata (cid, title, is_pinned)
- `ModelOutput` - Response with text, images, thoughts, candidates

### Core Methods
| Operation | Method |
|-----------|--------|
| List chats | `client.list_chats()` → `list[ChatInfo]` |
| Fetch history | `client.read_chat(cid)` → `ChatHistory` |
| Send message | `chat.send_message(text)` or `client.generate_content(text)` |

### Current webgemini-cli State
- Minimal `python-gemini-api` usage (only in `continue_chat()`)
- Browser auth already implemented via Playwright
- Direct HTTP requests used for list/fetch operations
- Rich export formatting already exists

---

## Implementation Phases

### Phase 1: Dependency & Client Migration

#### 1.1 Update `pyproject.toml`
- Remove `python-gemini-api` dependency
- Add `gemini-webapi>=1.21.0`
- Keep existing deps: click, rich, playwright, httpx/requests, pydantic

#### 1.2 Refactor `gemini_client.py`

**Key changes:**

```python
# OLD (python-gemini-api)
from gemini import Gemini
self._gemini = Gemini(cookies=self._cookies)
response = self._gemini.generate_content(message)

# NEW (gemini-webapi)
from gemini_webapi import GeminiClient
self._client = GeminiClient(secure_1psid=cookie_1psid, secure_1psidts=cookie_1psidts)
await self._client.init()
response = await self._client.generate_content(message)
```

**Methods to update:**

| Method | New Implementation |
|--------|-------------------|
| `list_chats()` | `chats = await client.list_chats()` → extract `ChatInfo.cid`, `.title` |
| `fetch_chat(conversation_id)` | `history = await client.read_chat(cid)` → extract from `ChatHistory.turns` |
| `continue_chat(message, conversation_id)` | Start chat with metadata, then `await chat.send_message(message)` |
| `__init__` | Store `GeminiClient` instance for reuse |

**Async handling:** Wrap calls in `asyncio.run()` at CLI command layer.

#### 1.3 Update `auth_manager.py`
- `GeminiClient` accepts cookies directly: `secure_1psid`, `secure_1psidts`
- Extract these specific cookies from Playwright storage state
- No format conversion needed - pass directly to constructor

---

### Phase 2: Enhance Export for Full Fidelity

#### 2.1 Update `fetch_chat` data extraction
Capture richer data from `ChatTurn` objects:
- Timestamps from `turn.model_output` metadata if available
- Images from `turn.model_output.images`
- Citations if present in model output

#### 2.2 Enhance `exporter.py`
- Support timestamps in markdown export
- Support image references/URLs
- Support citations
- Richer YAML frontmatter with `model`, `timestamp` fields

#### 2.3 Preserve backward compatibility
- JSON export format compatible with existing structure
- Add new fields without breaking existing consumers

---

### Phase 3: Testing & Verification

#### 3.1 Run existing tests
```bash
pytest tests/
```

#### 3.2 Manual testing flow
1. `webgemini-cli auth` → browser login
2. `webgemini-cli list` → verify chat listing
3. `webgemini-cli fetch <chat_id>` → verify history with richer data
4. `webgemini-cli continue-chat <chat_id> "test message"` → verify send works
5. `webgemini-cli export <chat_id>` → verify enhanced markdown

#### 3.3 Error handling
- Map `gemini_webapi` exceptions to existing `WebGeminiError` hierarchy
- Add new exceptions if needed (e.g., `RateLimitError`, `InvalidTokenError`)

---

## Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Replace dependency |
| `src/webgemini_cli/gemini_client.py` | Complete rewrite to use gemini-webapi |
| `src/webgemini_cli/auth_manager.py` | Minor updates for cookie format |
| `src/webgemini_cli/exporter.py` | Enhanced for richer data |

## Files to Test (shouldn't need changes)

- `tests/test_exporter.py`
- `tests/test_export_all.py`

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| Implementation approach | Use gemini-webapi as dependency |
| Feature scope | Core chat + history + full fidelity export |
| Streaming support | No - wait for complete response |
| Async handling | Wrap in `asyncio.run()` at CLI layer |

---

## Notes

- The `gemini-webapi` library is async-only, so all client operations must be awaited
- Cookie auto-refresh is enabled by default in gemini-webapi
- `GeminiClient` can also auto-import cookies from browser if `browser-cookie3` is installed
