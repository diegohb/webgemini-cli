# Phase 06: Docker LightPanda Support

Add optional Docker-based LightPanda browser support, enabling headless browser authentication on Windows without requiring local LightPanda installation. The `auth` command gains a `--lightpanda-host` flag and `LIGHTPANDA_HOST` environment variable for remote browser connections.

## Tasks

- [x] Modify `src/browser.ts`:
  - Add `remote: boolean` field to `BrowserProcess` interface
  - Change `proc` field type to `ChildProcessWithoutNullStreams | null` (nullable for remote)
  - Add `connectToRemoteBrowser(host: string, port: number): Promise<BrowserProcess>` function that skips `lightpanda.serve()` and returns a `BrowserProcess` with `proc: null` and `remote: true`
  - Update `stopBrowser()` to handle `proc: null` case (no-op for remote connections)
  - Update `isLightPandaNotFoundError()` detection for remote connections (throw `BrowserConnectionError` instead when attempting remote)

- [x] Modify `src/auth.ts`:
  - Add optional `remoteHost?: string` parameter to `attemptLogin()`
  - When `remoteHost` is provided, parse `host:port` and call `connectToRemoteBrowser()` instead of `startBrowser()`
  - When `remoteHost` is not provided, use existing `startBrowser()` behavior
  - Pass `remoteHost` through from `login()` to `attemptLogin()`

- [x] Modify `src/cli.ts`:
  - Add `--lightpanda-host <ws://host:port>` option to the `auth` command
  - Read `LIGHTPANDA_HOST` environment variable as fallback
  - Detection priority: CLI flag > env var > default (spawn local)
  - Pass remote host string to `login()` function
  - Update error message in `handleAuthError()` for `BrowserConnectionError` to suggest Docker alternative

- [x] Modify `src/config.ts`:
  - Add `LIGHTPANDA_HOST` environment variable reading
  - Add `getLightPandaHost(): string | undefined` helper function

- [x] Add `src/docker.ts` module:
  - Implement `checkDockerInstalled(): Promise<boolean>` using `docker --version`
  - Implement `checkLightPandaContainer(): Promise<{exists: boolean, running: boolean}>` checking for container named `lightpanda`
  - Implement `startLightPandaContainer(): Promise<void>` running `docker start lightpanda`
  - Implement `pullAndStartLightPanda(): Promise<void>` running `docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly`
  - Implement `ensureLightPandaRunning(): Promise<string>` that checks, auto-starts, or pulls as needed, returning the connection URL

- [x] Update `src/auth.ts` to use docker module:
  - When remote host is not specified and `LIGHTPANDA_DOCKER=true`, auto-provision Docker container
  - Call `ensureLightPandaRunning()` and use returned URL
  - Add `LIGHTPANDA_DOCKER` env var support for transparent Docker provisioning

- [x] Add error class in `src/errors.ts`:
  - Add `DockerNotAvailableError` for Docker CLI not found
  - Add `DockerContainerError` for container management failures

- [x] Update `README.md`:
  - Add "Docker Installation" subsection under "Prerequisites"
  - Document `LIGHTPANDA_HOST` environment variable
  - Document `--lightpanda-host` CLI flag
  - Document `LIGHTPANDA_DOCKER` env var for auto-provisioning
  - Add troubleshooting entry: "Docker LightPanda not running" with remediation steps

## Implementation Details

### URL Format
Remote LightPanda URLs use `ws://` prefix: `ws://localhost:9222` or `ws://192.168.1.100:9222`

### Error Handling
- If `--lightpanda-host` is specified but connection fails, fail immediately with `BrowserConnectionError` (no fallback to local)
- If Docker auto-provision fails (Docker not installed, pull fails, etc.), fail with appropriate error
- Clear error messages guide user to install Docker or start container manually

### Manual Docker Commands (shown in error messages)
```bash
# Install and run LightPanda
docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly

# Start existing container
docker start lightpanda

# Stop container
docker stop lightpanda
```

### Environment Variables Summary
| Variable | Purpose | Example |
|----------|---------|---------|
| `LIGHTPANDA_HOST` | Remote LightPanda CDP URL | `ws://localhost:9222` |
| `LIGHTPANDA_DOCKER` | Auto-provision Docker container | `true` |

## Verification

After implementation, verify:
- `webgemini auth --lightpanda-host ws://localhost:9222` connects to running Docker LightPanda
- `LIGHTPANDA_HOST=ws://localhost:9222 webgemini auth` works via env var
- `LIGHTPANDA_DOCKER=true webgemini auth` auto-provisions Docker if missing
- Error messages are clear when Docker is not available or container fails to start
- Existing local `lightpanda auth` still works without modifications
