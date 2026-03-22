import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, mkdirSync, writeFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const TEST_DIR = join(tmpdir(), "webgemini_cli_test");
const TEST_CONFIG_DIR = join(TEST_DIR, "config");
const TEST_STORAGE_PATH = join(TEST_CONFIG_DIR, "storage_state.json");

process.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;

const MOCK_COOKIES = [
  {
    name: "__Secure-1PSID",
    value: "testvalue1",
    expires: Math.floor(Date.now() / 1000) + 86400 * 10,
    domain: ".google.com",
    path: "/",
    secure: true,
  },
  {
    name: "__Secure-1PSIDTS",
    value: "testvalue2",
    expires: Math.floor(Date.now() / 1000) + 86400 * 10,
    domain: ".google.com",
    path: "/",
    secure: true,
  },
];

function setupTestStorage(): void {
  if (!existsSync(TEST_CONFIG_DIR)) {
    mkdirSync(TEST_CONFIG_DIR, { recursive: true });
  }
  writeFileSync(TEST_STORAGE_PATH, JSON.stringify({ cookies: MOCK_COOKIES }));
}

function cleanupTestStorage(): void {
  if (existsSync(TEST_DIR)) {
    rmSync(TEST_DIR, { recursive: true, force: true });
  }
}

describe("CLI Integration Tests", () => {
  const cliPath = join(process.cwd(), "src", "cli.ts");

  describe("Command-line Interface Parsing", () => {
    test("--version shows version 0.2.0", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "--version"],
        env: process.env,
      });

      const stdout = await new Response(proc.stdout).text();
      await proc.exited;

      expect(proc.exitCode).toBe(0);
      expect(stdout.trim()).toBe("0.2.0");
    });

    test("--help shows all commands", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "--help"],
        env: process.env,
      });

      const stdout = await new Response(proc.stdout).text();
      await proc.exited;

      expect(stdout).toContain("auth");
      expect(stdout).toContain("list");
      expect(stdout).toContain("fetch");
      expect(stdout).toContain("continue");
      expect(stdout).toContain("export");
      expect(stdout).toContain("export-all");
      expect(stdout).toContain("status");
    });

    test("unknown command returns exit code 1", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "nonexistent"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(1);
    });
  });

  describe("auth command", () => {
    test("auth --help displays auth command help", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "auth", "--help"],
        env: process.env,
      });

      const stdout = await new Response(proc.stdout).text();
      await proc.exited;

      expect(stdout).toContain("auth");
    });
  });

  describe("list command argument parsing", () => {
    test("missing storage exits with code 2", async () => {
      cleanupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "list"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(2);
    });

    test("-n option is parsed correctly", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "list", "-n", "5"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });

    test("--limit long form is parsed correctly", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "list", "--limit", "25"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });
  });

  describe("fetch command validation", () => {
    test("fetch without arguments shows error", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "fetch"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(1);
    });

    test("fetch with empty conversation-id shows error", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "fetch", ""],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
      expect(proc.exitCode).toBe(1);
    });
  });

  describe("continue command validation", () => {
    test("continue without arguments shows error", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "continue"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(1);
    });

    test("continue with empty message shows error", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "continue", "chat123", ""],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
      expect(proc.exitCode).toBe(1);
    });
  });

  describe("export command validation", () => {
    test("export without arguments shows error", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "export"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(1);
    });

    test("export -f json option is accepted", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "export", "chat123", "-f", "json"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });

    test("export --include-metadata flag is accepted", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "export", "chat123", "--include-metadata"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });
  });

  describe("export-all command options", () => {
    test("export-all -o option is accepted", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "export-all", "-o", TEST_DIR],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });

    test("export-all --since option is accepted", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "export-all", "--since", "2024-01-01"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });
  });

  describe("status command", () => {
    test("status with no storage exits with 2", async () => {
      cleanupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "status"],
        env: process.env,
      });

      const stdout = await new Response(proc.stdout).text();
      await proc.exited;

      expect(proc.exitCode).toBe(2);
      expect(stdout).toContain("Missing");
    });
  });

  describe("verbose flag", () => {
    test("-v flag is accepted by list command", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "-v", "list"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });

    test("--verbose flag is accepted", async () => {
      setupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "--verbose", "list"],
        env: process.env,
      });

      await proc.exited;
      cleanupTestStorage();
    });
  });

  describe("Exit codes", () => {
    test("version command exits with 0", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "--version"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(0);
    });

    test("missing command exits with 1", async () => {
      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "invalid"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(1);
    });

    test("missing auth exits with 2", async () => {
      cleanupTestStorage();

      const proc = Bun.spawn({
        cmd: ["bun", "run", cliPath, "list"],
        env: process.env,
      });

      await proc.exited;
      expect(proc.exitCode).toBe(2);
    });
  });
});

