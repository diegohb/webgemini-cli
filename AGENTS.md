# GemiTerm Agent Guide

## Dev Setup
```bash
pip install -e ".[dev]"   # install with dev deps
playwright install chromium # install browser
```

## Key Commands
```bash
pytest                    # run all tests
pytest tests/test_x.py    # run specific test file
ruff check src/           # lint
ruff format src/          # format
python -m build           # build package
```

## Project Structure
- `src/gemiterm/` — main package
- `src/gemiterm/__main__.py` — CLI entry point (calls `cli()`)
- `src/gemiterm/cli.py` — all Click commands
- Auth stored at `~/.config/gemiterm/storage_state.json`

## Important Conventions
- **Python >=3.11** required
- **ruff** for linting/formatting (line-length: 100, target: py311)
- **Click** CLI framework, **Rich** for console output
- Entry point: `python -m gemiterm` or `gemiterm` command

## Gotchas
- `__main__.py` catches `NoArgsIsHelpError` to show `--help` on no-args. If you change `cli()` calls, preserve this behavior.

## Release Process
Triggered by pushing a `v*` tag. CI pipeline: test → build-linux → build-windows → publish → release. Build artifacts: `dist/GemiTerm` (Linux), `dist/GemiTerm.exe` (Windows).

## Docs Index
- `docs/DEVELOPMENT.md` — dev setup, project structure, contributing guide
- `docs/TROUBLESHOOTING.md` — browser automation issues, session expiry, API errors
- `docs/ROADMAP.md` — planned features
