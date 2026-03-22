import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, mkdirSync, writeFileSync, rmSync, readFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const TEST_DIR = join(tmpdir(), "webgemini_config_test");
const TEST_CONFIG_DIR = join(TEST_DIR, "config");

function setupTestConfigDir(): void {
  if (!existsSync(TEST_CONFIG_DIR)) {
    mkdirSync(TEST_CONFIG_DIR, { recursive: true });
  }
}

function cleanupTestConfigDir(): void {
  if (existsSync(TEST_DIR)) {
    rmSync(TEST_DIR, { recursive: true, force: true });
  }
}

function getTestConfigPath(): string {
  return join(TEST_CONFIG_DIR, "config.json");
}

function getTestConfigPathAlt(): string {
  return join(TEST_CONFIG_DIR, ".webgeminirc");
}

describe("Config Module - Environment Variables", () => {
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    cleanupTestConfigDir();
    setupTestConfigDir();
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
  });

  afterEach(() => {
    cleanupTestConfigDir();
    if (ORIGINAL_CONFIG_DIR === undefined) {
      delete Bun.env.WEBGEMINI_CONFIG_DIR;
    } else {
      Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
    }
  });

  describe("getBrowserType()", () => {
    test("returns chromium by default when env var is not set", () => {
      delete Bun.env.BROWSER_TYPE;
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("chromium");
    });

    test("returns lightpanda when BROWSER_TYPE=lightpanda", () => {
      Bun.env.BROWSER_TYPE = "lightpanda";
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("lightpanda");
    });

    test("returns remote when BROWSER_TYPE=remote", () => {
      Bun.env.BROWSER_TYPE = "remote";
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("remote");
    });

    test("returns chromium for invalid browser type values", () => {
      Bun.env.BROWSER_TYPE = "firefox";
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("chromium");
    });

    test("returns chromium for empty string browser type", () => {
      Bun.env.BROWSER_TYPE = "";
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("chromium");
    });

    test("returns chromium when env var is undefined", () => {
      delete Bun.env.BROWSER_TYPE;
      const { getBrowserType } = require("../src/config");
      expect(getBrowserType()).toBe("chromium");
    });
  });

  describe("getChromiumPath()", () => {
    test("returns undefined when CHROMIUM_PATH is not set", () => {
      delete Bun.env.CHROMIUM_PATH;
      const { getChromiumPath } = require("../src/config");
      expect(getChromiumPath()).toBeUndefined();
    });

    test("returns custom path when CHROMIUM_PATH is set", () => {
      Bun.env.CHROMIUM_PATH = "/custom/chromium/path";
      const { getChromiumPath } = require("../src/config");
      expect(getChromiumPath()).toBe("/custom/chromium/path");
    });

    test("returns custom path with spaces", () => {
      Bun.env.CHROMIUM_PATH = "C:\\Program Files\\Chromium\\chrome.exe";
      const { getChromiumPath } = require("../src/config");
      expect(getChromiumPath()).toBe("C:\\Program Files\\Chromium\\chrome.exe");
    });

    test("returns empty string when CHROMIUM_PATH is empty", () => {
      Bun.env.CHROMIUM_PATH = "";
      const { getChromiumPath } = require("../src/config");
      expect(getChromiumPath()).toBe("");
    });
  });

  describe("getBrowserFallback()", () => {
    test("returns true by default when BROWSER_FALLBACK is not set", () => {
      delete Bun.env.BROWSER_FALLBACK;
      const { getBrowserFallback } = require("../src/config");
      expect(getBrowserFallback()).toBe(true);
    });

    test("returns false when BROWSER_FALLBACK=false", () => {
      Bun.env.BROWSER_FALLBACK = "false";
      const { getBrowserFallback } = require("../src/config");
      expect(getBrowserFallback()).toBe(false);
    });

    test("returns true when BROWSER_FALLBACK=true", () => {
      Bun.env.BROWSER_FALLBACK = "true";
      const { getBrowserFallback } = require("../src/config");
      expect(getBrowserFallback()).toBe(true);
    });

    test("returns true for any other non-false value", () => {
      Bun.env.BROWSER_FALLBACK = "1";
      const { getBrowserFallback } = require("../src/config");
      expect(getBrowserFallback()).toBe(true);
    });
  });

  describe("getLightPandaHost()", () => {
    test("returns undefined when LIGHTPANDA_HOST is not set", () => {
      delete Bun.env.LIGHTPANDA_HOST;
      const { getLightPandaHost } = require("../src/config");
      expect(getLightPandaHost()).toBeUndefined();
    });

    test("returns host URL when LIGHTPANDA_HOST is set", () => {
      Bun.env.LIGHTPANDA_HOST = "ws://localhost:9222";
      const { getLightPandaHost } = require("../src/config");
      expect(getLightPandaHost()).toBe("ws://localhost:9222");
    });
  });

  describe("getLightPandaDocker()", () => {
    test("returns false by default", () => {
      delete Bun.env.LIGHTPANDA_DOCKER;
      const { getLightPandaDocker } = require("../src/config");
      expect(getLightPandaDocker()).toBe(false);
    });

    test("returns true when LIGHTPANDA_DOCKER=true", () => {
      Bun.env.LIGHTPANDA_DOCKER = "true";
      const { getLightPandaDocker } = require("../src/config");
      expect(getLightPandaDocker()).toBe(true);
    });
  });
});

