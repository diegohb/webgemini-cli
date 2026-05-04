# Multi-Profile Authentication Plan

## Overview
Enhance GemiTerm to support multiple authenticated Google accounts (profiles) with seamless switching.

## Functional Requirements

### 1. Auth Command Behavior
- **First use (no profiles)**: Works as current single-account flow
- **Subsequent uses (>1 profile)**: Shows interactive auth menu with options:
  - Add new profile
  - Delete existing profile
  - Set default profile
  - Exit/continue with current

### 2. Auth Menu Display
For each profile show:
- Profile name/identifier
- Authentication state (active/inactive)
- Expiration time in format: `5/6/2026 10:30a (Wednesday)` (local system time)
- Connection refresh status

### 3. Command Modifications
- Commands operating on default profile: add `--all-profiles` / `-a` flag for multi-profile operation
- Conversation-ID-based commands: automatically search all active profiles without extra flag (conversation IDs are globally unique across profiles)

### 4. Update README.md

## Implementation Plan

### Phase 1: Profile Storage Architecture

**File: `src/gemiterm/config.py`**
- Change `STORAGE_STATE_FILE` from single file to directory: `profiles/`
- Profile storage: `profiles/<profile_name>/storage_state.json`
- Default profile marker: `profiles/.default` containing profile name
- Add functions:
  - `get_profiles_dir()` -> `Path`
  - `get_profile_path(name)` -> `Path`
  - `get_default_profile_name()` -> `str`
  - `set_default_profile_name(name)` -> `None`
  - `list_profiles()` -> `list[str]`

**File: `src/gemiterm/auth_manager.py`**
- Modify `login()` to accept optional `profile_name` parameter
- Store to `profiles/<name>/storage_state.json`
- Add `load_cookies(profile_name=None)` - uses default if None
- Add `check_cookie_freshness(profile_name)` - checks expiration per profile
- Add `delete_profile(name)` function
- Add `rename_profile(old_name, new_name)` function
- `check_cookie_freshness()`: use `__Secure-1PSIDTS.expires` for expiration display

### Phase 2: Auth Menu Implementation

**File: `src/gemiterm/cli.py`**

New command structure:
```python
@cli.command()
def auth():
    # If 0 profiles exist -> run login(), create default profile "default"
    # If 1+ profiles exist -> show_auth_menu()
```

**`show_auth_menu()`**:
- Display table of profiles with columns: Name, Status, Expires, Default
- Menu options as numbered selection or key shortcuts:
  - `[A] Add new profile`
  - `[D] Delete profile`
  - `[S] Set default`
  - `[E] Exit (use current default)`
- Status values: "Active" (fresh cookies), "Expired" (needs re-auth), "Refresh needed"

**Expiration display format**: `datetime.fromtimestamp(expires).strftime("%-m/%-d/%Y %-I:%M%p (%A)")`

### Phase 3: Command Modifications

**Update `list`, `fetch`, `continue`, `export`, `export_all` commands**:

Add flag:
```python
@click.option("--all-profiles", is_flag=True, help="Operate across all active profiles")
```

For `list --all-profiles`: iterate all active profiles, fetch chats from each, merge and dedupe by conversation ID, display with profile name column.

For `fetch <conversation_id>`: automatically search all active profiles (no extra flag needed since conversation IDs should be globally unique).

For `export --all-profiles`: export all conversations from all active profiles.

**Conversation ID uniqueness assumption**: Gemini conversation IDs are unique across accounts. `fetch`, `continue`, `export` commands will try profiles in sequence until conversation found.

### Phase 4: Profile Management Commands

```python
@cli.command()
@click.argument("action", type=click.Choice(["add", "delete", "rename", "default", "list"]))
@click.argument("profile_name", required=False)
def profile(action: str, profile_name: str | None):
    """Manage authentication profiles."""
    pass
```

### Phase 5: Update README.md

Add section under Configuration:
```markdown
### Authentication Profiles

GemiTerm supports multiple Google accounts via profiles.

#### Listing Profiles
gemiterm profile list

#### Adding a Profile
gemiterm auth  # shows menu if multiple profiles exist

#### Setting Default Profile
gemiterm profile default <profile_name>

#### Deleting a Profile
gemiterm profile delete <profile_name>
```

Update command sections to note `--all-profiles` flag availability.

## Files to Modify

1. `src/gemiterm/config.py` - Profile storage paths
2. `src/gemiterm/auth_manager.py` - Multi-profile support
3. `src/gemiterm/cli.py` - Auth menu, profile commands, --all-profiles flags
4. `README.md` - Documentation updates

## Execution Workflow

1. Create and switch to feature branch
2. Delegate all code changes to implementation sub-agents
3. Commit after each major change
4. Run tests after each major change; update test logic if needed

## Testing Approach

1. Add tests for profile storage functions in `tests/test_profiles.py`
2. Add tests for auth menu interaction
3. Integration tests for multi-profile workflow
4. Run `pytest` and `ruff check src/` for validation

## Completion Criteria

- [ ] `gemiterm auth` on first use creates "default" profile
- [ ] `gemiterm auth` with existing profiles shows interactive menu
- [ ] Menu displays profiles with status, expiration in correct format
- [ ] Can add, delete, set default profile via menu
- [ ] `--all-profiles` flag works on `list` command
- [ ] `fetch <conversation_id>` searches all profiles automatically
- [ ] README.md reflects new functionality
- [ ] All tests pass
- [ ] Ruff linting clean