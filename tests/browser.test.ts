import { describe, test, expect, beforeEach, afterEach, mock } from "bun:test";
import { Readable } from "node:stream";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import type { Browser as PlaywrightBrowser } from "playwright";
import type { BrowserProcess } from "../src/browser";

const TEST_DIR = join(tmpdir(), "webgemini_browser_test");

import { existsSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

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

const ORIGINAL_BROWSER_TYPE = Bun.env.BROWSER_TYPE;
const ORIGINAL_CHROMIUM_PATH = Bun.env.CHROMIUM_PATH;
const ORIGINAL_LIGHTPANDA_HOST = Bun.env.LIGHTPANDA_HOST;
const ORIGINAL_BROWSER_FALLBACK = Bun.env.BROWSER_FALLBACK;

beforeEach(() => {
  cleanupTestDir();
  setupTestDir();
});

afterEach(() => {
  cleanupTestDir();
  if (ORIGINAL_BROWSER_TYPE === undefined) {
    delete Bun.env.BROWSER_TYPE;
  } else {
    Bun.env.BROWSER_TYPE = ORIGINAL_BROWSER_TYPE;
  }
  if (ORIGINAL_CHROMIUM_PATH === undefined) {
    delete Bun.env.CHROMIUM_PATH;
  } else {
    Bun.env.CHROMIUM_PATH = ORIGINAL_CHROMIUM_PATH;
  }
  if (ORIGINAL_LIGHTPANDA_HOST === undefined) {
    delete Bun.env.LIGHTPANDA_HOST;
  } else {
    Bun.env.LIGHTPANDA_HOST = ORIGINAL_LIGHTPANDA_HOST;
  }
  if (ORIGINAL_BROWSER_FALLBACK === undefined) {
    delete Bun.env.BROWSER_FALLBACK;
  } else {
    Bun.env.BROWSER_FALLBACK = ORIGINAL_BROWSER_FALLBACK;
  }
});

function createMockPlaywrightBrowser(mockProc = { pid: 12345 }) {
  return {
    process: () => mockProc,
    close: () => Promise.resolve(),
  } as unknown as PlaywrightBrowser;
}

function createMockLightPandaProcess() {
  return {
    stdout: { destroy: () => {} } as unknown as Readable,
    stderr: { destroy: () => {} } as unknown as Readable,
    kill: () => {},
  };
}

describe("browser.ts - startChromium()", () => {
  test("launches Chromium with default executablePath", async () => {
    const mockBrowser = createMockPlaywrightBrowser();
    let capturedOptions: any = null;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async (options: any) => {
          capturedOptions = options;
          return mockBrowser;
        },
      },
    }));

    const { startChromium } = await import("../src/browser");
    const result = await startChromium({});

    expect(capturedOptions).toEqual({
      headless: false,
      executablePath: undefined,
      args: ["--remote-debugging-port=9222"],
    });
    expect(result.port).toBe(9222);
    expect(result.remote).toBe(false);
    expect(result.proc).not.toBeNull();
  });

  test("launches Chromium with custom executablePath", async () => {
    const mockBrowser = createMockPlaywrightBrowser();
    const customPath = "/custom/chromium/path";
    let capturedOptions: any = null;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async (options: any) => {
          capturedOptions = options;
          return mockBrowser;
        },
      },
    }));

    const { startChromium } = await import("../src/browser");
    const result = await startChromium({ executablePath: customPath });

    expect(capturedOptions).toEqual({
      headless: false,
      executablePath: customPath,
      args: ["--remote-debugging-port=9222"],
    });
    expect(result.port).toBe(9222);
  });

  test("throws ChromiumNotFoundError when Chromium is not found", async () => {
    const { ChromiumNotFoundError } = await import("../src/errors");
    const notFoundError = new Error("Chrome not found");
    (notFoundError as NodeJS.ErrnoException).code = "ENOENT";
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          throw notFoundError;
        },
      },
    }));

    const { startChromium } = await import("../src/browser");
    await expect(startChromium({})).rejects.toThrow(ChromiumNotFoundError);
  });

  test("rethrows non-ENOENT errors", async () => {
    const genericError = new Error("Some other error");
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          throw genericError;
        },
      },
    }));

    const { startChromium } = await import("../src/browser");
    await expect(startChromium({})).rejects.toThrow("Some other error");
  });
});