describe("Config Module - Config File Loading", () => {
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    cleanupTestConfigDir();
    setupTestConfigDir();
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
  });

  afterEach(() => {
    cleanupTestConfigDir();
    if (ORIGINAL_CONFIG_DIR === undefined) {
      delete Bun.env.WEBGEMINI_CONFIG_DIR;
    } else {
      Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
    }
  });

  describe("loadConfig()", () => {
    test("returns empty config when no config file exists", async () => {
      const { loadConfig } = await import("../src/config-file");
      const config = loadConfig();
      expect(config).toEqual({});
    });

    test("loads config from config.json", async () => {
      const { loadConfig, getConfigPath } = await import("../src/config-file");
      const configPath = getConfigPath();
      writeFileSync(configPath, JSON.stringify({ browser: { type: "lightpanda" as const } }));
      const config = loadConfig();
      expect(config.browser?.type).toBe("lightpanda");
    });

    test("loads config from .webgeminirc (alternative config file)", async () => {
      const { loadConfig, getConfigPathAlt } = await import("../src/config-file");
      const configPathAlt = getConfigPathAlt();
      writeFileSync(configPathAlt, JSON.stringify({ browser: { type: "remote" as const } }));
      const config = loadConfig();
      expect(config.browser?.type).toBe("remote");
    });

    test("prefers config.json over .webgeminirc when both exist", async () => {
      const { loadConfig, getConfigPath, getConfigPathAlt } = await import("../src/config-file");
      const configPath = getConfigPath();
      const configPathAlt = getConfigPathAlt();
      writeFileSync(configPath, JSON.stringify({ browser: { type: "chromium" } }));
      writeFileSync(configPathAlt, JSON.stringify({ browser: { type: "lightpanda" } }));
      const config = loadConfig();
      expect(config.browser?.type).toBe("chromium");
    });

    test("returns empty config for malformed JSON", async () => {
      const { loadConfig, getConfigPath } = await import("../src/config-file");
      const configPath = getConfigPath();
      writeFileSync(configPath, "{ invalid json }");
      const config = loadConfig();
      expect(config).toEqual({});
    });

    test("returns empty config for empty file", async () => {
      const { loadConfig, getConfigPath } = await import("../src/config-file");
      const configPath = getConfigPath();
      writeFileSync(configPath, "");
      const config = loadConfig();
      expect(config).toEqual({});
    });

    test("loads valid config with multiple fields", async () => {
      const { loadConfig, getConfigPath } = await import("../src/config-file");
      const configPath = getConfigPath();
      const configData = {
        browser: {
          type: "chromium",
          chromiumPath: "/path/to/chromium",
          remoteHost: "ws://localhost:9222"
        },
        customField: "value"
      };
      writeFileSync(configPath, JSON.stringify(configData));
      const config = loadConfig();
      expect(config.browser?.type).toBe("chromium");
      expect(config.browser?.chromiumPath).toBe("/path/to/chromium");
      expect(config.browser?.remoteHost).toBe("ws://localhost:9222");
      expect(config.customField).toBe("value");
    });
  });

  describe("saveConfig()", () => {
    test("saves config to file", async () => {
      const { saveConfig, loadConfig } = await import("../src/config-file");
      const configData = { browser: { type: "chromium" as const, chromiumPath: "/custom/path" } };
      saveConfig(configData);
      const config = loadConfig();
      expect(config.browser?.type).toBe("chromium");
      expect(config.browser?.chromiumPath).toBe("/custom/path");
    });

    test("overwrites existing config", async () => {
      const { saveConfig, loadConfig } = await import("../src/config-file");
      saveConfig({ browser: { type: "lightpanda" as const } });
      saveConfig({ browser: { type: "chromium" as const } });
      const config = loadConfig();
      expect(config.browser?.type).toBe("chromium");
    });

    test("creates config directory if it does not exist", async () => {
      cleanupTestConfigDir();
      const { saveConfig, loadConfig, getConfigDir } = await import("../src/config-file");
      const configData = { browser: { type: "chromium" as const } };
      saveConfig(configData);
      expect(existsSync(getConfigDir())).toBe(true);
      const config = loadConfig();
      expect(config.browser?.type).toBe("chromium");
    });
  });

  describe("mergeConfigWithEnv()", () => {
    test("returns chromium by default with default sources", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv();
      expect(result.browserType).toBe("chromium");
      expect(result.sources.browserType).toBe("default");
    });

    test("uses CLI override when provided", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv("lightpanda");
      expect(result.browserType).toBe("lightpanda");
      expect(result.sources.browserType).toBe("cli");
    });

    test("uses env var when CLI is not provided", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.BROWSER_TYPE = "remote";
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv();
      expect(result.browserType).toBe("remote");
      expect(result.sources.browserType).toBe("env");
    });

    test("uses config file when no CLI or env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { type: "lightpanda" as const } });
      const result = mergeConfigWithEnv();
      expect(result.browserType).toBe("lightpanda");
      expect(result.sources.browserType).toBe("config");
    });

    test("CLI takes precedence over env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.BROWSER_TYPE = "remote";
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv("chromium");
      expect(result.browserType).toBe("chromium");
      expect(result.sources.browserType).toBe("cli");
    });

    test("env var takes precedence over config file", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.BROWSER_TYPE = "lightpanda";
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { type: "remote" as const } });
      const result = mergeConfigWithEnv();
      expect(result.browserType).toBe("lightpanda");
      expect(result.sources.browserType).toBe("env");
    });

    test("chromiumPath from env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.CHROMIUM_PATH = "/env/chromium/path";
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv();
      expect(result.chromiumPath).toBe("/env/chromium/path");
      expect(result.sources.chromiumPath).toBe("env");
    });

    test("chromiumPath from config file when no env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { chromiumPath: "/config/chromium/path" } });
      const result = mergeConfigWithEnv();
      expect(result.chromiumPath).toBe("/config/chromium/path");
      expect(result.sources.chromiumPath).toBe("config");
    });

    test("env var takes precedence over config file for chromiumPath", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.CHROMIUM_PATH = "/env/chromium/path";
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { chromiumPath: "/config/chromium/path" } });
      const result = mergeConfigWithEnv();
      expect(result.chromiumPath).toBe("/env/chromium/path");
      expect(result.sources.chromiumPath).toBe("env");
    });

    test("remoteHost from LIGHTPANDA_HOST env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.LIGHTPANDA_HOST = "ws://localhost:9333";
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv();
      expect(result.remoteHost).toBe("ws://localhost:9333");
      expect(result.sources.remoteHost).toBe("env");
    });

    test("remoteHost from config file when no env var", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { remoteHost: "ws://config/host:9222" } });
      const result = mergeConfigWithEnv();
      expect(result.remoteHost).toBe("ws://config/host:9222");
      expect(result.sources.remoteHost).toBe("config");
    });

    test("LIGHTPANDA_HOST takes precedence over REMOTE_HOST", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.LIGHTPANDA_HOST = "ws://lightpanda:9222";
      Bun.env.REMOTE_HOST = "ws://remote:9222";
      const { mergeConfigWithEnv } = await import("../src/config-file");
      const result = mergeConfigWithEnv();
      expect(result.remoteHost).toBe("ws://lightpanda:9222");
    });

    test("full precedence chain: CLI > ENV > CONFIG > DEFAULT", async () => {
      delete Bun.env.BROWSER_TYPE;
      delete Bun.env.CHROMIUM_PATH;
      delete Bun.env.LIGHTPANDA_HOST;
      delete Bun.env.REMOTE_HOST;
      Bun.env.BROWSER_TYPE = "remote";
      Bun.env.CHROMIUM_PATH = "/env/path";
      const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
      saveConfig({ browser: { type: "lightpanda" as const, chromiumPath: "/config/path" } });
      const result = mergeConfigWithEnv("chromium");
      expect(result.browserType).toBe("chromium");
      expect(result.sources.browserType).toBe("cli");
      expect(result.chromiumPath).toBe("/env/path");
      expect(result.sources.chromiumPath).toBe("env");
    });
  });
});

