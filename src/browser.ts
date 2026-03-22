import { lightpanda } from "@lightpanda/browser";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import type { Readable } from "node:stream";
import { LightPandaNotFoundError, PortInUseError, BrowserConnectionError } from "./errors.js";

export interface LightPandaOptions {
  host: string;
  port: number;
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

function isLightPandaNotFoundError(error: unknown): boolean {
  if (error instanceof Error) {
    const code = (error as NodeJS.ErrnoException).code;
    return LIGHTPANDA_NOT_FOUND_CODES.includes(code || "");
  }
  return false;
}

export async function connectToRemoteBrowser(host: string, port: number): Promise<BrowserProcess> {
  return {
    stdout: null,
    stderr: null,
    proc: null,
    port,
    remote: true,
  };
}

function isPortInUseError(error: unknown): boolean {
  if (error instanceof Error) {
    const code = (error as NodeJS.ErrnoException).code;
    return code === "EADDRINUSE" || code === "EACCES";
  }
  return false;
}

export async function startBrowser(
  options: Partial<LightPandaOptions> = {}
): Promise<BrowserProcess> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: unknown = null;

  for (let port = opts.port; port <= PORT_RANGE_END; port++) {
    try {
      const proc = await lightpanda.serve({
        host: opts.host,
        port,
      });

      return {
        stdout: proc.stdout,
        stderr: proc.stderr,
        proc,
        port,
        remote: false,
      };
    } catch (error) {
      lastError = error;
      
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

export function stopBrowser(browser: BrowserProcess): void {
  if (browser.remote) {
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