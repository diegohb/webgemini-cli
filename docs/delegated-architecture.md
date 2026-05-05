# GemiTerm Architecture Refactoring & Upstream Delegation Plan

> **Updated**: 2026-05-05 | Based on `main` at commit `6185720` (v1.3.0, multi-profile auth)
> **Strategy**: Use upstream `gemini_webapi.GeminiClient` directly. Stop recreating wheels. Delegate code and test work to subagents.
> **Principles**: SOLID design — Single Responsibility (each module does one thing), Open/Closed (add commands via thin wrappers, not core changes), Liskov Substitution (use upstream types directly), Interface Segregation (client_helpers exposes only what CLI needs), Dependency Inversion (CLI depends on abstractions in client_helpers, not concrete upstream client).

---

## Context: What Changed Since Original Analysis

The codebase has significantly evolved:

| Change | Impact |
|---|---|
| **Multi-profile auth** (`profile` command, profile CRUD in `auth_manager.py`) | Profile iteration boilerplate now duplicated across ALL commands |
| **`--all-profiles`** flag on `list` and `export-all` | Cross-profile chat merging logic duplicated |
| **Auto-profile-search** on `fetch`, `continue`, `export` | "Try each profile until found" pattern repeated 3x |
| **`list` new options** (`--format json`, `--path`, `--all-profiles`) | More output modes to maintain |
| **`gemini-webapi>=2.0.0`** dependency | Upstream API may have changed; types available differ |
| **80+ tests** across 6 test files | Refactoring must not break existing tests |
| **`_get_browser_executable()` removed** | Auth simplified (no custom browser path resolution) |
| **`status` redesigned** | Now shows profile table instead of single auth check |

---

## Problem: Wheels Being Recreated Right Now

### P1: Profile Resolution Boilerplate (5 copies) — violates SRP & DRY

This exact pattern is copy-pasted in `list`, `fetch`, `continue`, `export`, `export-all`:

```python
statuses = list_profile_statuses()
active_profiles = [s for s in statuses if s["is_active"]]
if not active_profiles:
    console.print("[bold red]No active profiles found.[/bold red]")
    sys.exit(2)

for pname in active_profiles:
    try:
        secure_1psid, secure_1psidts = load_cookies(pname)
        client = GeminiClient(secure_1psid, secure_1psidts)
        # ... do something ...
    except ConversationNotFoundError:
        continue
    except (CookieExpiredError, AuthenticationError, GeminiAPIError) as e:
        last_error = e
        continue
```

**~40-60 lines duplicated per command x 5 commands = ~200-300 lines of pure duplication.**

### P2: Single-Profile Error Handling Boilerplate (3 copies) — violates SRP

Even the single-profile path repeats cookie loading + error mapping in multiple commands.

### P3: Dict Conversion Layer — violates ISP & LSP

`gemini_client.py` converts upstream `ChatInfo` -> `{id, title, is_pinned, timestamp}` and `ChatTurn` -> `{role, content, conversation_id}`. This loses type safety, forces every consumer to use string keys, and creates an unnecessary adapter layer.

### P4: Missing Upstream Capabilities — violates OCP

The upstream library provides deep research, gem management, model listing, image generation, streaming output, and file upload — none of which GemiTerm exposes. We should be open for extension (adding these as thin wrappers) without modifying core infrastructure.

### P5: Version Test Anti-Pattern

`tests/test_cli_install_status.py::test_version_flag` asserts a hardcoded version string. This creates a maintenance burden — every version bump requires updating the test. This test should be removed entirely.

---

## Architecture: Target State (SOLID-Compliant)

```
+-------------------------------------------------------------+
|                      gemiterm CLI                            |
|                  (Click + Rich formatting)                   |
|                  SRP: Each command = one concern              |
+---------+----------+-----------+-----------+----------------+
|  auth   |  status  |  profile  | export    | export-all      |
| (ours)  | (ours)   |  (ours)   | (ours)    | (ours)          |
+---------+----------+-----------+-----------+----------------+
| list*   | fetch*   | continue* | ask       | research        |
|(+filter)|(+format) | (+REPL)  | (thin)    | (thin)          |
+---------+----------+-----------+-----------+----------------+
|                                | models    | gems            |
|                                | (thin)    | (thin)          |
+--------------------------------+-----------+----------------+
|              client_helpers.py (NEW)                          |
|  ISP: Exposes only the interfaces CLI commands need           |
|  DIP: CLI depends on these abstractions, not upstream client  |
|  +----------------------+  +-----------------------------+   |
|  | get_default_client()  |  | resolve_conversation_owner() |   |
|  | get_all_profiles_     |  | handle_api_errors()          |   |
|  | chats()               |  | run_async()                  |   |
|  +----------------------+  +-----------------------------+   |
+--------------------------------------------------------------+
|              gemini_webapi.GeminiClient (upstream)            |
|         ChatMixin + GemMixin + ResearchMixin                  |
|         Cookie auto-refresh + TLS fingerprinting              |
+--------------------------------------------------------------+
```

