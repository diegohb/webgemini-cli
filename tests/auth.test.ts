import { describe, test, expect, mock, beforeEach } from "bun:test";
import { validateCookies, checkCookieFreshness } from "../src/auth";
import type { GeminiCookie } from "../src/types";

const createMockCookie = (name: string, expires: number): GeminiCookie => ({
  name,
  value: "test_value",
  expires,
  domain: ".google.com",
  path: "/",
  secure: true,
});

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