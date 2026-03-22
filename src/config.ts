import { homedir } from "os";
import { join } from "path";
import { mkdirSync, existsSync } from "fs";
import {
  loadConfig,
  mergeConfigWithEnv,
  getConfigPath,
  getConfigDir,
  type ResolvedConfig,
} from "./config-file.js";

/** Default configuration directory path: ~/.config/webgemini-cli/ */
export const CONFIG_DIR_DEFAULT = join(homedir(), ".config", "webgemini-cli");
/** Storage state filename for cookies */
export const STORAGE_STATE_FILE = "storage_state.json";

/**
 * Gets the full path to the storage state file (cookies).
 * Respects WEBGEMINI_CONFIG_DIR environment variable if set.
 * @returns Absolute path to storage_state.json
 */
export function getStorageStatePath(): string {
  const configDir = Bun.env.WEBGEMINI_CONFIG_DIR ?? CONFIG_DIR_DEFAULT;
  return join(configDir, STORAGE_STATE_FILE);
}

/**
 * Ensures the configuration directory exists, creating it if necessary.
 * Respects WEBGEMINI_CONFIG_DIR environment variable if set.
 */
export function ensureConfigDir(): void {
  const configDir = Bun.env.WEBGEMINI_CONFIG_DIR ?? CONFIG_DIR_DEFAULT;
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true });
  }
}

/**
 * Gets the LIGHTPANDA_HOST environment variable value.
 * @returns The remote LightPanda WebSocket URL or undefined if not set.
 */
export function getLightPandaHost(): string | undefined {
  return Bun.env.LIGHTPANDA_HOST;
}

/**
 * Gets the LIGHTPANDA_DOCKER environment variable value.
 * @returns True if Docker auto-provisioning is enabled.
 */
export function getLightPandaDocker(): boolean {
  return Bun.env.LIGHTPANDA_DOCKER === "true";
}

export type BrowserType = "chromium" | "lightpanda" | "remote";

/**
 * Gets the BROWSER_TYPE environment variable value.
 * @returns The browser type (chromium, lightpanda, or remote). Defaults to chromium.
 */
export function getBrowserType(): BrowserType {
  const type = Bun.env.BROWSER_TYPE;
  if (type === "lightpanda" || type === "remote") {
    return type;
  }
  return "chromium";
}

/**
 * Gets the CHROMIUM_PATH environment variable value.
 * @returns The custom Chromium executable path or undefined if not set.
 */
export function getChromiumPath(): string | undefined {
  return Bun.env.CHROMIUM_PATH;
}

export function getRemoteHost(): string | undefined {
  return Bun.env.LIGHTPANDA_HOST ?? Bun.env.REMOTE_HOST;
}

export function getBrowserFallback(): boolean {
  const fallback = Bun.env.BROWSER_FALLBACK;
  if (fallback === "false") {
    return false;
  }
  return true;
}

export type { ResolvedConfig } from "./config-file.js";
