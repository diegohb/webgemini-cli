# Phase 05: Finalization & Cleanup

Complete the migration with documentation updates, testing, and cleanup. Remove obsolete Python files and ensure the project is ready for production use.

## Tasks

- [ ] Update README.md:
  - Update prerequisites: Bun instead of Python, LightPanda browser
  - Update installation instructions for Bun
  - Document new architecture (TypeScript + Python subprocess)
  - Update usage examples with new CLI commands
  - Document Python wrapper protocol for future reference
  - Add troubleshooting section for common issues

- [ ] Update project configuration files:
  - Update `.gitignore` for Bun artifacts (bun.lockb, dist/, node_modules/)
  - Keep Python gitignore patterns for python/ directory
  - Create/update `.python-version` in python/ subdirectory
  - Add `pyproject.toml` in python/ subdirectory for Python wrapper

- [ ] Create tests:
  - Create `tests/` directory with Bun test files
  - Test Python wrapper JSON protocol
  - Test TypeScript GeminiClient wrapper
  - Test auth module (mock browser operations)
  - Test CLI commands (integration tests)
  - Run tests with `bun test`

- [ ] Verify build process:
  - Run `bun run build` to create standalone executable
  - Test compiled binary works independently
  - Verify binary size is reasonable
  - Document build output location

- [ ] Clean up obsolete files:
  - Remove old `src/webgemini_cli/` Python directory (moved to python/)
  - Remove old `pyproject.toml` from root (create new one in python/)
  - Remove old `requirements.txt` from root
  - Remove `.pytest_cache/` from root
  - Remove `.ruff_cache/` from root
  - Keep Python tests in `python/tests/`

- [ ] Create final project structure:
  ```
  webgemini-cli/
  ├── src/                    # TypeScript source
  │   ├── cli.ts
  │   ├── index.ts
  │   ├── auth.ts
  │   ├── browser.ts
  │   ├── cdp-client.ts
  │   ├── config.ts
  │   ├── cookie-store.ts
  │   ├── errors.ts
  │   ├── exporter.ts
  │   ├── gemini-client.ts
  │   ├── python-wrapper.ts
  │   └── types/
  │       ├── gemini.ts
  │       └── wrapper.ts
  ├── python/                 # Python wrapper
  │   ├── wrapper.py
  │   ├── webgemini_cli/
  │   │   ├── __init__.py
  │   │   ├── gemini_client.py
  │   │   └── exceptions.py
  │   ├── pyproject.toml
  │   └── requirements.txt
  ├── tests/                  # TypeScript tests
  ├── dist/                   # Build output
  ├── package.json
  ├── tsconfig.json
  └── README.md
  ```

- [ ] Verify all commands work:
  - `bun run src/cli.ts auth`
  - `bun run src/cli.ts list`
  - `bun run src/cli.ts fetch <id>`
  - `bun run src/cli.ts continue <id> <message>`
  - `bun run src/cli.ts export <id>`
  - `bun run src/cli.ts export-all`
  - `bun run src/cli.ts status`

- [ ] Performance verification:
  - Compare startup time vs Python version
  - Verify Python subprocess overhead is acceptable
  - Check memory usage is reasonable
  - Test with multiple rapid commands

- [ ] Final documentation:
  - Ensure all code has JSDoc comments
  - Document environment variables
  - Document configuration options
  - Add examples for common use cases
