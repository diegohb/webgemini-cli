import { Command } from "commander";
import { login, loadCookies } from "./auth.js";
import { GeminiClient } from "./gemini-client.js";
import { formatChatAsMarkdown } from "./exporter.js";
import {
  AuthenticationError,
  CookieExpiredError,
  LightPandaNotFoundError,
  ChromiumNotFoundError,
  PortInUseError,
  BrowserClosedError,
  BrowserConnectionError,
  GeminiAPIError,
  ConversationNotFoundError,
  WebGeminiError,
  DockerNotAvailableError,
  DockerContainerError,
} from "./errors.js";
import { checkCookieFreshness } from "./auth.js";
import { getStorageStatePath, CONFIG_DIR_DEFAULT, getLightPandaHost, getLightPandaDocker, getBrowserType, getRemoteHost, getBrowserFallback, type BrowserType } from "./config.js";
import { getConfigPath, getConfigDir, loadConfig, saveConfig, getConfigValue, setConfigValue, mergeConfigWithEnv, type ResolvedConfig, type Config } from "./config-file.js";
import { setBrowserVerbose, setDebugBrowser } from "./browser.js";
import { existsSync } from "fs";
import { join } from "path";

const program = new Command();
let verbose = false;

function logVerbose(...args: unknown[]): void {
  if (verbose) {
    console.error("[VERBOSE]", ...args);
  }
}

function getBrowserFromFlags(cliBrowser?: string): BrowserType {
  if (cliBrowser === "chromium" || cliBrowser === "lightpanda" || cliBrowser === "remote") {
    return cliBrowser;
  }
  return getBrowserType();
}

function getResolvedConfig(cliBrowser?: string): ResolvedConfig {
  return mergeConfigWithEnv(cliBrowser);
}

program
  .name("webgemini")
  .description("CLI for Gemini web interactions")
  .version("0.2.0")
  .option("-v, --verbose", "Enable verbose output")
  .option("-b, --browser <type>", "Browser type (chromium|lightpanda|remote)")
  .option("--debug-browser", "Enable detailed browser debugging")
  .hook("preAction", (thisCommand) => {
    verbose = thisCommand.opts().verbose === true;
    const debugBrowser = thisCommand.opts().debugBrowser === true;
    setBrowserVerbose(verbose);
    setDebugBrowser(debugBrowser);
  });

program
  .command("auth")
  .description("Authenticate with Gemini")
  .option("--lightpanda-host <ws://host:port>", "Connect to remote LightPanda browser (deprecated, use --browser remote --remote-host)")
  .option("--lightpanda-docker", "Use Docker LightPanda (auto-provision if needed) (deprecated, use --browser lightpanda)")
  .option("--remote-host <ws://host:port>", "Remote browser WebSocket URL (required when --browser remote is used)")
  .action(async (options: { browser?: string; lightpandaHost?: string; lightpandaDocker?: boolean; remoteHost?: string }) => {
    try {
      logVerbose("Starting browser authentication...");
      console.log("Starting browser authentication...");

      if (options.lightpandaHost) {
        console.log(`\x1b[33m  Warning: --lightpanda-host is deprecated. Use --browser remote --remote-host <url>\x1b[0m`);
      }
      if (options.lightpandaDocker) {
        console.log(`\x1b[33m  Warning: --lightpanda-docker is deprecated. Use --browser lightpanda\x1b[0m`);
      }

      const browserType = getBrowserFromFlags(options.browser);
      let remoteHost: string | undefined;

      if (browserType === "remote") {
        if (options.remoteHost) {
          remoteHost = options.remoteHost;
        } else if (options.lightpandaHost) {
          remoteHost = options.lightpandaHost;
        } else {
          console.error(`\x1b[31m✗ Error:\x1b[0m --browser remote requires --remote-host <ws://host:port>`);
          process.exit(1);
        }
      } else if (browserType === "lightpanda") {
        if (options.lightpandaDocker || getLightPandaDocker()) {
          const fallbackEnabled = getBrowserFallback();
          try {
            const { ensureLightPandaRunning } = await import("./docker.js");
            remoteHost = await ensureLightPandaRunning();
            console.log(`\x1b[90m  Auto-provisioning Docker LightPanda...\x1b[0m`);
          } catch (dockerError) {
            if (fallbackEnabled) {
              console.log(`\x1b[33m  LightPanda Docker failed: ${dockerError instanceof Error ? dockerError.message : String(dockerError)}\x1b[0m`);
              console.log(`\x1b[90m  Falling back to Chromium...\x1b[0m`);
              logVerbose("LightPanda Docker failed, using Chromium as fallback browser");
              remoteHost = undefined;
            } else {
              console.error(`\x1b[31m✗ LightPanda Docker failed:\x1b[0m ${dockerError instanceof Error ? dockerError.message : String(dockerError)}`);
              throw dockerError;
            }
          }
        } else {
          remoteHost = getLightPandaHost();
        }
      }

      logVerbose(`Using browser type: ${browserType}`);
      if (remoteHost) {
        logVerbose(`Remote host: ${remoteHost}`);
      }

      const cookies = await login(browserType, remoteHost);
      logVerbose(`Authentication successful, saved ${cookies.length} cookies`);
      console.log(`\x1b[32m✓ Authentication successful!\x1b[0m`);
      console.log(`\x1b[90m  Saved ${cookies.length} cookies.\x1b[0m`);
    } catch (error) {
      handleAuthError(error);
    }
  });