describe("Config Module - Path Functions", () => {
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    cleanupTestConfigDir();
    setupTestConfigDir();
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
  });

  afterEach(() => {
    cleanupTestConfigDir();
    if (ORIGINAL_CONFIG_DIR === undefined) {
      delete Bun.env.WEBGEMINI_CONFIG_DIR;
    } else {
      Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
    }
  });

  test("getConfigDir returns custom config dir", async () => {
    const { getConfigDir } = await import("../src/config-file");
    expect(getConfigDir()).toBe(TEST_CONFIG_DIR);
  });

  test("getConfigPath returns path to config.json", async () => {
    const { getConfigPath } = await import("../src/config-file");
    expect(getConfigPath()).toBe(getTestConfigPath());
  });

  test("getConfigPathAlt returns path to .webgeminirc", async () => {
    const { getConfigPathAlt } = await import("../src/config-file");
    expect(getConfigPathAlt()).toBe(getTestConfigPathAlt());
  });

  test("ensureConfigDir creates directory if not exists", async () => {
    cleanupTestConfigDir();
    const { ensureConfigDir, getConfigDir } = await import("../src/config-file");
    ensureConfigDir();
    expect(existsSync(getConfigDir())).toBe(true);
  });
});

describe("Config Module - getConfigValue / setConfigValue", () => {
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    cleanupTestConfigDir();
    setupTestConfigDir();
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
  });

  afterEach(() => {
    cleanupTestConfigDir();
    if (ORIGINAL_CONFIG_DIR === undefined) {
      delete Bun.env.WEBGEMINI_CONFIG_DIR;
    } else {
      Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
    }
  });

  test("getConfigValue returns nested value", async () => {
    const { getConfigValue, saveConfig } = await import("../src/config-file");
    saveConfig({ browser: { type: "chromium" } });
    const value = getConfigValue("browser.type");
    expect(value).toBe("chromium");
  });

  test("getConfigValue returns undefined for missing path", async () => {
    const { getConfigValue } = await import("../src/config-file");
    const value = getConfigValue("nonexistent.path");
    expect(value).toBeUndefined();
  });

  test("getConfigValue returns undefined for non-object at path", async () => {
    const { getConfigValue, setConfigValue } = await import("../src/config-file");
    setConfigValue("browser", "not an object" as unknown);
    const value = getConfigValue("browser.type");
    expect(value).toBeUndefined();
  });

  test("setConfigValue sets nested value", async () => {
    const { setConfigValue, getConfigValue } = await import("../src/config-file");
    setConfigValue("browser.type", "lightpanda");
    const value = getConfigValue("browser.type");
    expect(value).toBe("lightpanda");
  });

  test("setConfigValue creates nested objects as needed", async () => {
    const { setConfigValue, getConfigValue } = await import("../src/config-file");
    setConfigValue("deep.nested.value", "test");
    const value = getConfigValue("deep.nested.value");
    expect(value).toBe("test");
  });

  test("setConfigValue overwrites existing value", async () => {
    const { setConfigValue, getConfigValue } = await import("../src/config-file");
    setConfigValue("browser.type", "chromium");
    setConfigValue("browser.type", "lightpanda");
    const value = getConfigValue("browser.type");
    expect(value).toBe("lightpanda");
  });
});

