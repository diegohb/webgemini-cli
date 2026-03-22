import { Command } from "commander";

const program = new Command();

program
  .name("webgemini")
  .description("CLI for Gemini web interactions")
  .version("0.2.0")
  .option("-v, --verbose", "Enable verbose output");

program
  .command("auth")
  .description("Authenticate with Gemini")
  .action(() => {
    console.log("not implemented");
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
  .action(() => {
    console.log("not implemented");
  });

program.parse();
