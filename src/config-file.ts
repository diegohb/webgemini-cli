import { homedir } from "os";
import { join, dirname } from "path";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";

export const CONFIG_FILE_NAME = "config.json";
export const CONFIG_FILE_NAME_ALT = ".webgeminirc";

export interface BrowserConfig {
  type?: "chromium" | "lightpanda" | "remote";
  chromiumPath?: string;
  remoteHost?: string;
}

export interface Config {
  browser?: BrowserConfig;
  [key: string]: unknown;
}

export interface ResolvedConfig {
  browserType: "chromium" | "lightpanda" | "remote";
  chromiumPath?: string;
  remoteHost?: string;
  sources: {
    browserType: "cli" | "env" | "config" | "default";
    chromiumPath: "env" | "config" | "default";
    remoteHost: "env" | "config" | "default";
  };
}

export function getConfigDir(): string {
  return Bun.env.WEBGEMINI_CONFIG_DIR ?? join(homedir(), ".config", "webgemini-cli");
}

export function getConfigPath(): string {
  return join(getConfigDir(), CONFIG_FILE_NAME);
}

export function getConfigPathAlt(): string {
  return join(getConfigDir(), CONFIG_FILE_NAME_ALT);
}

export function ensureConfigDir(): void {
  const configDir = getConfigDir();
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true });
  }
}

function parseConfig(content: string): Config {
  try {
    return JSON.parse(content) as Config;
  } catch {
    return {};
  }
}

export function loadConfig(): Config {
  const configPath = getConfigPath();
  const configPathAlt = getConfigPathAlt();

  if (existsSync(configPath)) {
    try {
      const content = readFileSync(configPath, "utf-8");
      return parseConfig(content);
    } catch {
      return {};
    }
  }

  if (existsSync(configPathAlt)) {
    try {
      const content = readFileSync(configPathAlt, "utf-8");
      return parseConfig(content);
    } catch {
      return {};
    }
  }

  return {};
}

export function saveConfig(config: Config): void {
  ensureConfigDir();
  const configPath = getConfigPath();
  writeFileSync(configPath, JSON.stringify(config, null, 2), "utf-8");
}

export function mergeConfigWithEnv(cliBrowser?: string): ResolvedConfig {
  const fileConfig = loadConfig();
  const envBrowserType = Bun.env.BROWSER_TYPE;
  const envChromiumPath = Bun.env.CHROMIUM_PATH;
  const envRemoteHost = Bun.env.LIGHTPANDA_HOST ?? Bun.env.REMOTE_HOST;

  let browserType: "chromium" | "lightpanda" | "remote" = "chromium";
  let browserTypeSource: "cli" | "env" | "config" | "default" = "default";
  let chromiumPath: string | undefined;
  let chromiumPathSource: "env" | "config" | "default" = "default";
  let remoteHost: string | undefined;
  let remoteHostSource: "env" | "config" | "default" = "default";

  if (cliBrowser === "chromium" || cliBrowser === "lightpanda" || cliBrowser === "remote") {
    browserType = cliBrowser;
    browserTypeSource = "cli";
  } else if (envBrowserType === "lightpanda" || envBrowserType === "remote") {
    browserType = envBrowserType;
    browserTypeSource = "env";
  } else if (fileConfig.browser?.type === "lightpanda" || fileConfig.browser?.type === "remote") {
    browserType = fileConfig.browser.type;
    browserTypeSource = "config";
  }

  if (envChromiumPath) {
    chromiumPath = envChromiumPath;
    chromiumPathSource = "env";
  } else if (fileConfig.browser?.chromiumPath) {
    chromiumPath = fileConfig.browser.chromiumPath;
    chromiumPathSource = "config";
  }

  if (envRemoteHost) {
    remoteHost = envRemoteHost;
    remoteHostSource = "env";
  } else if (fileConfig.browser?.remoteHost) {
    remoteHost = fileConfig.browser.remoteHost;
    remoteHostSource = "config";
  }

  return {
    browserType,
    chromiumPath,
    remoteHost,
    sources: {
      browserType: browserTypeSource,
      chromiumPath: chromiumPathSource,
      remoteHost: remoteHostSource,
    },
  };
}

export function getConfigValue(path: string): unknown {
  const config = loadConfig();
  const parts = path.split(".");

  let current: unknown = config;
  for (const part of parts) {
    if (current === null || current === undefined || typeof current !== "object") {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }

  return current;
}

export function setConfigValue(path: string, value: unknown): void {
  const config = loadConfig();
  const parts = path.split(".");

  let current: Record<string, unknown> = config;
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i]!;
    if (!(part in current) || typeof current[part] !== "object" || current[part] === null) {
      current[part] = {};
    }
    current = current[part] as Record<string, unknown>;
  }

  const lastPart = parts[parts.length - 1]!;
  current[lastPart] = value;

  saveConfig(config);
}