---

## Implementation Plan: 4 Phases, 11 Tasks

Each task is designed to be **fully delegatable to a subagent** with clear inputs, outputs, and acceptance criteria.

---

### Phase 1: Extract Shared Client Helpers (Eliminates Duplication)

**Goal**: Create `src/gemiterm/client_helpers.py` that encapsulates all profile resolution, client creation, and error handling — one place, one responsibility (SRP). Update `cli.py` to use it.

#### Task 1.1: Create `client_helpers.py`

**Subagent instructions**: Create a new file `src/gemiterm/client_helpers.py` containing:

1. **`run_async(coro)`** — A sync-over-async bridge. Runs an async coroutine synchronously using `asyncio.run()` or a cached event loop. This replaces the event loop management currently in `GeminiClient._get_loop()`. Single responsibility: async-to-sync bridging.

2. **`create_client(secure_1psid, secure_1psidts) -> gemini_webapi.GeminiClient`** — Initializes and returns an initialized upstream `GeminiClient`. Wraps `init()` via `run_async()`. Catches upstream exceptions and maps to our custom exceptions. Single responsibility: client construction.

3. **`get_default_client() -> gemini_webapi.GeminiClient`** — Loads cookies from the default profile via `load_cookies()` and returns an initialized client via `create_client()`. Handles `CookieExpiredError` and `AuthenticationError` by printing Rich messages and calling `sys.exit(2)`. Single responsibility: default-profile client resolution.

4. **`get_client_for_profile(profile_name: str) -> gemini_webapi.GeminiClient`** — Same as above but for a named profile. Single responsibility: named-profile client resolution.

5. **`get_active_profiles() -> list[dict]`** — Returns `list_profile_statuses()` filtered to active profiles. Exits with code 2 and Rich message if none found. Single responsibility: active profile enumeration.

6. **`resolve_conversation_owner(conversation_id: str) -> tuple[gemini_webapi.GeminiClient, str]`** — Iterates all active profiles, tries `read_chat(conversation_id)` on each, returns `(client, profile_name)` on first success. Raises `ConversationNotFoundError` if not found in any profile. Single responsibility: conversation-to-profile mapping.

7. **`get_all_profiles_chats() -> list[ChatInfo]`** — Fetches chats from all active profiles, deduplicates by ID, adds `profile` attribute to each. Returns merged list. Single responsibility: cross-profile chat aggregation.

8. **`handle_api_error(e: Exception) -> NoReturn`** — Maps exception types to exit codes and Rich error messages:
   - `CookieExpiredError` -> exit 2 + "Session expired" + "Run gemiterm auth"
   - `AuthenticationError` -> exit 2 + "Not authenticated" + "Run gemiterm auth"
   - `ConversationNotFoundError` -> exit 1 + "Not found" + "Run gemiterm list"
   - `GeminiAPIError` -> exit 1 + "API error"
   Single responsibility: error-to-exit-code mapping.

**Acceptance criteria**:
- All functions are type-hinted
- All functions use Rich `Console` for error output
- No functions print on success (only on error/exit)
- File is < 150 lines
- `ruff check` and `ruff format` pass

**Dependencies from our codebase**: `auth_manager.py` (load_cookies, list_profile_statuses), `config.py` (profile functions), `exceptions.py`, `gemini_webapi.GeminiClient`

---

#### Task 1.2: Simplify `gemini_client.py`

**Subagent instructions**: Refactor `src/gemiterm/gemini_client.py` — apply SRP by removing the data transformation concern and keeping only the session management concern:

1. **Remove** the dict conversion layer (`_parse_chat_history`, the dict construction in `list_chats` and `fetch_chat`). These violate LSP by converting upstream types to untyped dicts.
2. **`list_chats()`** should return `list[ChatInfo]` directly from upstream — no transformation.
3. **`fetch_chat(conversation_id)`** should return `ChatHistory` directly from upstream — no transformation.
4. **`continue_chat(conversation_id, message)`** should return `str` (response text) — keep this as-is since it has complex session management logic that is genuinely ours.
5. **Keep** the `_chat_sessions` caching dict for REPL session persistence — this is our unique value.
6. **Remove** `_get_loop()` — event loop management moves to `client_helpers.run_async()`.
7. **Simplify** `_ensure_client()` to just call `client_helpers.create_client()`.