describe("Exporter Module", () => {
  test("formatChatAsMarkdown with metadata", async () => {
    const { formatChatAsMarkdown } = await import("../src/exporter");

    const messages = [
      { role: "user" as const, content: "Hello", conversation_id: "123" },
      { role: "model" as const, content: "Hi there!", conversation_id: "123" },
    ];

    const result = formatChatAsMarkdown(messages, "Test Chat", "123", {
      includeMetadata: true,
    });

    expect(result).toContain("# Test Chat");
    expect(result).toContain("**User:**");
    expect(result).toContain("**Gemini:**");
    expect(result).toContain("Hello");
    expect(result).toContain("Hi there!");
    expect(result).toContain("conversation_id: 123");
  });

  test("formatChatAsMarkdown without conversationId omits comment", async () => {
    const { formatChatAsMarkdown } = await import("../src/exporter");

    const messages = [
      { role: "user" as const, content: "Hello", conversation_id: "123" },
    ];

    const result = formatChatAsMarkdown(messages, "Test Chat", undefined, {
      includeMetadata: false,
    });

    expect(result).toContain("# Test Chat");
    expect(result).not.toContain("conversation_id:");
    expect(result).not.toContain("title:");
  });

  test("formatChatAsMarkdown handles code blocks", async () => {
    const { formatChatAsMarkdown } = await import("../src/exporter");

    const messages = [
      { role: "user" as const, content: "```js\nconsole.log('hello')\n```", conversation_id: "123" },
    ];

    const result = formatChatAsMarkdown(messages, "Code Chat", "123", {
      includeMetadata: false,
    });

    expect(result).toContain("```js");
    expect(result).toContain("console.log('hello')");
    expect(result).toContain("```");
  });
});

describe("Error Classes", () => {
  test("WebGeminiError base class works", async () => {
    const { WebGeminiError } = await import("../src/errors");
    const error = new WebGeminiError("test message");
    expect(error.name).toBe("WebGeminiError");
    expect(error.message).toBe("test message");
    expect(error).toBeInstanceOf(Error);
  });

  test("AuthenticationError extends WebGeminiError", async () => {
    const { AuthenticationError, WebGeminiError } = await import("../src/errors");
    const error = new AuthenticationError("auth failed");
    expect(error).toBeInstanceOf(WebGeminiError);
    expect(error.name).toBe("AuthenticationError");
  });

  test("CookieExpiredError extends AuthenticationError", async () => {
    const { CookieExpiredError, AuthenticationError } = await import("../src/errors");
    const error = new CookieExpiredError("expired");
    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.name).toBe("CookieExpiredError");
  });

  test("ConversationNotFoundError works", async () => {
    const { ConversationNotFoundError, WebGeminiError } = await import("../src/errors");
    const error = new ConversationNotFoundError("not found");
    expect(error).toBeInstanceOf(WebGeminiError);
    expect(error.name).toBe("ConversationNotFoundError");
  });

  test("GeminiAPIError works", async () => {
    const { GeminiAPIError, WebGeminiError } = await import("../src/errors");
    const error = new GeminiAPIError("api error");
    expect(error).toBeInstanceOf(WebGeminiError);
    expect(error.name).toBe("GeminiAPIError");
  });

  test("getErrorClass maps error types correctly", async () => {
    const { getErrorClass } = await import("../src/errors");
    
    const AuthClass = getErrorClass("AuthenticationError");
    expect(new AuthClass("test")).toBeInstanceOf(Error);

    const UnknownClass = getErrorClass("NonExistentError");
    expect(new UnknownClass("test")).toBeInstanceOf(Error);
  });
});