describe("Config Module - Integration", () => {
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    cleanupTestConfigDir();
    setupTestConfigDir();
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
  });

  afterEach(() => {
    cleanupTestConfigDir();
    if (ORIGINAL_CONFIG_DIR === undefined) {
      delete Bun.env.WEBGEMINI_CONFIG_DIR;
    } else {
      Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
    }
  });

  test("complete config workflow: init, modify, verify", async () => {
    const { saveConfig, loadConfig, mergeConfigWithEnv } = await import("../src/config-file");
    
    saveConfig({
      browser: {
        type: "chromium",
        chromiumPath: "/default/chromium"
      }
    });

    let config = loadConfig();
    expect(config.browser?.type).toBe("chromium");
    expect(config.browser?.chromiumPath).toBe("/default/chromium");

    Bun.env.CHROMIUM_PATH = "/custom/chromium";
    let result = mergeConfigWithEnv();
    expect(result.chromiumPath).toBe("/custom/chromium");
    expect(result.sources.chromiumPath).toBe("env");

    Bun.env.CHROMIUM_PATH = undefined;
    result = mergeConfigWithEnv("lightpanda");
    expect(result.browserType).toBe("lightpanda");
    expect(result.sources.browserType).toBe("cli");
  });

  test("config file with malformed JSON does not crash", async () => {
    const { getConfigPath, loadConfig } = await import("../src/config-file");
    const configPath = getConfigPath();
    writeFileSync(configPath, "{ broken");
    
    expect(() => loadConfig()).not.toThrow();
    const config = loadConfig();
    expect(config).toEqual({});
  });

  test("empty config file returns empty object", async () => {
    const { getConfigPath, loadConfig } = await import("../src/config-file");
    const configPath = getConfigPath();
    writeFileSync(configPath, "");

    const config = loadConfig();
    expect(config).toEqual({});
  });
});