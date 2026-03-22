import { startBrowser, stopBrowser, type BrowserProcess } from "./browser.js";
import { connectToLightPanda, closeCDPConnection, type CDPConnection } from "./cdp-client.js";
import type { BrowserType } from "./config.js";

export interface BrowserConnection {
  cdpConn: CDPConnection;
  browserProc: BrowserProcess;
  port: number;
}

export async function getBrowserConnection(
  browserType: BrowserType,
  remoteHost?: string,
  cookies?: Record<string, string>
): Promise<BrowserConnection> {
  let browserProc: BrowserProcess | null = null;
  let cdpConn: CDPConnection | null = null;

  if (browserType === "remote" && remoteHost) {
    const url = new URL(remoteHost);
    const host = url.hostname;
    const port = parseInt(url.port, 10) || 9222;
    browserProc = await startBrowserWithRemote(host, port);
  } else if (browserType === "chromium") {
    browserProc = await startBrowserWithChromium();
  } else if (browserType === "lightpanda") {
    browserProc = await startBrowserWithLightPanda();
  } else if (remoteHost) {
    const url = new URL(remoteHost);
    const host = url.hostname;
    const port = parseInt(url.port, 10) || 9222;
    browserProc = await startBrowserWithRemote(host, port);
  } else {
    browserProc = await startBrowser();
  }

  try {
    let cdpUrl: string;
    if (browserProc.remote) {
      cdpUrl = remoteHost!;
      if (cdpUrl.includes("0.0.0.0")) {
        cdpUrl = cdpUrl.replace("0.0.0.0", "localhost");
      }
    } else {
      cdpUrl = `http://127.0.0.1:${browserProc.port}`;
    }
    cdpConn = await connectToLightPanda(cdpUrl);

    return {
      cdpConn,
      browserProc,
      port: browserProc.port,
    };
  } catch (error) {
    if (cdpConn) {
      await closeCDPConnection(cdpConn).catch(() => {});
    }
    if (browserProc) {
      stopBrowser(browserProc);
    }
    throw error;
  }
}

async function startBrowserWithRemote(host: string, port: number): Promise<BrowserProcess> {
  const { connectToRemoteBrowser } = await import("./browser.js");
  return connectToRemoteBrowser(host, port);
}

async function startBrowserWithChromium(): Promise<BrowserProcess> {
  const { startChromium } = await import("./browser.js");
  const { getChromiumPath } = await import("./config.js");
  return startChromium({ executablePath: getChromiumPath() });
}

async function startBrowserWithLightPanda(): Promise<BrowserProcess> {
  const { startLightPanda } = await import("./browser.js");
  return startLightPanda();
}

export async function releaseBrowserConnection(conn: BrowserConnection): Promise<void> {
  if (conn.cdpConn) {
    await closeCDPConnection(conn.cdpConn).catch(() => {});
  }
  if (conn.browserProc) {
    stopBrowser(conn.browserProc);
  }
}