describe("Browser Flag", () => {
  const cliPath = join(process.cwd(), "src", "cli.ts");

  test("--help shows browser option", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "--help"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("--browser");
    expect(stdout).toContain("chromium|lightpanda|remote");
  });

  test("--browser flag is accepted by status command", async () => {
    cleanupTestStorage();

    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "-b", "chromium", "status"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(proc.exitCode).toBe(2);
    expect(stdout).toContain("Browser type");
  });

  test("--browser flag long form is accepted", async () => {
    cleanupTestStorage();

    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "--browser", "lightpanda", "status"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(proc.exitCode).toBe(2);
    expect(stdout).toContain("Browser type");
  });

  test("auth command --help shows remote-host option", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "auth", "--help"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("--remote-host");
    expect(stdout).toContain("deprecated");
  });
});

describe("Config Module", () => {
  test("getBrowserType returns chromium by default", async () => {
    const { getBrowserType } = await import("../src/config");
    const original = Bun.env.BROWSER_TYPE;
    delete Bun.env.BROWSER_TYPE;
    const result = getBrowserType();
    expect(result).toBe("chromium");
    Bun.env.BROWSER_TYPE = original;
  });

  test("getBrowserType respects BROWSER_TYPE env var", async () => {
    const { getBrowserType } = await import("../src/config");
    const original = Bun.env.BROWSER_TYPE;
    Bun.env.BROWSER_TYPE = "lightpanda";
    const result = getBrowserType();
    expect(result).toBe("lightpanda");
    Bun.env.BROWSER_TYPE = original;
  });

  test("getBrowserType returns chromium for invalid values", async () => {
    const { getBrowserType } = await import("../src/config");
    const original = Bun.env.BROWSER_TYPE;
    Bun.env.BROWSER_TYPE = "invalid";
    const result = getBrowserType();
    expect(result).toBe("chromium");
    Bun.env.BROWSER_TYPE = original;
  });
});

describe("Config File Module", () => {
  const TEST_CONFIG_DIR = join(tmpdir(), "webgemini_config_file_test");
  const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

  beforeEach(() => {
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
    rmSync(TEST_CONFIG_DIR, { recursive: true, force: true });
    mkdirSync(TEST_CONFIG_DIR, { recursive: true });
  });

  afterEach(() => {
    rmSync(TEST_CONFIG_DIR, { recursive: true, force: true });
    Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
  });

  test("loadConfig returns empty config when no file exists", async () => {
    const { loadConfig } = await import("../src/config-file");
    const config = loadConfig();
    expect(config).toEqual({});
  });

  test("loadConfig returns config from file", async () => {
    const { loadConfig, getConfigPath } = await import("../src/config-file");
    const configPath = getConfigPath();
    const configData = { browser: { type: "lightpanda" as const } };
    writeFileSync(configPath, JSON.stringify(configData));
    const config = loadConfig();
    expect(config.browser?.type).toBe("lightpanda");
  });

  test("saveConfig writes config to file", async () => {
    const { saveConfig, loadConfig } = await import("../src/config-file");
    const configData = { browser: { type: "chromium" as const, chromiumPath: "/custom/path" } };
    saveConfig(configData);
    const config = loadConfig();
    expect(config.browser?.type).toBe("chromium");
    expect(config.browser?.chromiumPath).toBe("/custom/path");
  });

  test("mergeConfigWithEnv uses CLI override", async () => {
    const { mergeConfigWithEnv } = await import("../src/config-file");
    const result = mergeConfigWithEnv("lightpanda");
    expect(result.browserType).toBe("lightpanda");
    expect(result.sources.browserType).toBe("cli");
  });

  test("mergeConfigWithEnv uses env var when no CLI", async () => {
    const { mergeConfigWithEnv } = await import("../src/config-file");
    const original = Bun.env.BROWSER_TYPE;
    Bun.env.BROWSER_TYPE = "remote";
    const result = mergeConfigWithEnv();
    expect(result.browserType).toBe("remote");
    expect(result.sources.browserType).toBe("env");
    Bun.env.BROWSER_TYPE = original;
  });

  test("mergeConfigWithEnv uses config file when no env or CLI", async () => {
    const { mergeConfigWithEnv, saveConfig } = await import("../src/config-file");
    saveConfig({ browser: { type: "lightpanda" as const } });
    const result = mergeConfigWithEnv();
    expect(result.browserType).toBe("lightpanda");
    expect(result.sources.browserType).toBe("config");
  });

  test("mergeConfigWithEnv defaults to chromium", async () => {
    const { mergeConfigWithEnv } = await import("../src/config-file");
    const result = mergeConfigWithEnv();
    expect(result.browserType).toBe("chromium");
    expect(result.sources.browserType).toBe("default");
  });

  test("getConfigValue returns nested value", async () => {
    const { getConfigValue, saveConfig } = await import("../src/config-file");
    saveConfig({ browser: { type: "chromium" as const } });
    const value = getConfigValue("browser.type");
    expect(value).toBe("chromium");
  });

  test("getConfigValue returns undefined for missing path", async () => {
    const { getConfigValue } = await import("../src/config-file");
    const value = getConfigValue("nonexistent.path");
    expect(value).toBeUndefined();
  });

  test("setConfigValue sets nested value", async () => {
    const { setConfigValue, getConfigValue } = await import("../src/config-file");
    setConfigValue("browser.type", "lightpanda");
    const value = getConfigValue("browser.type");
    expect(value).toBe("lightpanda");
  });

  test("getConfigPath returns correct path", async () => {
    const { getConfigPath } = await import("../src/config-file");
    const configPath = getConfigPath();
    expect(configPath).toBe(join(TEST_CONFIG_DIR, "config.json"));
  });
});

