# Plan 2: Python Re-Implementation for Browser Auth

## Context

The `webgemini auth` command hangs on Windows when using Bun + Playwright due to subprocess/IPC handling incompatibilities. The `notebooklm-py` project has solved this same problem using Python with proper Windows event loop policy handling.

## Goal

Replace the Node.js browser automation layer with Python, leveraging the proven approach from `teng-lin/notebooklm-py`.

## Reference Implementation

Key insights from `teng-lin/notebooklm-py`:

1. **Windows Event Loop Policy**: Context manager switches between `Selector` and `Proactor` event loop policies
2. **Synchronous API**: Uses `playwright.sync_api.sync_playwright` with `launch_persistent_context`
3. **Chromium Install**: `_ensure_chromium_installed()` pre-flight check
4. **Edge Support**: Can use `channel="msedge"` for Microsoft Edge

## Tasks

### Phase 1: Python Environment Setup

- [ ] Create `python/` subdirectory in project root
- [ ] Create `python/requirements.txt`:
  ```
  playwright>=1.40.0
  python-dotenv>=1.0.0
  ```
- [ ] Create `python/auth.py` - CLI entry point
- [ ] Create `python/browser_auth.py` - core browser auth logic

### Phase 2: Core Browser Auth Module

- [ ] Port cookie polling logic from `browser-auth.cjs` to Python
- [ ] Implement `_windows_playwright_event_loop()` context manager:
  ```python
  @contextmanager
  def _windows_playwright_event_loop():
      # Save current policy
      original_policy = asyncio.get_event_loop_policy()
      
      # Switch to Proactor for Playwright (Windows)
      asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
      
      try:
          yield
      finally:
          # Restore original policy
          asyncio.set_event_loop_policy(original_policy)
  ```
- [ ] Use `sync_playwright` API instead of async
- [ ] Use `launch_persistent_context` with `user_data_dir` for profile persistence

### Phase 3: CLI Interface

- [ ] `python/auth.py` accepts same CLI args: `<input.json> <output.json>`
- [ ] Same input/output contract as current `browser-auth.cjs`
- [ ] Handle `PYTHONUTF8=1` env var for Unicode on non-English Windows

### Phase 4: Integration

- [ ] Option A: Replace `browser-auth.cjs` with Python subprocess call
- [ ] Option B: Keep thin `browser-auth.cjs` wrapper that spawns Python
- [ ] Update `runChromiumAuth()` in `browser.ts` to call Python worker

### Phase 5: Testing

- [ ] Verify browser launches on Windows with `python/auth.py`
- [ ] Verify cookie capture works end-to-end
- [ ] Run `webgemini auth` with Python backend
- [ ] Verify existing tests still pass

## Architecture

```
src/browser.ts (runChromiumAuth)
    └── spawns: node python/auth.py <input.json> <output.json>
              └── python/auth.py
                  └── sync_playwright context
                      └── chromium.launch_persistent_context()
                          └── poll for __Secure-1PSID, __Secure-1PSIDTS
```

## Advantages

1. **Proven on Windows**: `notebooklm-py` already solves these issues
2. **Sync API**: More reliable than async for subprocess spawning
3. **Event Loop Control**: Proper Windows asyncio policy handling
4. **Shared Codebase**: Could potentially share auth logic with notebooklm-py

## Risks

1. **Python Dependency**: Adds Python requirement to project
2. **Build Complexity**: Need to ensure Python + Playwright are installed
3. **Maintenance**: Two language codebases for browser auth

## Verification

1. `python -c "from playwright.sync_api import sync_playwright; print('OK')"` works
2. `python python/auth.py <test-input.json> <test-output.json>` launches browser
3. `webgemini auth --browser chromium` completes successfully on Windows