The class's single responsibility becomes: **REPL session lifecycle management**. For everything else, CLI commands will use `client_helpers` functions that return the upstream client directly.

**Acceptance criteria**:
- File is < 70 lines
- No dict construction (`{}` with string keys) for API responses
- `continue_chat` still works (session caching preserved)
- `ruff check` and `ruff format` pass

---

#### Task 1.3: Refactor `cli.py` to use `client_helpers.py`

**Subagent instructions**: Update `src/gemiterm/cli.py` to eliminate all duplicated profile resolution and error handling. Replace with calls to `client_helpers` — apply DIP (depend on `client_helpers` abstractions, not direct upstream client construction):

1. **`list` command**: Replace 50+ lines of profile resolution with:
   ```python
   if all_profiles:
       chats = get_all_profiles_chats()
   else:
       client = get_default_client()
       chats = run_async(client.list_chats())
   ```
   Update filtering/sorting to work with `ChatInfo` attributes (`chat.cid`, `chat.title`, etc.) instead of dict keys.

2. **`fetch` command**: Replace profile iteration with:
   ```python
   client, profile_name = resolve_conversation_owner(conversation_id)
   history = run_async(client.read_chat(conversation_id))
   ```
   Update output formatting to use `ChatHistory`/`ChatTurn` attributes.

3. **`continue` command**: Replace profile iteration with `resolve_conversation_owner()`. Keep the REPL logic — that's our value-add. For the REPL, create a local `GeminiClient` wrapper (from the simplified `gemini_client.py`) to manage session caching.

4. **`export` command**: Same pattern as `fetch`.

5. **`export-all` command**:
   ```python
   if all_profiles:
       chats = get_all_profiles_chats()
   else:
       client = get_default_client()
       chats = run_async(client.list_chats())
   ```

6. Wrap each command's API calls in try/except using `handle_api_error()`.

7. Update `exporter.py` to accept `ChatHistory` (or `list[ChatTurn]`) instead of `list[dict]`.

**Acceptance criteria**:
- `cli.py` drops by ~200+ lines (from ~1030 to ~800)
- Zero duplicated profile-resolution code
- Zero duplicated error-handling code
- All existing CLI commands produce identical output
- `ruff check` and `ruff format` pass

**IMPORTANT**: This is the highest-risk task. The subagent must verify that ALL existing tests still pass after this change.

---

#### Task 1.4: Update `exporter.py` for upstream types

**Subagent instructions**: Update `src/gemiterm/exporter.py` — apply LSP by accepting upstream types directly instead of requiring dict conversion:

1. Change `format_chat_as_markdown` signature to accept `ChatHistory` (from `gemini_webapi`) instead of `list[dict]`.
2. Access `.turns` to iterate messages, use `.role` and `.text` attributes instead of dict keys.
3. Keep the same markdown output format — output compatibility is preserved.
4. Update any type hints accordingly.

**Acceptance criteria**:
- Same markdown output as before
- No dict access patterns (`message["role"]`) — use attribute access (`turn.role`)
- `ruff check` and `ruff format` pass

---

### Phase 2: Fix Existing Test Gaps

**Goal**: Fix broken/anti-pattern tests and update coverage for refactored architecture.

#### Task 2.1: Remove version assertion test

**Subagent instructions**: Remove `tests/test_cli_install_status.py::TestRootCliGroup::test_version_flag` entirely. This test asserts a hardcoded version string, creating a maintenance burden — every version bump requires updating the test. Version display is already validated by Click's `@click.version_option` decorator.

Also remove the entire `TestRootCliGroup` class if `test_version_flag` was its only meaningful test. Keep `test_help_flag` and `test_no_args_exits_with_2` if they exist and provide real value — but merge them into an existing test class rather than keeping a near-empty class.

**Acceptance criteria**: `pytest tests/test_cli_install_status.py` passes. No test asserts a hardcoded version string anywhere in the codebase.

---

#### Task 2.2: Update existing tests for refactored types

**Subagent instructions**: After Phase 1 is complete, update all test files to work with the refactored code. Apply ISP — tests should mock `client_helpers` interfaces, not internal implementations:

1. Tests that mock `GeminiClient.list_chats()` should return `ChatInfo` objects (or appropriate mocks with `.cid`, `.title`, `.is_pinned`, `.timestamp` attributes) instead of dicts.
2. Tests that mock `GeminiClient.fetch_chat()` should return `ChatHistory` objects (with `.turns` containing `ChatTurn` objects with `.role` and `.text` attributes) instead of dicts.
3. Update mock patches to target `client_helpers` where appropriate:
   - `gemiterm.client_helpers.get_default_client` instead of `gemiterm.cli.load_cookies` + `gemiterm.cli.GeminiClient`
   - `gemiterm.client_helpers.resolve_conversation_owner` for cross-profile commands
   - `gemiterm.client_helpers.run_async` for async bridge
4. Shared mock fixtures should be extracted to a `tests/conftest.py` to avoid duplication (DRY).

**Acceptance criteria**: `pytest` passes with 0 failures. All 80+ existing tests green.

---

#### Task 2.3: Fill missing test coverage

**Subagent instructions**: Add tests for these uncovered scenarios:

1. **`list` with `--after`/`--before` date filtering** — verify chats outside date range are excluded
2. **`list` with `--offset` pagination** — verify correct page of results
3. **`export-all` with `--all-profiles`** — verify cross-profile export and deduplication
4. **`fetch` finding conversation in non-default profile** — verify profile auto-search
5. **`continue` finding conversation in non-default profile** — verify profile auto-search
6. **`profile` command**: `add`, `delete`, `rename`, `default` actions (currently only `list` is tested)
7. **`auth` interactive menu**: choices A, D, S, R (currently only X is tested)
8. **Interactive REPL**: actual message exchange and `/exit` command
9. **`validate_cookies`** and **`refresh_cookies`** in `auth_manager.py`
10. **`client_helpers.py`** — unit tests for each function

Place new tests in the existing test files where they logically fit, or create `tests/test_client_helpers.py` for the new module. Use shared fixtures from `conftest.py`.

**Acceptance criteria**: `pytest --tb=short` passes. At least 15 new test cases added.

---

### Phase 3: Add Upstream Capability Passthrough (New Commands)

**Goal**: Expose upstream capabilities as thin wrappers — apply OCP (extend with new commands without modifying core infrastructure).

#### Task 3.1: Add `ask` command

**Subagent instructions**: Add a new `ask` CLI command to `src/gemiterm/cli.py`:

```python
@cli.command()
@click.argument("prompt")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--image", type=click.Path(exists=True), help="Image file to include")
@click.option("--model", default=None, help="Model to use")
def ask(prompt: str, no_stream: bool, image: str | None, model: str | None) -> None:
```

**Behavior**:
- Uses `get_default_client()` from `client_helpers` — DIP
- For streaming: iterate `client.generate_content_stream(prompt, files=[image] if image else [])`, print each `text_delta` using Rich
- For non-streaming: call `client.generate_content(prompt, files=[image] if image else [])`, print `response.text`
- Print chat ID if available in metadata
- Handle errors via `handle_api_error()`

**Delegation**: This is 100% upstream `GeminiClient.generate_content` / `generate_content_stream`. We only add Rich formatting on top.

**Acceptance criteria**:
- `gemiterm ask "What is Python?"` produces streaming output
- `gemiterm ask --no-stream "Hello"` produces single-shot output
- `gemiterm ask --image photo.jpg "Describe this"` works
- `ruff check` passes

---

#### Task 3.2: Add `research` command group

**Subagent instructions**: Add a `research` Click group with three subcommands:

```python
@cli.group()
def research() -> None:
    """Deep research workflow"""

@research.command("send")
@click.argument("prompt")
def research_send(prompt: str) -> None:
    """Submit a research topic"""

@research.command("check")
@click.argument("chat_id")
def research_check(chat_id: str) -> None:
    """Check research progress"""

@research.command("get")
@click.argument("chat_id")
@click.option("--output", "-o", type=click.Path(), help="Save result to file")
def research_get(chat_id: str, output: Path | None) -> None:
    """Retrieve completed research"""
```

**Delegation**: All logic comes from `gemini_webapi.GeminiClient`:
- `client.create_deep_research_plan(prompt)` for send
- `client.check_deep_research_status(chat_id)` for check
- `client.get_deep_research_result(chat_id)` for get

All use `get_default_client()` + `run_async()` + `handle_api_error()` — DIP.

