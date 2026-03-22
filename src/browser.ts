import { lightpanda } from "@lightpanda/browser";
import { chromium, type Browser as PlaywrightBrowser } from "playwright";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import type { Readable } from "node:stream";
import { LightPandaNotFoundError, PortInUseError, BrowserConnectionError, ChromiumNotFoundError } from "./errors.js";
import { getBrowserType, getChromiumPath, getLightPandaHost, getBrowserFallback } from "./config.js";

let verbose = false;
let debugBrowser = false;

export function setBrowserVerbose(v: boolean): void {
  verbose = v;
}

export function setDebugBrowser(v: boolean): void {
  debugBrowser = v;
}

function logBrowserDebug(...args: unknown[]): void {
  if (debugBrowser) {
    console.error("[BROWSER DEBUG]", ...args);
  }
}

function logBrowserVerbose(...args: unknown[]): void {
  if (verbose || debugBrowser) {
    console.error("[BROWSER VERBOSE]", ...args);
  }
}

export interface LightPandaOptions {
  host: string;
  port: number;
}

export interface ChromiumOptions {
  executablePath?: string;
}

export interface BrowserProcess {
  stdout: Readable | null;
  stderr: Readable | null;
  proc: ChildProcessWithoutNullStreams | null;
  port: number;
  remote: boolean;
}

const DEFAULT_OPTIONS: LightPandaOptions = {
  host: "127.0.0.1",
  port: 9222,
};

const PORT_RANGE_START = 9222;
const PORT_RANGE_END = 9332;
const LIGHTPANDA_NOT_FOUND_CODES = ["ENOENT", "ENOFS", "EACCES"];
const CHROMIUM_NOT_FOUND_CODES = ["ENOENT", "ENOFS", "EACCES"];

function isLightPandaNotFoundError(error: unknown): boolean {
  if (error instanceof Error) {
    const code = (error as NodeJS.ErrnoException).code;
    return LIGHTPANDA_NOT_FOUND_CODES.includes(code || "");
  }
  return false;
}

export function isChromiumNotFoundError(error: unknown): boolean {
  if (error instanceof Error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (CHROMIUM_NOT_FOUND_CODES.includes(code || "")) {
      return true;
    }
    return error.message.includes("executable doesn't exist") ||
           error.message.includes("no chrome/chromium installed") ||
           error.message.includes("Chrome not found") ||
           error.message.includes("Chromium not found");
  }
  return false;
}

export async function connectToRemoteBrowser(host: string, port: number): Promise<BrowserProcess> {
  logBrowserDebug(`Connecting to remote browser at ${host}:${port}`);
  return {
    stdout: null,
    stderr: null,
    proc: null,
    port,
    remote: true,
  };
}

let playwrightBrowser: PlaywrightBrowser | null = null;

export async function startChromium(
  options: ChromiumOptions = {}
): Promise<BrowserProcess> {
  logBrowserDebug(`Launching Chromium with executablePath: ${options.executablePath || "default"}`);
  try {
    const browser = await chromium.launch({
      headless: false,
      executablePath: options.executablePath,
      args: ["--remote-debugging-port=9222"],
    });

    playwrightBrowser = browser;

    const proc = browser.process();
    logBrowserDebug(`Chromium launched, PID: ${proc?.pid}, port: 9222`);

    return {
      stdout: null,
      stderr: null,
      proc: proc as ChildProcessWithoutNullStreams | null,
      port: 9222,
      remote: false,
    };
  } catch (error) {
    logBrowserDebug(`Chromium launch failed: ${error instanceof Error ? error.message : String(error)}`);
    if (isChromiumNotFoundError(error)) {
      throw new ChromiumNotFoundError(
        `Chromium browser not found. Please ensure Chromium is installed. ` +
        `Set CHROMIUM_PATH environment variable to specify a custom location.`
      );
    }
    throw error;
  }
}