program
  .command("list")
  .description("List all conversations")
  .option("-n, --limit <number>", "Maximum number of results", "10")
  .action(async (options: { limit: string }) => {
    try {
      logVerbose("Loading cookies...");
      const cookies = await loadCookies();
      const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      logVerbose(`Loaded ${cookies.length} cookies`);

      const limit = Math.min(Math.max(parseInt(options.limit, 10) || 10, 1), 50);
      logVerbose(`Calling listChats with limit ${limit}...`);

      const client = new GeminiClient(cookieDict);
      const chats = await client.listChats();

      if (chats.length === 0) {
        console.log("No conversations found.");
        return;
      }

      const displayChats = chats.slice(0, limit);
      console.log(`\nFound ${chats.length} conversation(s):\n`);

      const tableData = displayChats.map((chat, i) => ({
        "#": i + 1,
        "Conversation ID": chat.id,
        "Title": chat.title,
      }));

      console.table(tableData);

      if (chats.length > limit) {
        console.log(`\x1b[90mShowing ${limit} of ${chats.length} conversations. Use -n to increase limit (max 50).\x1b[0m`);
      }
    } catch (error) {
      handleCommandError(error, 2);
    }
  });

program
  .command("fetch")
  .description("Fetch a specific conversation")
  .argument("<conversation-id>", "Conversation ID to fetch")
  .option("-f, --format <format>", "Output format (text, json)", "text")
  .action(async (conversationId: string, options: { format: string }) => {
    try {
      if (!conversationId || conversationId.trim() === "") {
        console.error(`\x1b[31m✗ Error:\x1b[0m Conversation ID cannot be empty`);
        process.exit(1);
      }

      logVerbose(`Loading cookies for fetch, conversationId: ${conversationId}...`);
      const cookies = await loadCookies();
      const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      logVerbose("Cookies loaded successfully");

      const client = new GeminiClient(cookieDict);
      logVerbose(`Fetching chat ${conversationId}...`);
      const messages = await client.fetchChat(conversationId);

      if (options.format === "json") {
        console.log(JSON.stringify({ conversation_id: conversationId, messages }, null, 2));
      } else {
        if (messages.length === 0) {
          console.log("No messages found in this conversation.");
          return;
        }

        for (const msg of messages) {
          const role = msg.role === "user" ? "USER" : "MODEL";
          const color = msg.role === "user" ? "\x1b[32m" : "\x1b[34m";
          console.log(`\n${color}${role}:\x1b[0m`);
          console.log(msg.content);
        }
      }
    } catch (error) {
      if (error instanceof ConversationNotFoundError) {
        console.error(`\x1b[31m✗ Conversation not found:\x1b[0m ${error.message}`);
        console.error(`\x1b[90m  Run 'webgemini list' to see available conversations.\x1b[0m`);
        process.exit(1);
      }
      handleCommandError(error, 1);
    }
  });