describe("Config CLI Commands", () => {
  const TEST_CONFIG_DIR = join(tmpdir(), "webgemini_config_cli_test");
  const cliPath = join(process.cwd(), "src", "cli.ts");

  beforeEach(() => {
    Bun.env.WEBGEMINI_CONFIG_DIR = TEST_CONFIG_DIR;
    rmSync(TEST_CONFIG_DIR, { recursive: true, force: true });
    mkdirSync(TEST_CONFIG_DIR, { recursive: true });
  });

  afterEach(() => {
    rmSync(TEST_CONFIG_DIR, { recursive: true, force: true });
    delete Bun.env.WEBGEMINI_CONFIG_DIR;
  });

  test("config --help shows config commands", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "--help"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("get");
    expect(stdout).toContain("set");
    expect(stdout).toContain("list");
    expect(stdout).toContain("init");
  });

  test("config list shows current configuration", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "list"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("Configuration");
    expect(stdout).toContain("browser.type");
    expect(stdout).toContain("browser.chromiumPath");
    expect(stdout).toContain("browser.remoteHost");
  });

  test("config get returns value from config file", async () => {
    const { saveConfig } = await import("../src/config-file");
    saveConfig({ browser: { type: "lightpanda" as const } });

    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "get", "browser.type"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout.trim()).toBe('"lightpanda"');
  });

  test("config set updates config file", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "set", "browser.type", "remote"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("✓");

    const { getConfigValue } = await import("../src/config-file");
    const value = getConfigValue("browser.type");
    expect(value).toBe("remote");
  });

  test("config init creates default config", async () => {
    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "init"],
      env: process.env,
    });

    const stdout = await new Response(proc.stdout).text();
    await proc.exited;

    expect(stdout).toContain("✓");
    expect(proc.exitCode).toBe(0);
  });

  test("config init fails if config already exists", async () => {
    const { saveConfig } = await import("../src/config-file");
    saveConfig({ browser: { type: "chromium" as const } });

    const proc = Bun.spawn({
      cmd: ["bun", "run", cliPath, "config", "init"],
      env: process.env,
    });

    await proc.exited;
    expect(proc.exitCode).toBe(1);
  });
});