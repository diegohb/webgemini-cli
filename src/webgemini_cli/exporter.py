from datetime import datetime
from typing import Any


def format_chat_as_markdown(
    messages: list[dict[str, Any]],
    title: str,
    conversation_id: str | None = None,
    include_metadata: bool = False,
) -> str:
    export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_count = len(messages)

    lines: list[str] = []

    if conversation_id:
        lines.append(f"<!-- conversation_id: {conversation_id} -->")

    if include_metadata:
        lines.append("---")
        lines.append(f'title: "{title}"')
        lines.append(f'export_date: "{export_date}"')
        lines.append(f"message_count: {message_count}")
        lines.append("---\n")
    else:
        lines.append("")

    lines.append(f"# {title}\n")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp")
        images = msg.get("images")
        citations = msg.get("citations")

        if role == "user":
            lines.append("**User:**")
        else:
            lines.append("**Gemini:**")

        if timestamp:
            lines.append(f"<small>{timestamp}</small>")

        lines.append("")
        lines.append(_format_content(content))
        lines.append("")

        if images:
            lines.append("")
            lines.append("**Images:**")
            for img in images:
                if isinstance(img, dict):
                    lines.append(f"- {img.get('title', 'Image')}: {img.get('url', '')}")
                else:
                    lines.append(f"- {img}")
            lines.append("")

        if citations:
            lines.append("")
            lines.append("**Citations:**")
            for cit in citations:
                if isinstance(cit, dict):
                    lines.append(f"- [{cit.get('title', 'Source')}]({cit.get('url', '')})")
                else:
                    lines.append(f"- {cit}")
            lines.append("")

    return "\n".join(lines)


def _format_content(content: str) -> str:
    if "```" in content:
        return _format_code_blocks(content)
    return content


def _format_code_blocks(content: str) -> str:
    lines = content.split("\n")
    result: list[str] = []
    in_code_block = False
    code_language = ""

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_language = line.strip()[3:].strip()
                if code_language:
                    result.append(f"```{code_language}")
                else:
                    result.append("```")
            else:
                in_code_block = False
                result.append("```")
        elif in_code_block:
            result.append(line)
        else:
            result.append(line)

    return "\n".join(result)