program
  .command("continue")
  .description("Continue a conversation with a new message")
  .argument("<conversation-id>", "Conversation ID")
  .argument("<message>", "Message to send")
  .action(async (conversationId: string, message: string) => {
    try {
      if (!conversationId || conversationId.trim() === "") {
        console.error(`\x1b[31m✗ Error:\x1b[0m Conversation ID cannot be empty`);
        process.exit(1);
      }

      if (!message || message.trim() === "") {
        console.error(`\x1b[31m✗ Error:\x1b[0m Message cannot be empty`);
        process.exit(1);
      }

      logVerbose(`Loading cookies for continue, conversationId: ${conversationId}...`);
      const cookies = await loadCookies();
      const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      logVerbose("Cookies loaded successfully");

      const client = new GeminiClient(cookieDict);
      logVerbose(`Sending message to conversation ${conversationId}...`);
      const response = await client.continueChat(conversationId, message);
      logVerbose("Response received");

      console.log(response);
    } catch (error) {
      if (error instanceof ConversationNotFoundError) {
        console.error(`\x1b[31m✗ Conversation not found:\x1b[0m ${error.message}`);
        console.error(`\x1b[90m  Run 'webgemini list' to see available conversations.\x1b[0m`);
        process.exit(1);
      }
      if (error instanceof CookieExpiredError) {
        console.error(`\x1b[31m✗ Cookie expired:\x1b[0m ${error.message}`);
        console.error(`\x1b[90m  Run 'webgemini auth' to re-authenticate.\x1b[0m`);
        process.exit(2);
      }
      handleCommandError(error, 1);
    }
  });

program
  .command("export")
  .description("Export a conversation")
  .argument("<conversation-id>", "Conversation ID to export")
  .option("-f, --format <format>", "Export format (markdown, json)", "markdown")
  .option("-o, --output <path>", "Output file path")
  .option("--include-metadata", "Include metadata in export", false)
  .action(async (conversationId: string, options: { format: string; output?: string; includeMetadata?: boolean }) => {
    try {
      if (!conversationId || conversationId.trim() === "") {
        console.error(`\x1b[31m✗ Error:\x1b[0m Conversation ID cannot be empty`);
        process.exit(1);
      }

      logVerbose(`Loading cookies for export, conversationId: ${conversationId}...`);
      const cookies = await loadCookies();
      const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      logVerbose("Cookies loaded successfully");

      const client = new GeminiClient(cookieDict);
      logVerbose(`Fetching chat ${conversationId} for export...`);
      const messages = await client.fetchChat(conversationId);

      const date = new Date().toISOString().slice(0, 10);
      const defaultFilename = `gemini-chat-${conversationId}-${date}.${options.format === "json" ? "json" : "md"}`;
      const outputPath = options.output || defaultFilename;

      let content: string;
      if (options.format === "json") {
        content = JSON.stringify({ conversation_id: conversationId, messages }, null, 2);
      } else {
        const title = `Chat Export ${conversationId}`;
        content = formatChatAsMarkdown(messages, title, conversationId, {
          includeMetadata: options.includeMetadata,
        });
      }

      await Bun.write(outputPath, content);
      console.log(`\x1b[32m✓ Exported to ${outputPath}\x1b[0m`);
    } catch (error) {
      if (error instanceof ConversationNotFoundError) {
        console.error(`\x1b[31m✗ Conversation not found:\x1b[0m ${error.message}`);
        console.error(`\x1b[90m  Run 'webgemini list' to see available conversations.\x1b[0m`);
        process.exit(1);
      }
      handleCommandError(error, 1);
    }
  });

