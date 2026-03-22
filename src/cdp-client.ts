import { chromium, type Browser, type BrowserContext, type Page } from "playwright";

export interface CDPConnection {
  browser: Browser;
  context: BrowserContext;
  page: Page;
}

export async function connectToLightPanda(cdpUrl: string): Promise<CDPConnection> {
  const browser = await chromium.connectOverCDP(cdpUrl);
  const context = await browser.newContext();
  const page = await context.newPage();

  return {
    browser,
    context,
    page,
  };
}

export async function closeCDPConnection(conn: CDPConnection): Promise<void> {
  await conn.page.close();
  await conn.context.close();
  await conn.browser.close();
}