import { lightpanda } from "@lightpanda/browser";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import type { Readable } from "node:stream";

export interface LightPandaOptions {
  host: string;
  port: number;
}

export interface BrowserProcess {
  stdout: Readable | null;
  stderr: Readable | null;
  proc: ChildProcessWithoutNullStreams;
}

const DEFAULT_OPTIONS: LightPandaOptions = {
  host: "127.0.0.1",
  port: 9222,
};

export async function startBrowser(
  options: Partial<LightPandaOptions> = {}
): Promise<BrowserProcess> {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  const proc = await lightpanda.serve({
    host: opts.host,
    port: opts.port,
  });

  return {
    stdout: proc.stdout,
    stderr: proc.stderr,
    proc,
  };
}

export function stopBrowser(browser: BrowserProcess): void {
  if (browser.stdout) {
    browser.stdout.destroy();
  }
  if (browser.stderr) {
    browser.stderr.destroy();
  }
  browser.proc.kill();
}