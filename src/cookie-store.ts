import { appendFileSync, readFileSync, existsSync } from "fs";
import { getStorageStatePath, ensureConfigDir } from "./config.js";
import { AuthenticationError, CookieExpiredError } from "./errors.js";
import type { GeminiCookie } from "./types/gemini.js";

export async function saveCookies(cookies: GeminiCookie[]): Promise<void> {
  ensureConfigDir();
  const storageState = {
    cookies,
  };
  const path = getStorageStatePath();
  await Bun.write(path, JSON.stringify(storageState, null, 2));
}

export async function loadCookies(): Promise<GeminiCookie[]> {
  const path = getStorageStatePath();

  if (!existsSync(path)) {
    throw new AuthenticationError(`Cookie file not found at ${path}. Please run 'webgemini auth' first.`);
  }

  try {
    const content = readFileSync(path, "utf-8");
    const data = JSON.parse(content);

    if (!data.cookies || !Array.isArray(data.cookies)) {
      throw new CookieExpiredError("Cookie file format is invalid.");
    }

    return data.cookies as GeminiCookie[];
  } catch (e) {
    if (e instanceof CookieExpiredError) {
      throw e;
    }
    throw new AuthenticationError(`Failed to read cookie file: ${(e as Error).message}`);
  }
}