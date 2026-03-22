import type { GeminiMessage } from "./types/gemini.js";

/**
 * Options for chat export formatting.
 */
export interface ExportOptions {
  /** Include metadata (title, export date, message count) at the top of the export */
  includeMetadata?: boolean;
}

function formatContent(content: string): string {
  if (content.includes("```")) {
    return formatCodeBlocks(content);
  }
  return content;
}

function formatCodeBlocks(content: string): string {
  const lines = content.split("\n");
  const result: string[] = [];
  let inCodeBlock = false;
  let codeLanguage = "";

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeLanguage = line.trim().slice(3).trim();
        if (codeLanguage) {
          result.push(`\`\`\`${codeLanguage}`);
        } else {
          result.push("```");
        }
      } else {
        inCodeBlock = false;
        result.push("```");
      }
    } else if (inCodeBlock) {
      result.push(line);
    } else {
      result.push(line);
    }
  }

  return result.join("\n");
}

/**
 * Formats a list of Gemini messages as a Markdown document.
 * @param messages - Array of GeminiMessage objects to format
 * @param title - Title for the exported chat
 * @param conversationId - Optional conversation ID to include as metadata
 * @param options - Export options such as including metadata
 * @returns Formatted Markdown string
 */
export function formatChatAsMarkdown(
  messages: GeminiMessage[],
  title: string,
  conversationId?: string,
  options: ExportOptions = {}
): string {
  const exportDate = new Date().toISOString().replace("T", " ").slice(0, 19);
  const messageCount = messages.length;

  const lines: string[] = [];

  if (conversationId) {
    lines.push(`<!-- conversation_id: ${conversationId} -->`);
  }

  if (options.includeMetadata) {
    lines.push("---");
    lines.push(`title: "${title}"`);
    lines.push(`export_date: "${exportDate}"`);
    lines.push(`message_count: ${messageCount}`);
    lines.push("---\n");
  } else {
    lines.push("");
  }

  lines.push(`# ${title}\n`);

  for (const msg of messages) {
    const role = msg.role || "user";
    const content = msg.content || "";
    const timestamp = (msg as any).timestamp;

    if (role === "user") {
      lines.push("**User:**");
    } else {
      lines.push("**Gemini:**");
    }

    if (timestamp) {
      lines.push(`<small>${timestamp}</small>`);
    }

    lines.push("");
    lines.push(formatContent(content));
    lines.push("");
  }

  return lines.join("\n");
}