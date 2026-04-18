# GemiTerm Agent Guide

## Project Overview
Python CLI tool bridging Playwright-based Google auth with the gemini-webapi library. Entry point: `gemiterm` command.

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
- `src/gemiterm/` — main package (not `src/` directly)
- `src/gemiterm/__main__.py` — entry point
- `src/gemiterm/cli.py` — Click-based CLI commands
- `src/gemiterm/gemini_client.py` — Gemini API wrapper
- `src/gemiterm/auth_manager.py` — Playwright auth
- `src/gemiterm/exporter.py` — Markdown/JSON export
- `tests/` — pytest test suite

## Important Conventions
- **Python >=3.11** required
- **ruff** for linting/formatting (line-length: 100, target: py311)
- **Click** for CLI framework
- **Rich** for formatted console output
- Auth cookies stored at `~/.config/gemiterm/storage_state.json`

## How to Investigate

Read the highest-value sources first: root manifests, build/test/lint config, CI workflows. Only inspect code files if architecture is unclear after reading config and docs.

## Docs Index
- `docs/DEVELOPMENT.md` — dev setup, project structure, contributing guide
- `docs/TROUBLESHOOTING.md` — browser automation issues, session expiry, API errors
- `docs/ROADMAP.md` — planned features

## Release Process
Release is automated via tag push (`v*`). CI runs: test → build-linux → build-windows → publish → release.