describe("browser.ts - startLightPanda()", () => {
  test("starts LightPanda with default options", async () => {
    const mockProc = createMockLightPandaProcess();
    let capturedOptions: any = null;
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async (options: any) => {
          capturedOptions = options;
          return mockProc;
        },
      },
    }));

    const { startLightPanda } = await import("../src/browser");
    const result = await startLightPanda({});

    expect(capturedOptions).toEqual({
      host: "127.0.0.1",
      port: 9222,
    });
    expect(result.port).toBe(9222);
    expect(result.remote).toBe(false);
  });

  test("starts LightPanda with custom host and port", async () => {
    const mockProc = createMockLightPandaProcess();
    let capturedOptions: any = null;
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async (options: any) => {
          capturedOptions = options;
          return mockProc;
        },
      },
    }));

    const { startLightPanda } = await import("../src/browser");
    const result = await startLightPanda({ host: "192.168.1.1", port: 9299 });

    expect(capturedOptions).toEqual({
      host: "192.168.1.1",
      port: 9299,
    });
    expect(result.port).toBe(9299);
  });

  test("throws LightPandaNotFoundError when LightPanda is not found", async () => {
    const { LightPandaNotFoundError } = await import("../src/errors");
    const notFoundError = new Error("LightPanda not found");
    (notFoundError as NodeJS.ErrnoException).code = "ENOENT";
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async () => {
          throw notFoundError;
        },
      },
    }));

    const { startLightPanda } = await import("../src/browser");
    await expect(startLightPanda({})).rejects.toThrow(LightPandaNotFoundError);
  });

  test("throws PortInUseError when all ports are in use", async () => {
    const { PortInUseError } = await import("../src/errors");
    const portInUseError = new Error("Port in use");
    (portInUseError as NodeJS.ErrnoException).code = "EADDRINUSE";
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async () => {
          throw portInUseError;
        },
      },
    }));

    const { startLightPanda } = await import("../src/browser");
    await expect(startLightPanda({ port: 9222 })).rejects.toThrow(PortInUseError);
  });
});

describe("browser.ts - connectToRemoteBrowser()", () => {
  test("connects to remote browser with host and port", async () => {
    const { connectToRemoteBrowser } = await import("../src/browser");
    const result = await connectToRemoteBrowser("192.168.1.100", 9333);

    expect(result.port).toBe(9333);
    expect(result.remote).toBe(true);
    expect(result.proc).toBeNull();
    expect(result.stdout).toBeNull();
    expect(result.stderr).toBeNull();
  });
});

