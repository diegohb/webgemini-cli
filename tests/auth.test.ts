import { describe, test, expect, mock, beforeEach, afterEach } from "bun:test";
import { existsSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { Readable } from "node:stream";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import type { Browser as PlaywrightBrowser, BrowserContext, Page } from "playwright";
import { validateCookies, checkCookieFreshness, login, loadCookies } from "../src/auth";
import type { GeminiCookie } from "../src/types";
import type { BrowserProcess } from "../src/browser";
import type { CDPConnection } from "../src/cdp-client";
import { saveCookies } from "../src/cookie-store";

const TEST_DIR = join(tmpdir(), "webgemini_auth_test");

const createMockCookie = (name: string, expires: number): GeminiCookie => ({
  name,
  value: "test_value",
  expires,
  domain: ".google.com",
  path: "/",
  secure: true,
});

function setupTestDir(): void {
  if (!existsSync(TEST_DIR)) {
    mkdirSync(TEST_DIR, { recursive: true });
  }
}

function cleanupTestDir(): void {
  if (existsSync(TEST_DIR)) {
    rmSync(TEST_DIR, { recursive: true, force: true });
  }
}

const ORIGINAL_CONFIG_DIR = Bun.env.WEBGEMINI_CONFIG_DIR;

beforeEach(() => {
  cleanupTestDir();
  setupTestDir();
  Bun.env.WEBGEMINI_CONFIG_DIR = TEST_DIR;
});

afterEach(() => {
  cleanupTestDir();
  if (ORIGINAL_CONFIG_DIR === undefined) {
    delete Bun.env.WEBGEMINI_CONFIG_DIR;
  } else {
    Bun.env.WEBGEMINI_CONFIG_DIR = ORIGINAL_CONFIG_DIR;
  }
});

function createMockPlaywrightBrowser(mockProc = { pid: 12345 }) {
  return {
    process: () => mockProc,
    close: () => Promise.resolve(),
  } as unknown as PlaywrightBrowser;
}

function createMockCDPConnection(mockPage: Partial<Page> = {}, mockContext: Partial<BrowserContext> = {}) {
  return {
    browser: {} as PlaywrightBrowser,
    context: {
      cookies: async () => [],
      ...mockContext,
    } as unknown as BrowserContext,
    page: {
      goto: async () => {},
      waitForTimeout: async () => {},
      close: async () => {},
      ...mockPage,
    } as unknown as Page,
  };
}

function createMockLightPandaProcess() {
  return {
    stdout: { destroy: () => {} } as unknown as Readable,
    stderr: { destroy: () => {} } as unknown as Readable,
    kill: () => {},
  };
}

function createMockCookies(nameValuePairs: Array<{ name: string; value: string }>) {
  return nameValuePairs.map(({ name, value }) => ({
    name,
    value,
    expires: Math.floor(Date.now() / 1000) + 86400,
    domain: ".google.com",
    path: "/",
    secure: true,
    httpOnly: false,
    sameSite: "Lax" as const,
  }));
}

describe("validateCookies", () => {
  test("passes when all required cookies are present", () => {
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", Date.now() / 1000 + 86400),
      createMockCookie("__Secure-1PSIDTS", Date.now() / 1000 + 86400),
    ];

    expect(() => validateCookies(cookies)).not.toThrow();
  });

  test("throws when __Secure-1PSID is missing", () => {
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSIDTS", Date.now() / 1000 + 86400),
    ];

    expect(() => validateCookies(cookies)).toThrow("Missing required cookies: __Secure-1PSID");
  });

  test("throws when __Secure-1PSIDTS is missing", () => {
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", Date.now() / 1000 + 86400),
    ];

    expect(() => validateCookies(cookies)).toThrow("Missing required cookies: __Secure-1PSIDTS");
  });

  test("throws when both required cookies are missing", () => {
    const cookies: GeminiCookie[] = [];

    expect(() => validateCookies(cookies)).toThrow("Missing required cookies: __Secure-1PSID, __Secure-1PSIDTS");
  });
});

describe("checkCookieFreshness", () => {
  test("returns true when cookie expires in more than 7 days", () => {
    const futureExpiry = Math.floor(Date.now() / 1000) + 10 * 86400;
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", futureExpiry),
      createMockCookie("__Secure-1PSIDTS", futureExpiry),
    ];

    expect(checkCookieFreshness(cookies)).toBe(true);
  });

  test("returns false when cookie expires in less than 7 days", () => {
    const nearExpiry = Math.floor(Date.now() / 1000) + 5 * 86400;
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", nearExpiry),
      createMockCookie("__Secure-1PSIDTS", nearExpiry),
    ];

    expect(checkCookieFreshness(cookies)).toBe(false);
  });

  test("returns false when __Secure-1PSIDTS is missing", () => {
    const futureExpiry = Math.floor(Date.now() / 1000) + 10 * 86400;
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", futureExpiry),
    ];

    expect(checkCookieFreshness(cookies)).toBe(false);
  });

  test("returns false when cookie is already expired", () => {
    const pastExpiry = Math.floor(Date.now() / 1000) - 86400;
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", pastExpiry),
      createMockCookie("__Secure-1PSIDTS", pastExpiry),
    ];

    expect(checkCookieFreshness(cookies)).toBe(false);
  });
});