function isPortInUseError(error: unknown): boolean {
  if (error instanceof Error) {
    const code = (error as NodeJS.ErrnoException).code;
    return code === "EADDRINUSE" || code === "EACCES";
  }
  return false;
}

export async function startLightPanda(
  options: Partial<LightPandaOptions> = {}
): Promise<BrowserProcess> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: unknown = null;

  for (let port = opts.port; port <= PORT_RANGE_END; port++) {
    try {
      logBrowserDebug(`Attempting to start LightPanda on ${opts.host}:${port}`);
      const proc = await lightpanda.serve({
        host: opts.host,
        port,
      });

      logBrowserDebug(`LightPanda started on port ${port}`);
      return {
        stdout: proc.stdout,
        stderr: proc.stderr,
        proc,
        port,
        remote: false,
      };
    } catch (error) {
      lastError = error;
      logBrowserDebug(`LightPanda failed on port ${port}: ${error instanceof Error ? error.message : String(error)}`);
      
      if (isLightPandaNotFoundError(error)) {
        throw new LightPandaNotFoundError(
          `LightPanda browser not found. Please ensure LightPanda is installed. ` +
          `Run 'npm install -g @lightpanda/browser' or visit https://lightpanda.dev`
        );
      }
      
      if (!isPortInUseError(error)) {
        if (error instanceof Error && error.message.includes("connect")) {
          throw new BrowserConnectionError(
            `Could not connect to LightPanda browser on port ${port}. ${error.message}`
          );
        }
        throw error;
      }
    }
  }

  throw new PortInUseError(
    opts.port,
    `Port ${opts.port} is already in use. Tried alternate ports ${PORT_RANGE_START}-${PORT_RANGE_END} without success.`
  );
}

export async function startBrowser(): Promise<BrowserProcess> {
  const browserType = getBrowserType();

  if (browserType === "chromium") {
    logBrowserVerbose("Starting Chromium browser...");
    return startChromium({ executablePath: getChromiumPath() });
  }

  if (browserType === "lightpanda") {
    logBrowserVerbose("Starting LightPanda browser...");
    try {
      return await startLightPanda();
    } catch (lightpandaError) {
      const fallbackEnabled = getBrowserFallback();
      if (!fallbackEnabled) {
        logBrowserVerbose("LightPanda failed and BROWSER_FALLBACK=false, propagating error");
        throw lightpandaError;
      }
      
      logBrowserVerbose(`LightPanda failed: ${lightpandaError instanceof Error ? lightpandaError.message : String(lightpandaError)}`);
      logBrowserVerbose("Attempting Chromium fallback...");
      
      try {
        const chromiumResult = await startChromium({ executablePath: getChromiumPath() });
        logBrowserVerbose("Chromium fallback successful");
        return chromiumResult;
      } catch (chromiumError) {
        logBrowserVerbose(`Chromium fallback also failed: ${chromiumError instanceof Error ? chromiumError.message : String(chromiumError)}`);
        throw lightpandaError;
      }
    }
  }

  const remoteHost = getLightPandaHost();
  if (!remoteHost) {
    throw new BrowserConnectionError(
      `BROWSER_TYPE is set to 'remote' but LIGHTPANDA_HOST is not configured. ` +
      `Set LIGHTPANDA_HOST environment variable or use a different BROWSER_TYPE.`
    );
  }

  const url = new URL(remoteHost);
  const host = url.hostname;
  const port = parseInt(url.port, 10) || 9222;

  return connectToRemoteBrowser(host, port);
}

export function stopBrowser(browser: BrowserProcess): void {
  if (browser.remote) {
    return;
  }
  if (playwrightBrowser) {
    playwrightBrowser.close();
    playwrightBrowser = null;
    return;
  }
  if (browser.stdout) {
    browser.stdout.destroy();
  }
  if (browser.stderr) {
    browser.stderr.destroy();
  }
  if (browser.proc) {
    browser.proc.kill();
  }
}