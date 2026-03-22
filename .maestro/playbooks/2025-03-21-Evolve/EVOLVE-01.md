# Phase 01: Bun/TypeScript Foundation

Initialize the Bun-native TypeScript project structure. This phase establishes the new runtime foundation while preserving the existing Python code for later integration as a subprocess wrapper.

## Tasks

- [x] Initialize Bun project in project root:
  - Run `bun init` to create package.json, tsconfig.json, index.ts
  - Update package.json with project metadata (name: webgemini-cli, version: 0.2.0)
  - Set `"type": "module"` in package.json
  - Add `@types/bun` to devDependencies

- [x] Configure TypeScript for Bun:
  - Update tsconfig.json with Bun-optimized settings:
    - `"module": "esnext"`, `"target": "esnext"`
    - `"moduleResolution": "bundler"`
    - `"types": ["bun-types"]`
    - `"allowImportingTsExtensions": true`

- [x] Install core dependencies:
  - `bun add @lightpanda/browser` - LightPanda browser engine
  - `bun add playwright` - For controlling LightPanda via CDP
  - Consider CLI framework: `commander` or `cley` or native Bun args parsing

- [x] Create TypeScript source structure:
  - Create `src/` directory for TypeScript source
  - Create `src/cli.ts` as main entry point
  - Create `src/index.ts` for library exports
  - Create `src/types/` directory for TypeScript interfaces

- [x] Define TypeScript interfaces in `src/types/`:
  - `GeminiCookie` interface matching Python cookie format
  - `GeminiChat` interface with id, title fields
  - `GeminiMessage` interface with role, content, conversation_id
  - `PythonWrapperRequest` interface for stdin communication
  - `PythonWrapperResponse` interface for stdout responses

- [x] Configure package.json scripts:
  - `"dev": "bun run --watch src/cli.ts"`
  - `"start": "bun run src/cli.ts"`
  - `"build": "bun build ./src/cli.ts --outdir ./dist --compile"`
  - `"test": "bun test"`

- [x] Create CLI skeleton in `src/cli.ts`:
  - Set up command parsing (use chosen CLI framework)
  - Define placeholder commands: auth, list, fetch, continue, export, export-all, status
  - Each command should print "not implemented" for now
  - Add global `-v, --verbose` flag support

- [x] Create configuration module `src/config.ts`:
  - Define `CONFIG_DIR` default: `~/.config/webgemini-cli/`
  - Define `STORAGE_STATE_FILE` default: `storage_state.json`
  - Create `getStorageStatePath()` function returning full path
  - Create `ensureConfigDir()` function to create directory if missing
  - Support `WEBGEMINI_CONFIG_DIR` environment variable override
  - Use `Bun.env` for environment variable access

- [x] Verify Bun CLI works:
  - Run `bun run src/cli.ts --help`
  - Confirm all placeholder commands are visible
  - Test verbose flag: `bun run src/cli.ts -v --help`

- [x] Preserve existing Python code:
  - Create `python/` directory
  - Move `src/webgemini_cli/` Python package to `python/webgemini_cli/`
  - Update Python imports if needed
  - Ensure Python code still works: `python -m python.webgemini_cli.cli --help`
  - Run `bun init` to create package.json, tsconfig.json, index.ts
  - Update package.json with project metadata (name: webgemini-cli, version: 0.2.0)
  - Set `"type": "module"` in package.json
  - Add `@types/bun` to devDependencies

- [x] Configure TypeScript for Bun:
  - Update tsconfig.json with Bun-optimized settings:
    - `"module": "esnext"`, `"target": "esnext"`
    - `"moduleResolution": "bundler"`
    - `"types": ["bun-types"]`
    - `"allowImportingTsExtensions": true`

- [x] Install core dependencies:
  - `bun add @lightpanda/browser` - LightPanda browser engine
  - `bun add playwright` - For controlling LightPanda via CDP
  - Consider CLI framework: `commander` or `cley` or native Bun args parsing

- [x] Create TypeScript source structure:
  - Create `src/` directory for TypeScript source
  - Create `src/cli.ts` as main entry point
  - Create `src/index.ts` for library exports
  - Create `src/types/` directory for TypeScript interfaces

- [x] Define TypeScript interfaces in `src/types/`:
  - `GeminiCookie` interface matching Python cookie format
  - `GeminiChat` interface with id, title fields
  - `GeminiMessage` interface with role, content, conversation_id
  - `PythonWrapperRequest` interface for stdin communication
  - `PythonWrapperResponse` interface for stdout responses

- [x] Configure package.json scripts:
  - `"dev": "bun run --watch src/cli.ts"`
  - `"start": "bun run src/cli.ts"`
  - `"build": "bun build ./src/cli.ts --outdir ./dist --compile"`
  - `"test": "bun test"`

- [x] Create CLI skeleton in `src/cli.ts`:
  - Set up command parsing (use chosen CLI framework)
  - Define placeholder commands: auth, list, fetch, continue, export, export-all, status
  - Each command should print "not implemented" for now
  - Add global `-v, --verbose` flag support

- [x] Create configuration module `src/config.ts`:
  - Define `CONFIG_DIR` default: `~/.config/webgemini-cli/`
  - Define `STORAGE_STATE_FILE` default: `storage_state.json`
  - Create `getStorageStatePath()` function returning full path
  - Create `ensureConfigDir()` function to create directory if missing
  - Support `WEBGEMINI_CONFIG_DIR` environment variable override
  - Use `Bun.env` for environment variable access

- [x] Verify Bun CLI works:
  - Run `bun run src/cli.ts --help`
  - Confirm all placeholder commands are visible
  - Test verbose flag: `bun run src/cli.ts -v --help`

- [x] Preserve existing Python code:
  - Create `python/` directory
  - Move `src/webgemini_cli/` Python package to `python/webgemini_cli/`
  - Update Python imports if needed
  - Ensure Python code still works: `python -m python.webgemini_cli.cli --help`