describe("login() integration tests", () => {
  describe("login() with mocked CDP connection", () => {
    test("login() connects to correct CDP URL for Chromium", async () => {
      const { login: loginFn } = await import("../src/auth");
      let cdpUrl: string | undefined;

      mock.module("playwright", () => ({
        chromium: {
          launch: async () => ({
            process: () => ({ pid: 12345 }),
            close: async () => {},
          }),
        },
      }));

      mock.module("../src/cdp-client", () => ({
        connectToLightPanda: async (url: string) => {
          cdpUrl = url;
          return {
            browser: {},
            context: {
              cookies: async () => [
                { name: "__Secure-1PSID", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
                { name: "__Secure-1PSIDTS", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
              ],
            },
            page: { goto: async () => {}, waitForTimeout: async () => {}, close: async () => {} },
          };
        },
        closeCDPConnection: async () => {},
      }));

      const cookies = await loginFn("chromium");
      expect(cdpUrl).toContain("127.0.0.1");
      expect(cookies).toHaveLength(2);
    });

    test("login() connects to correct CDP URL for remote browser", async () => {
      const { login: loginFn } = await import("../src/auth");
      let cdpUrl: string | undefined;

      mock.module("../src/cdp-client", () => ({
        connectToLightPanda: async (url: string) => {
          cdpUrl = url;
          return {
            browser: {},
            context: {
              cookies: async () => [
                { name: "__Secure-1PSID", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
                { name: "__Secure-1PSIDTS", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
              ],
            },
            page: { goto: async () => {}, waitForTimeout: async () => {}, close: async () => {} },
          };
        },
        closeCDPConnection: async () => {},
      }));

      const cookies = await loginFn("remote", "ws://192.168.1.100:9333");
      expect(cdpUrl).toBe("ws://192.168.1.100:9333");
      expect(cookies).toHaveLength(2);
    });

    test("login() replaces 0.0.0.0 with localhost in remote URL", async () => {
      const { login: loginFn } = await import("../src/auth");
      let cdpUrl: string | undefined;

      mock.module("../src/cdp-client", () => ({
        connectToLightPanda: async (url: string) => {
          cdpUrl = url;
          return {
            browser: {},
            context: {
              cookies: async () => [
                { name: "__Secure-1PSID", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
                { name: "__Secure-1PSIDTS", value: "test", expires: Date.now() / 1000 + 86400, domain: ".google.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
              ],
            },
            page: { goto: async () => {}, waitForTimeout: async () => {}, close: async () => {} },
          };
        },
        closeCDPConnection: async () => {},
      }));

      await loginFn("remote", "ws://0.0.0.0:9222");
      expect(cdpUrl).toBe("ws://localhost:9222");
    });
  });

  describe("cookie saving and loading integration", () => {
    test("saveCookies() and loadCookies() work together", async () => {
      const cookies: GeminiCookie[] = [
        createMockCookie("__Secure-1PSID", Math.floor(Date.now() / 1000) + 86400),
        createMockCookie("__Secure-1PSIDTS", Math.floor(Date.now() / 1000) + 86400),
      ];

      await saveCookies(cookies);

      const loaded = await loadCookies();
      expect(loaded).toHaveLength(2);
      expect(loaded[0]?.name).toBe("__Secure-1PSID");
      expect(loaded[1]?.name).toBe("__Secure-1PSIDTS");
    });

    test("loadCookies() rejects when missing __Secure-1PSID", async () => {
      const cookies: GeminiCookie[] = [
        createMockCookie("__Secure-1PSIDTS", Math.floor(Date.now() / 1000) + 86400),
      ];

      await saveCookies(cookies);

      await expect(loadCookies()).rejects.toThrow("Missing required cookies");
    });

    test("loadCookies() rejects when missing __Secure-1PSIDTS", async () => {
      const cookies: GeminiCookie[] = [
        createMockCookie("__Secure-1PSID", Math.floor(Date.now() / 1000) + 86400),
      ];

      await saveCookies(cookies);

      await expect(loadCookies()).rejects.toThrow("Missing required cookies");
    });

    test("loadCookies() rejects when both cookies are missing", async () => {
      const cookies: GeminiCookie[] = [];

      await saveCookies(cookies);

      await expect(loadCookies()).rejects.toThrow("Missing required cookies");
    });
  });
});