**Acceptance criteria**:
- `gemiterm research send "AI in 2026"` returns a research plan/chat ID
- `gemiterm research check <id>` shows progress
- `gemiterm research get <id>` retrieves results
- `ruff check` passes

---

#### Task 3.3: Add `models` command

**Subagent instructions**: Add a `models` command:

```python
@cli.command()
def models() -> None:
    """List available Gemini models"""
```

**Behavior**: Calls `client.list_models()` via `get_default_client()` + `run_async()`, displays in a Rich table with model name and description. Uses `handle_api_error()` for errors.

**Acceptance criteria**: `gemiterm models` displays a formatted table of available models.

---

#### Task 3.4: Add tests for new commands

**Subagent instructions**: Create `tests/test_new_commands.py` with tests for:

1. `ask` command: streaming output, non-streaming output, with image, auth errors, API errors
2. `research send`: successful submission, API error
3. `research check`: in-progress, completed, not-found
4. `research get`: successful retrieval, file output, not-found
5. `models`: successful listing, empty list, API error

All tests should mock `client_helpers` functions (`get_default_client`, `run_async`) — not the upstream client directly. This follows DIP: tests depend on the same abstractions as the CLI.

Use shared fixtures from `conftest.py`.

**Acceptance criteria**: `pytest tests/test_new_commands.py` passes with at least 15 test cases.

---

### Phase 4: Polish & Documentation

#### Task 4.1: Update AGENTS.md

**Subagent instructions**: Update `AGENTS.md` to reflect:
- New module `client_helpers.py` and its role (SRP: client lifecycle and error mapping)
- New commands: `ask`, `research`, `models`
- Updated project structure
- Updated testing approach (mock `client_helpers` interfaces, not internal implementations)

#### Task 4.2: Update README help text examples

**Subagent instructions**: Update any README or docs examples to include the new commands.

#### Task 4.3: Final validation

**Subagent instructions**: Run the full validation suite:
```bash
ruff check src/
ruff format src/ --check
pytest -v
```
Fix any issues found.

---

## Execution Order & Dependencies

```
Phase 1 (Foundation):
  1.1 client_helpers.py --+
  1.2 simplify gemini_client.py --+-- can run in parallel
  1.3 refactor cli.py ------------- <- depends on 1.1 + 1.2
  1.4 update exporter.py ---------- <- depends on 1.3

Phase 2 (Tests):
  2.1 remove version test --------- <- independent, run first
  2.2 update tests for refactored types <- depends on Phase 1
  2.3 fill coverage gaps ---------- <- depends on Phase 1

Phase 3 (New Features):
  3.1 ask command ----------------- <- depends on Phase 1
  3.2 research commands ----------- <- depends on Phase 1
  3.3 models command -------------- <- depends on Phase 1
  3.4 tests for new commands ----- <- depends on 3.1-3.3

Phase 4 (Polish):
  4.1-4.3 ------------------------- <- depends on all above
```

**Recommended order for subagent delegation**:
1. Task 2.1 (remove stale test — quick, unblocks everything)
2. Task 1.1 + Task 1.2 in parallel (independent foundations)
3. Task 1.3 + Task 1.4 together (core refactoring)
4. Task 2.2 (update existing tests)
5. Tasks 3.1 + 3.2 + 3.3 in parallel (new commands)
6. Task 3.4 (tests for new commands)
7. Task 2.3 (coverage gaps)
8. Tasks 4.1-4.3 (polish)

---

## What We OWN vs What We DELEGATE to Upstream

| Keep (Our Value-Add — SRP) | Delegate to Upstream |
|---|---|
| Playwright browser auth (`auth`) | `generate_content` / `generate_content_stream` |
| Multi-profile management (`profile`) | `list_chats` / `read_chat` / `start_chat` |
| Interactive REPL (`continue`) | `send_message` on `ChatSession` |
| Markdown/JSON export (`export`, `export-all`) | `create_deep_research_plan` / deep research |
| Rich terminal formatting (all commands) | `list_models` |
| Chat filtering/sorting/pagination (`list`) | `fetch_gems` / `create_gem` / Gem CRUD |
| Cookie freshness validation | `upload_file` (multimodal) |
| Standalone binary distribution | Image generation capabilities |
| Profile-aware client resolution (`client_helpers`) | Cookie auto-refresh (`auto_refresh=True`) |
| Error mapping to exit codes (`handle_api_error`) | Extension integration |

**Principle**: If the upstream library does it, we call it — not reimplement it. We own the UX layer only.
