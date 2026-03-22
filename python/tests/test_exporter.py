from webgemini_cli.exporter import (
    format_chat_as_markdown,
    _format_content,
    _format_code_blocks,
)


class TestFormatChatAsMarkdown:
    def test_basic_user_message(self):
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
        ]
        result = format_chat_as_markdown(messages, "Test Chat")
        assert "**User:**" in result
        assert "Hello, how are you?" in result

    def test_basic_assistant_message(self):
        messages = [
            {"role": "model", "content": "I'm doing well, thank you!"},
        ]
        result = format_chat_as_markdown(messages, "Test Chat")
        assert "**Gemini:**" in result
        assert "I'm doing well, thank you!" in result

    def test_conversation_id_in_header(self):
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        result = format_chat_as_markdown(messages, "Test Chat", conversation_id="abc123")
        assert "<!-- conversation_id: abc123 -->" in result

    def test_yaml_front_matter_with_metadata(self):
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        result = format_chat_as_markdown(
            messages, "Test Chat", conversation_id="abc123", include_metadata=True
        )
        assert "---" in result
        assert 'title: "Test Chat"' in result
        assert "export_date:" in result
        assert "message_count: 1" in result

    def test_multiple_messages(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "model", "content": "I'm great!"},
        ]
        result = format_chat_as_markdown(messages, "Multi Message Chat")
        assert result.count("**User:**") == 2
        assert result.count("**Gemini:**") == 2

    def test_timestamp_if_present(self):
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-15 10:30:00"},
        ]
        result = format_chat_as_markdown(messages, "Test Chat")
        assert "<small>2024-01-15 10:30:00</small>" in result

    def test_title_in_output(self):
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        result = format_chat_as_markdown(messages, "My Special Chat")
        assert "# My Special Chat" in result


class TestFormatContent:
    def test_plain_text_unchanged(self):
        content = "This is plain text without any code."
        result = _format_content(content)
        assert result == content

    def test_code_blocks_preserved(self):
        content = "Here is some code:\n```python\nprint('hello')\n```"
        result = _format_content(content)
        assert "```python" in result
        assert "print('hello')" in result


class TestFormatCodeBlocks:
    def test_simple_code_block(self):
        content = "```python\nprint('hello')\n```"
        result = _format_code_blocks(content)
        assert result == content

    def test_code_block_with_language(self):
        content = "```javascript\nconst x = 1;\n```"
        result = _format_code_blocks(content)
        assert "```javascript" in result

    def test_empty_language(self):
        content = "```\ncode without language\n```"
        result = _format_code_blocks(content)
        assert "```" in result

    def test_multiple_code_blocks(self):
        content = "First block:\n```python\nprint(1)\n```\nSecond block:\n```javascript\nconsole.log(2)\n```"
        result = _format_code_blocks(content)
        assert result.count("```") == 4

    def test_inline_code_not_modified(self):
        content = "Use `inline code` in text"
        result = _format_code_blocks(content)
        assert result == content
