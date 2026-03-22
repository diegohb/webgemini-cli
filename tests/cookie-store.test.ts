import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, unlinkSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const TEST_DIR = join(tmpdir(), "webgemini_test_config");
const TEST_PATH = join(TEST_DIR, "storage_state.json");

process.env.WEBGEMINI_CONFIG_DIR = TEST_DIR;

import type { GeminiCookie } from "../src/types";
import { saveCookies, loadCookies } from "../src/cookie-store";
import { AuthenticationError, CookieExpiredError } from "../src/errors";

const createMockCookie = (name: string, expires: number): GeminiCookie => ({
  name,
  value: "test_value",
  expires,
  domain: ".google.com",
  path: "/",
  secure: true,
});

describe("saveCookies", () => {
  beforeEach(() => {
    if (existsSync(TEST_PATH)) {
      unlinkSync(TEST_PATH);
    }
  });

  afterEach(() => {
    if (existsSync(TEST_PATH)) {
      unlinkSync(TEST_PATH);
    }
  });

  test("saves cookies to storage_state.json", async () => {
    const cookies: GeminiCookie[] = [
      createMockCookie("__Secure-1PSID", Math.floor(Date.now() / 1000) + 86400),
      createMockCookie("__Secure-1PSIDTS", Math.floor(Date.now() / 1000) + 86400),
    ];

    await saveCookies(cookies);

    expect(existsSync(TEST_PATH)).toBe(true);

    const content = await Bun.file(TEST_PATH).text();
    const parsed = JSON.parse(content);
    expect(parsed.cookies).toHaveLength(2);
    expect(parsed.cookies[0].name).toBe("__Secure-1PSID");
    expect(parsed.cookies[1].name).toBe("__Secure-1PSIDTS");
  });
});

describe("loadCookies", () => {
  beforeEach(() => {
    if (existsSync(TEST_PATH)) {
      unlinkSync(TEST_PATH);
    }
  });

  afterEach(() => {
    if (existsSync(TEST_PATH)) {
      unlinkSync(TEST_PATH);
    }
  });

  test("loads cookies from storage_state.json", async () => {
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

  test("throws AuthenticationError when file does not exist", async () => {
    let error: Error | null = null;
    try {
      await loadCookies();
    } catch (e) {
      error = e as Error;
    }

    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error?.message).toContain("Cookie file not found");
  });

  test("throws CookieExpiredError when cookies array is missing", async () => {
    await Bun.write(TEST_PATH, JSON.stringify({ invalid: "format" }));

    let error: Error | null = null;
    try {
      await loadCookies();
    } catch (e) {
      error = e as Error;
    }

    expect(error).toBeInstanceOf(CookieExpiredError);
  });

  test("throws CookieExpiredError when cookies is not an array", async () => {
    await Bun.write(TEST_PATH, JSON.stringify({ cookies: "not an array" }));

    let error: Error | null = null;
    try {
      await loadCookies();
    } catch (e) {
      error = e as Error;
    }

    expect(error).toBeInstanceOf(CookieExpiredError);
  });
});