describe("browser.ts - startBrowser()", () => {
  test("starts Chromium when BROWSER_TYPE=chromium", async () => {
    Bun.env.BROWSER_TYPE = "chromium";
    delete Bun.env.CHROMIUM_PATH;

    const mockBrowser = createMockPlaywrightBrowser();
    let launchCalled = false;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          launchCalled = true;
          return mockBrowser;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(launchCalled).toBe(true);
    expect(result.port).toBe(9222);
    expect(result.remote).toBe(false);
  });

  test("starts Chromium with custom path when CHROMIUM_PATH is set", async () => {
    Bun.env.BROWSER_TYPE = "chromium";
    Bun.env.CHROMIUM_PATH = "/custom/chromium";

    const mockBrowser = createMockPlaywrightBrowser();
    let capturedExecutablePath: string | undefined = undefined;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async (options: any) => {
          capturedExecutablePath = options.executablePath;
          return mockBrowser;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    await startBrowser();

    expect(capturedExecutablePath).toBe("/custom/chromium");
  });

  test("starts LightPanda when BROWSER_TYPE=lightpanda", async () => {
    Bun.env.BROWSER_TYPE = "lightpanda";

    const mockProc = createMockLightPandaProcess();
    let serveCalled = false;
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async () => {
          serveCalled = true;
          return mockProc;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(serveCalled).toBe(true);
    expect(result.port).toBe(9222);
    expect(result.remote).toBe(false);
  });

  test("falls back to Chromium when LightPanda fails and BROWSER_FALLBACK=true", async () => {
    Bun.env.BROWSER_TYPE = "lightpanda";
    Bun.env.BROWSER_FALLBACK = "true";

    const lightpandaError = new Error("LightPanda not found");
    (lightpandaError as NodeJS.ErrnoException).code = "ENOENT";
    
    let lightpandaServeCalled = false;
    let chromiumLaunchCalled = false;
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async () => {
          lightpandaServeCalled = true;
          throw lightpandaError;
        },
      },
    }));

    const mockBrowser = createMockPlaywrightBrowser();
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          chromiumLaunchCalled = true;
          return mockBrowser;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(lightpandaServeCalled).toBe(true);
    expect(chromiumLaunchCalled).toBe(true);
    expect(result.port).toBe(9222);
  });

  test("propagates LightPanda error when BROWSER_FALLBACK=false", async () => {
    const { LightPandaNotFoundError } = await import("../src/errors");
    Bun.env.BROWSER_TYPE = "lightpanda";
    Bun.env.BROWSER_FALLBACK = "false";

    const lightpandaError = new Error("LightPanda not found");
    (lightpandaError as NodeJS.ErrnoException).code = "ENOENT";
    
    mock.module("@lightpanda/browser", () => ({
      lightpanda: {
        serve: async () => {
          throw lightpandaError;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    await expect(startBrowser()).rejects.toThrow(LightPandaNotFoundError);
  });

  test("connects to remote browser when BROWSER_TYPE=remote with LIGHTPANDA_HOST", async () => {
    Bun.env.BROWSER_TYPE = "remote";
    Bun.env.LIGHTPANDA_HOST = "ws://192.168.1.100:9333";

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(result.port).toBe(9333);
    expect(result.remote).toBe(true);
  });

  test("throws error when BROWSER_TYPE=remote but LIGHTPANDA_HOST is not set", async () => {
    const { BrowserConnectionError } = await import("../src/errors");
    Bun.env.BROWSER_TYPE = "remote";
    delete Bun.env.LIGHTPANDA_HOST;

    const { startBrowser } = await import("../src/browser");
    await expect(startBrowser()).rejects.toThrow(BrowserConnectionError);
  });

  test("defaults to Chromium when BROWSER_TYPE is not set", async () => {
    delete Bun.env.BROWSER_TYPE;

    const mockBrowser = createMockPlaywrightBrowser();
    let launchCalled = false;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          launchCalled = true;
          return mockBrowser;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(launchCalled).toBe(true);
    expect(result.port).toBe(9222);
  });

  test("defaults to Chromium when BROWSER_TYPE is invalid", async () => {
    Bun.env.BROWSER_TYPE = "firefox";

    const mockBrowser = createMockPlaywrightBrowser();
    let launchCalled = false;
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => {
          launchCalled = true;
          return mockBrowser;
        },
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(launchCalled).toBe(true);
    expect(result.port).toBe(9222);
  });
});

describe("browser.ts - stopBrowser()", () => {
  test("does nothing for remote browser", async () => {
    const { stopBrowser } = await import("../src/browser");
    const browserProcess: BrowserProcess = {
      stdout: null,
      stderr: null,
      proc: null,
      port: 9222,
      remote: true,
    };

    expect(() => stopBrowser(browserProcess)).not.toThrow();
  });

  test("handles null stdout and stderr gracefully", async () => {
    const mockProc = { kill: () => {} };
    
    const { stopBrowser } = await import("../src/browser");
    const browserProcess: BrowserProcess = {
      stdout: null,
      stderr: null,
      proc: mockProc as unknown as ChildProcessWithoutNullStreams,
      port: 9222,
      remote: false,
    };

    expect(() => stopBrowser(browserProcess)).not.toThrow();
  });

  test("handles null proc gracefully", async () => {
    const mockStdout = { destroy: () => {} };
    const mockStderr = { destroy: () => {} };

    const { stopBrowser } = await import("../src/browser");
    const browserProcess: BrowserProcess = {
      stdout: mockStdout as unknown as Readable,
      stderr: mockStderr as unknown as Readable,
      proc: null,
      port: 9222,
      remote: false,
    };

    expect(() => stopBrowser(browserProcess)).not.toThrow();
  });

  test("destroys stdout and stderr streams and kills proc", async () => {
    let stdoutDestroyed = false;
    let stderrDestroyed = false;
    let procKilled = false;
    
    const mockStdout = { 
      destroy: () => { stdoutDestroyed = true; } 
    };
    const mockStderr = { 
      destroy: () => { stderrDestroyed = true; } 
    };
    const mockProc = { 
      kill: () => { procKilled = true; } 
    };

    const { stopBrowser } = await import("../src/browser");
    const browserProcess: BrowserProcess = {
      stdout: mockStdout as unknown as Readable,
      stderr: mockStderr as unknown as Readable,
      proc: mockProc as unknown as ChildProcessWithoutNullStreams,
      port: 9222,
      remote: false,
    };

    stopBrowser(browserProcess);

    expect(stdoutDestroyed).toBe(true);
    expect(stderrDestroyed).toBe(true);
    expect(procKilled).toBe(true);
  });
});

describe("browser.ts - isChromiumNotFoundError()", () => {
  test("returns true for ENOENT error", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("not found");
    (error as NodeJS.ErrnoException).code = "ENOENT";
    expect(isChromiumNotFoundError(error)).toBe(true);
  });

  test("returns true for error message containing 'executable doesn't exist'", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("executable doesn't exist");
    expect(isChromiumNotFoundError(error)).toBe(true);
  });

  test("returns true for error message containing 'no chrome/chromium installed'", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("no chrome/chromium installed");
    expect(isChromiumNotFoundError(error)).toBe(true);
  });

  test("returns true for error message containing 'Chrome not found'", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("Chrome not found");
    expect(isChromiumNotFoundError(error)).toBe(true);
  });

  test("returns true for error message containing 'Chromium not found'", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("Chromium not found");
    expect(isChromiumNotFoundError(error)).toBe(true);
  });

  test("returns false for generic error", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    const error = new Error("some other error");
    expect(isChromiumNotFoundError(error)).toBe(false);
  });

  test("returns false for non-Error object", async () => {
    const { isChromiumNotFoundError } = await import("../src/browser");
    expect(isChromiumNotFoundError("not an error")).toBe(false);
    expect(isChromiumNotFoundError(null)).toBe(false);
    expect(isChromiumNotFoundError(undefined)).toBe(false);
  });
});

describe("browser.ts - verbose and debug flags", () => {
  test("setBrowserVerbose enables verbose mode", async () => {
    const { setBrowserVerbose } = await import("../src/browser");
    expect(() => setBrowserVerbose(true)).not.toThrow();
    expect(() => setBrowserVerbose(false)).not.toThrow();
  });

  test("setDebugBrowser enables debug mode", async () => {
    const { setDebugBrowser } = await import("../src/browser");
    expect(() => setDebugBrowser(true)).not.toThrow();
    expect(() => setDebugBrowser(false)).not.toThrow();
  });
});

describe("browser.ts - BrowserProcess interface", () => {
  test("BrowserProcess has correct structure", async () => {
    const mockBrowser = createMockPlaywrightBrowser();
    
    mock.module("playwright", () => ({
      chromium: {
        launch: async () => mockBrowser,
      },
    }));

    const { startBrowser } = await import("../src/browser");
    const result = await startBrowser();

    expect(result).toHaveProperty("stdout");
    expect(result).toHaveProperty("stderr");
    expect(result).toHaveProperty("proc");
    expect(result).toHaveProperty("port");
    expect(result).toHaveProperty("remote");
    expect(typeof result.port).toBe("number");
    expect(typeof result.remote).toBe("boolean");
  });
});