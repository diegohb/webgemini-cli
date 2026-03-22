import { startBrowser, stopBrowser, type BrowserProcess } from "./browser.js";
import { connectToLightPanda, closeCDPConnection, type CDPConnection } from "./cdp-client.js";
import { saveCookies, loadCookies as loadCookiesFromStore } from "./cookie-store.js";
import { AuthenticationError, CookieExpiredError } from "./errors.js";
import type { GeminiCookie } from "./types/index.js";

const GEMINI_URL = "https://gemini.google.com";
const REQUIRED_COOKIES = ["__Secure-1PSID", "__Secure-1PSIDTS"];
const POLL_INTERVAL_MS = 1000;
const COOKIE_FRESHNESS_DAYS = 7;

export async function login(): Promise<GeminiCookie[]> {
  let browserProc: BrowserProcess | null = null;
  let cdpConn: CDPConnection | null = null;

  try {
    browserProc = await startBrowser();
    cdpConn = await connectToLightPanda("http://127.0.0.1:9222");

    await cdpConn.page.goto(GEMINI_URL);
    await cdpConn.page.waitForTimeout(2000);

    const cookies = await pollForCookies(cdpConn);
    await saveCookies(cookies);
    return cookies;
  } finally {
    if (cdpConn) {
      await closeCDPConnection(cdpConn);
    }
    if (browserProc) {
      stopBrowser(browserProc);
    }
  }
}

async function pollForCookies(cdpConn: CDPConnection): Promise<GeminiCookie[]> {
  const startTime = Date.now();
  const timeout = 10 * 60 * 1000;

  while (Date.now() - startTime < timeout) {
    const cookies = await cdpConn.context.cookies([GEMINI_URL]);
    const geminiCookies = cookies.filter((c) =>
      REQUIRED_COOKIES.includes(c.name)
    ) as GeminiCookie[];

    if (geminiCookies.length === REQUIRED_COOKIES.length) {
      return geminiCookies;
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  throw new AuthenticationError(
    "Login timeout: Could not obtain required cookies within 10 minutes."
  );
}

export async function loadCookies(): Promise<GeminiCookie[]> {
  const cookies = await loadCookiesFromStore();
  validateCookies(cookies);
  return cookies;
}

export function validateCookies(cookies: GeminiCookie[]): void {
  const cookieNames = cookies.map((c) => c.name);
  const missingCookies = REQUIRED_COOKIES.filter(
    (name) => !cookieNames.includes(name)
  );

  if (missingCookies.length > 0) {
    throw new AuthenticationError(
      `Missing required cookies: ${missingCookies.join(", ")}`
    );
  }
}

export function checkCookieFreshness(cookies: GeminiCookie[]): boolean {
  const tsCookie = cookies.find((c) => c.name === "__Secure-1PSIDTS");
  if (!tsCookie) {
    return false;
  }

  const expiryDate = new Date(tsCookie.expires * 1000);
  const now = new Date();
  const daysUntilExpiry = Math.floor(
    (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );

  return daysUntilExpiry > COOKIE_FRESHNESS_DAYS;
}