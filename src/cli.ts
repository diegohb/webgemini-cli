import { Command } from "commander";
import { login, loadCookies } from "./auth.js";
import { AuthenticationError, CookieExpiredError, LightPandaNotFoundError, PortInUseError, BrowserClosedError, BrowserConnectionError } from "./errors.js";

const program = new Command();

program
  .name("webgemini")
  .description("CLI for Gemini web interactions")
  .version("0.2.0")
  .option("-v, --verbose", "Enable verbose output");

program
  .command("auth")
  .description("Authenticate with Gemini")
  .action(async () => {
    try {
      console.log("Starting browser authentication...");
      const cookies = await login();
      console.log(`\x1b[32m✓ Authentication successful!\x1b[0m`);
      console.log(`\x1b[90m  Saved ${cookies.length} cookies.\x1b[0m`);
    } catch (error) {
      if (error instanceof LightPandaNotFoundError) {
        console.error(`\x1b[31m✗ LightPanda not found:\x1b[0m ${error.message}`);
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
          process.exit(1);
        }
        if (error.message.includes("ECONNREFUSED")) {
          console.error(`\x1b[31m✗ Connection failed:\x1b[0m Could not connect to LightPanda. Port may be in use.`);
          process.exit(1);
        }
        console.error(`\x1b[31m✗ Error:\x1b[0m ${error.message}`);
        process.exit(1);
      }
      console.error(`\x1b[31m✗ Unknown error occurred\x1b[0m`);
      process.exit(1);
    }
  });

program
  .command("list")
  .description("List all conversations")
  .action(() => {
    console.log("not implemented");
  });

program
  .command("fetch")
  .description("Fetch a specific conversation")
  .argument("<conversation-id>", "Conversation ID to fetch")
  .action((conversationId: string) => {
    console.log("not implemented");
  });

program
  .command("continue")
  .description("Continue a conversation with a new message")
  .argument("<conversation-id>", "Conversation ID")
  .argument("<message>", "Message to send")
  .action((conversationId: string, message: string) => {
    console.log("not implemented");
  });

program
  .command("export")
  .description("Export a conversation")
  .argument("<conversation-id>", "Conversation ID to export")
  .option("-f, --format <format>", "Export format (markdown, json)", "markdown")
  .action((conversationId: string, options: { format: string }) => {
    console.log("not implemented");
  });

program
  .command("export-all")
  .description("Export all conversations")
  .option("-f, --format <format>", "Export format (markdown, json)", "markdown")
  .option("-o, --output <directory>", "Output directory", "./exports")
  .action((options: { format: string; output: string }) => {
    console.log("not implemented");
  });

program
  .command("status")
  .description("Check authentication status")
  .action(async () => {
    try {
      const cookies = await loadCookies();
      console.log(`\x1b[32m✓ Authenticated\x1b[0m`);
      console.log(`\x1b[90m  ${cookies.length} cookies stored\x1b[0m`);
    } catch (error) {
      console.error(`\x1b[31m✗ Not authenticated:\x1b[0m ${(error as Error).message}`);
      process.exit(1);
    }
  });

program.parse();