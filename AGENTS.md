# GemiTerm Development Guidelines

## Problem Summary

The GemiTerm Windows standalone executable (`GemiTerm.exe`) failed with `ModuleNotFoundError: No module named 'rich'` when downloaded via `install.ps1` on machines without Python installed. The pipx installation worked fine, but the standalone exe did not.

## Root Causes & Solutions

### 1. PyInstaller Not Bundling Dependencies

**Problem**: Early CI builds ran `pip install build && python -m build` which creates a wheel but does NOT install the actual project dependencies (`rich`, `click`, `playwright`, `gemini-webapi`) into site-packages. PyInstaller couldn't find them and created a stub exe (~10MB) that required system Python.

**Fix**: Added explicit `pip install rich click playwright gemini-webapi pyinstaller` before PyInstaller in the build job. The resulting exe was ~60MB and self-contained.

**File**: `.github/workflows/release.yml`

### 2. Playwright API Change

**Problem**: Playwright v1.58.0 removed the programmatic `p.chromium.install()` API. Browser installation must be done via CLI: `playwright install chromium`.

**Fix**: Changed from `p.chromium.install()` to subprocess call using `py -3 -m playwright install chromium`.

**File**: `src/gemiterm/cli.py` - `install_browser` command

### 3. py Launcher Detection on Frozen Exe

**Problem**: When running as a PyInstaller frozen exe, `sys.executable` points to the exe itself, not Python. The `py` launcher was found by `shutil.which("py")` but on machines without Python, it shows "Python was not found" and returns exit code 0 (which looks like success).

**Fix**: Added proper Python version detection:
```python
result = subprocess.run([py_cmd, "-3", "--version"], capture_output=True, text=True)
if result.returncode == 0 and "Python" in result.stdout and "not found" not in result.stdout.lower():
    # py launcher actually works
```

**File**: `src/gemiterm/cli.py` - `install_browser` command

### 4. Chromium Download URL Hardcoding

**Problem**: Chromium revision was hardcoded as `chromium-1312` in the fallback download, but that revision doesn't exist on Google's storage servers.

**Fix**: 
1. Check for existing Edge or Chrome browsers first (most Windows machines have one)
2. Try multiple CDN URLs for Chromium download:
   - `playwright.azureedge.net/builds/chromium/`
   - `playwright.downloads.microsoft.com/download/chromium/`
   - Fallback to Google storage

**File**: `src/gemiterm/cli.py` - `_download_chromium_fallback()` and `_check_existing_browser()`

### 5. GitHub Actions Workflow Issues

**Problem 1**: `actions/checkout@v4` with `fetch-tags: true` conflicts with shallow clone (`fetch-depth: 1`) when checking out a tag, causing: `fatal: Cannot fetch both <sha> and refs/tags/v1.x.x to refs/tags/v1.x.x`

**Fix**: Removed `fetch-tags: true` from checkout step in release job.

**Problem 2**: PyPI rejects re-uploading the same file content. Version bumps required for each release attempt.

**Fix**: Always bump version when making significant changes that require re-testing.

### 6. Frozen Exe Environment Detection

**Problem**: In frozen exe, `sys.executable` is the exe path, not Python. `sys.base_prefix` points to a virtual environment if one exists, not the bundled Python.

**Fix**: Use `getattr(sys, "frozen", False)` to detect frozen state, and use `shutil.which("py")` to find the py launcher.

## Testing Checklist

Before tagging a release, ALWAYS test locally:

```powershell
# Build the exe locally
pip install -e ".[dev]"
pip install pyinstaller
pyinstaller --onefile --name GemiTerm --add-data "src/gemiterm;gemiterm" --paths "$(python -c 'import site; print(site.getsitepackages()[0])')" src/gemiterm/__main__.py

# Test the built exe
.\dist\GemiTerm.exe --version
.\dist\GemiTerm.exe install-browser
.\dist\GemiTerm.exe --help
```

## Version Bumping Policy

- Always bump version in `pyproject.toml` AND `src/gemiterm/__init__.py`
- Use semantic versioning (MAJOR.MINOR.PATCH)
- PyPI rejects re-uploading same file content, so version must increase

## Release Process

1. Make code changes
2. Test locally (build exe, test `install-browser`)
3. Bump version (both files)
4. Commit: `git add -A && git commit -m "description"`
5. Tag: `git tag vX.X.X && git push origin main && git push origin vX.X.X`
6. Wait for workflow to complete
7. Verify release on GitHub

## Key Files

- `.github/workflows/release.yml` - Release workflow with build, publish, and release jobs
- `src/gemiterm/cli.py` - CLI commands including `install_browser`
- `src/gemiterm/__init__.py` - Version string
- `pyproject.toml` - Project metadata including version
- `install.ps1` - Windows installation script