program
  .command("export-all")
  .description("Export all conversations")
  .option("-f, --format <format>", "Export format (markdown, json)", "markdown")
  .option("-o, --output-dir <directory>", "Output directory", "./exports")
  .option("--since <date>", "Only export conversations since this date (YYYY-MM-DD)")
  .option("--include-metadata", "Include metadata in exports", false)
  .action(async (options: { format: string; outputDir: string; since?: string; includeMetadata?: boolean }) => {
    try {
      logVerbose("Loading cookies for export-all...");
      const cookies = await loadCookies();
      const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      logVerbose("Cookies loaded successfully");

      const client = new GeminiClient(cookieDict);
      logVerbose("Listing all chats...");
      const chats = await client.listChats();

      if (chats.length === 0) {
        console.log("No conversations to export.");
        return;
      }

      let filteredChats = chats;
      if (options.since) {
        const sinceDate = new Date(options.since);
        sinceDate.setHours(0, 0, 0, 0);
        filteredChats = chats.filter((chat) => {
          return true;
        });
      }

      console.log(`Exporting ${filteredChats.length} conversation(s) to ${options.outputDir}...`);

      const indexLines: string[] = [];
      let successCount = 0;
      let failCount = 0;

      for (let i = 0; i < filteredChats.length; i++) {
        const chat = filteredChats[i]!;
        const progress = `[${i + 1}/${filteredChats.length}]`;
        process.stdout.write(`\r${progress} Exporting "${chat.title}"...`);

        try {
          const messages = await client.fetchChat(chat.id);

          const date = new Date().toISOString().slice(0, 10);
          const safeTitle = chat.title.replace(/[/\\?%*:|"<>]/g, "-").slice(0, 50);
          const filename = `gemini-chat-${chat.id}-${date}.${options.format === "json" ? "json" : "md"}`;
          const outputPath = join(options.outputDir, filename);

          let content: string;
          if (options.format === "json") {
            content = JSON.stringify({ conversation_id: chat.id, title: chat.title, messages }, null, 2);
          } else {
            content = formatChatAsMarkdown(messages, chat.title, chat.id, {
              includeMetadata: options.includeMetadata,
            });
          }

          await Bun.write(outputPath, content);
          indexLines.push(`- [${chat.title}](./${filename})`);
          successCount++;
        } catch (error) {
          failCount++;
          logVerbose(`\nFailed to export ${chat.id}: ${error}`);
        }
      }

      console.log(`\n\n\x1b[32m✓ Exported ${successCount} conversation(s)\x1b[0m`);
      if (failCount > 0) {
        console.log(`\x1b[31m✗ Failed to export ${failCount} conversation(s)\x1b[0m`);
      }

      if (indexLines.length > 0) {
        const indexContent = `# Gemini Chat Exports\n\nExported on ${new Date().toISOString().slice(0, 10)}\n\n${indexLines.join("\n")}\n`;
        await Bun.write(join(options.outputDir, "_index.md"), indexContent);
      }
    } catch (error) {
      handleCommandError(error, 1);
    }
  });

const configCmd = program
  .command("config")
  .description("Manage configuration settings");

configCmd
  .command("get")
  .description("Get a configuration value")
  .argument("<path>", "Configuration path (e.g., browser.type)")
  .action(async (path: string) => {
    const value = getConfigValue(path);
    if (value === undefined) {
      console.error(`\x1b[31m✗ Configuration path '${path}' not found\x1b[0m`);
      process.exit(1);
    }
    console.log(JSON.stringify(value, null, 2));
  });

configCmd
  .command("set")
  .description("Set a configuration value")
  .argument("<path>", "Configuration path (e.g., browser.type)")
  .argument("<value>", "Configuration value")
  .action(async (path: string, value: string) => {
    let parsedValue: unknown = value;
    if (value === "true" || value === "false") {
      parsedValue = value === "true";
    } else if (!isNaN(Number(value))) {
      parsedValue = Number(value);
    }
    setConfigValue(path, parsedValue);
    console.log(`\x1b[32m✓ Set ${path} = ${JSON.stringify(parsedValue)}\x1b[0m`);
  });

configCmd
  .command("list")
  .description("List all configuration values")
  .action(async () => {
    const resolved = getResolvedConfig();
    const config = loadConfig();
    const configPath = getConfigPath();

    console.log(`\x1b[1mConfiguration\x1b[0m`);
    console.log(`  Config file: \x1b[90m${configPath}\x1b[0m`);
    console.log();

    console.log(`\x1b[1mBrowser Settings\x1b[0m`);
    console.log(`  browser.type:`);
    console.log(`    current:  \x1b[90m${resolved.browserType}\x1b[0m`);
    console.log(`    source:   \x1b[90m${resolved.sources.browserType}\x1b[0m`);

    console.log(`  browser.chromiumPath:`);
    console.log(`    current:  \x1b[90m${resolved.chromiumPath ?? "(none)"}\x1b[0m`);
    console.log(`    source:   \x1b[90m${resolved.sources.chromiumPath}\x1b[0m`);

    console.log(`  browser.remoteHost:`);
    console.log(`    current:  \x1b[90m${resolved.remoteHost ?? "(none)"}\x1b[0m`);
    console.log(`    source:   \x1b[90m${resolved.sources.remoteHost}\x1b[0m`);

    console.log();
    console.log(`\x1b[1mConfig File Contents\x1b[0m`);
    console.log(`\x1b[90m${JSON.stringify(config, null, 2)}\x1b[0m`);
  });

configCmd
  .command("init")
  .description("Initialize a default configuration file")
  .action(async () => {
    const configPath = getConfigPath();
    const existingConfig = loadConfig();

    if (Object.keys(existingConfig).length > 0) {
      console.error(`\x1b[33m⚠ Config file already exists at ${configPath}\x1b[0m`);
      console.error(`\x1b[90m  Use 'webgemini config set' to modify existing values.\x1b[0m`);
      process.exit(1);
    }

    const resolved = getResolvedConfig();
    const defaultConfig: Config = {
      browser: {
        type: resolved.browserType,
        chromiumPath: resolved.chromiumPath,
        remoteHost: resolved.remoteHost,
      },
    };

    saveConfig(defaultConfig);
    console.log(`\x1b[32m✓ Created default config at ${configPath}\x1b[0m`);
    console.log(`\x1b[90m  Edit this file or use 'webgemini config set' to customize.\x1b[0m`);
  });

program
  .command("status")
  .description("Check authentication status")
  .action(async (options: { browser?: string }) => {
    try {
      const configDir = Bun.env.WEBGEMINI_CONFIG_DIR ?? CONFIG_DIR_DEFAULT;
      const storagePath = getStorageStatePath();
      const storageExists = existsSync(storagePath);
      const resolved = getResolvedConfig(options.browser);

      console.log(`\x1b[1mConfiguration Status\x1b[0m`);
      console.log(`  Config directory: \x1b[90m${configDir}\x1b[0m`);
      console.log(`  Storage file:    \x1b[90m${storagePath}\x1b[0m`);
      console.log(`  Browser type:    \x1b[90m${resolved.browserType}\x1b[0m \x1b[90m(${resolved.sources.browserType})\x1b[0m`);

      if (!storageExists) {
        console.log(`\n  Authentication: \x1b[31m✗ Missing\x1b[0m`);
        console.log(`\x1b[90m  Run 'webgemini auth' to authenticate.\x1b[0m`);
        process.exit(2);
      }

      const cookies = await loadCookies();
      const isFresh = checkCookieFreshness(cookies);

      if (isFresh) {
        console.log(`  Authentication: \x1b[32m✓ Valid\x1b[0m`);
      } else {
        console.log(`  Authentication: \x1b[33m⚠ Expired\x1b[0m`);
        console.log(`\x1b[90m  Run 'webgemini auth' to re-authenticate.\x1b[0m`);
        process.exit(2);
      }

      try {
        const cookieDict = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
        const client = new GeminiClient(cookieDict);
        logVerbose("Testing API connection with listChats...");
        await client.listChats();
        console.log(`  API connection: \x1b[32m✓ Connected\x1b[0m`);
      } catch (error) {
        console.log(`  API connection: \x1b[31m✗ Error\x1b[0m`);
        if (error instanceof GeminiAPIError) {
          console.log(`\x1b[90m  ${error.message}\x1b[0m`);
        }
        process.exit(1);
      }
    } catch (error) {
      if (error instanceof AuthenticationError) {
        console.log(`  Authentication: \x1b[31m✗ Invalid\x1b[0m`);
        console.log(`\x1b[90m  Run 'webgemini auth' to re-authenticate.\x1b[0m`);
        process.exit(2);
      }
      handleCommandError(error, 1);
    }
  });

function handleAuthError(error: unknown): void {
  if (error instanceof LightPandaNotFoundError) {
    console.error(`\x1b[31m✗ LightPanda not found:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Try using Chromium instead: --browser chromium\x1b[0m`);
    console.error(`\x1b[90m  Or set BROWSER_FALLBACK=false to disable automatic fallback.\x1b[0m`);
    process.exit(1);
  }
  if (error instanceof ChromiumNotFoundError) {
    console.error(`\x1b[31m✗ Chromium not found:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Set CHROMIUM_PATH environment variable to specify a custom location.\x1b[0m`);
    process.exit(1);
  }
  if (error instanceof PortInUseError) {
    console.error(`\x1b[31m✗ Port in use:\x1b[0m ${error.message}`);
    process.exit(1);
  }
  if (error instanceof BrowserClosedError) {
    console.error(`\x1b[31m✗ Browser closed:\x1b[0m ${error.message}`);
    process.exit(1);
  }
  if (error instanceof BrowserConnectionError) {
    console.error(`\x1b[31m✗ Connection failed:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Use --browser remote --remote-host <ws://host:port> to connect to a remote browser.\x1b[0m`);
    console.error(`\x1b[90m  Or try using Chromium instead: --browser chromium\x1b[0m`);
    process.exit(1);
  }
  if (error instanceof DockerNotAvailableError) {
    console.error(`\x1b[31m✗ Docker not available:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Install Docker from https://docs.docker.com/get-docker/\x1b[0m`);
    console.error(`\x1b[90m  Or try using Chromium instead: --browser chromium\x1b[0m`);
    process.exit(1);
  }
  if (error instanceof DockerContainerError) {
    console.error(`\x1b[31m✗ Docker container error:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Try using Chromium instead: --browser chromium\x1b[0m`);
    console.error(`\x1b[90m  Or set BROWSER_FALLBACK=false to disable automatic fallback.\x1b[0m`);
    process.exit(1);
  }
  if (error instanceof AuthenticationError) {
    console.error(`\x1b[31m✗ Authentication failed:\x1b[0m ${error.message}`);
    process.exit(1);
  }
  if (error instanceof CookieExpiredError) {
    console.error(`\x1b[31m✗ Cookie expired:\x1b[0m ${error.message}`);
    process.exit(1);
  }
  if (error instanceof Error) {
    if (error.message.includes("ENOENT") || error.message.includes("not found")) {
      console.error(`\x1b[31m✗ LightPanda not found:\x1b[0m Please ensure LightPanda is installed. Run 'npm install -g @lightpanda/browser' or visit https://lightpanda.dev`);
      console.error(`\x1b[90m  Or try using Chromium instead: --browser chromium\x1b[0m`);
      process.exit(1);
    }
    if (error.message.includes("ECONNREFUSED")) {
      console.error(`\x1b[31m✗ Connection failed:\x1b[0m Could not connect to LightPanda. Port may be in use.`);
      console.error(`\x1b[90m  Try using Chromium instead: --browser chromium\x1b[0m`);
      process.exit(1);
    }
    console.error(`\x1b[31m✗ Error:\x1b[0m ${error.message}`);
    process.exit(1);
  }
  console.error(`\x1b[31m✗ Unknown error occurred\x1b[0m`);
  process.exit(1);
}

function handleCommandError(error: unknown, defaultExitCode: number): void {
  if (error instanceof CookieExpiredError) {
    console.error(`\x1b[31m✗ Cookie expired:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Run 'webgemini auth' to re-authenticate.\x1b[0m`);
    process.exit(2);
  }
  if (error instanceof AuthenticationError) {
    console.error(`\x1b[31m✗ Authentication error:\x1b[0m ${error.message}`);
    console.error(`\x1b[90m  Run 'webgemini auth' to re-authenticate.\x1b[0m`);
    process.exit(2);
  }
  if (error instanceof GeminiAPIError) {
    console.error(`\x1b[31m✗ API error:\x1b[0m ${error.message}`);
    process.exit(defaultExitCode);
  }
  if (error instanceof WebGeminiError) {
    console.error(`\x1b[31m✗ Error:\x1b[0m ${error.message}`);
    process.exit(defaultExitCode);
  }
  if (error instanceof Error) {
    console.error(`\x1b[31m✗ Error:\x1b[0m ${error.message}`);
    process.exit(defaultExitCode);
  }
  console.error(`\x1b[31m✗ Unknown error occurred\x1b[0m`);
  process.exit(defaultExitCode);
}

program.parse();