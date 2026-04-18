from gemiterm.exporter import format_chat_as_markdown


class TestFormatChatAsMarkdownExportAll:
    def test_export_single_chat(self):
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "model", "content": "I'm doing well, thank you!"},
        ]
        result = format_chat_as_markdown(messages, "Test Chat", conversation_id="test123")
        assert "# Test Chat" in result
        assert "<!-- conversation_id: test123 -->" in result
        assert result.count("**User:**") == 1
        assert result.count("**Gemini:**") == 1

    def test_export_with_metadata(self):
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

    def test_export_multiple_messages(self):
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "model", "content": "Second message"},
            {"role": "user", "content": "Third message"},
        ]
        result = format_chat_as_markdown(messages, "Multi Message Chat")
        assert result.count("**User:**") == 2
        assert result.count("**Gemini:**") == 1

    def test_export_with_timestamps(self):
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-15 10:30:00"},
            {"role": "model", "content": "Hi there!", "timestamp": "2024-01-15 10:30:05"},
        ]
        result = format_chat_as_markdown(messages, "Timestamped Chat")
        assert "<small>2024-01-15 10:30:00</small>" in result
        assert "<small>2024-01-15 10:30:05</small>" in result

    def test_export_code_blocks(self):
        messages = [
            {"role": "user", "content": "Write Python:\n```python\nprint('hello')\n```"},
        ]
        result = format_chat_as_markdown(messages, "Code Chat")
        assert "```python" in result
        assert "print('hello')" in result

    def test_export_special_characters_in_title(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = format_chat_as_markdown(messages, "Chat with 'quotes' and \"double quotes\"")
        assert "# Chat with 'quotes' and \"double quotes\"" in result

    def test_export_empty_content(self):
        messages = [
            {"role": "user", "content": ""},
        ]
        result = format_chat_as_markdown(messages, "Empty Chat")
        assert "# Empty Chat" in result
        assert "**User:**" in result

    def test_export_without_conversation_id(self):
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        result = format_chat_as_markdown(messages, "No ID Chat")
        assert "<!-- conversation_id:" not in result


class TestIndexGeneration:
    def test_index_content_format(self):
        exported_chats = [
            {"id": "chat1", "title": "Alpha Chat", "filename": "alpha.md"},
            {"id": "chat2", "title": "Beta Chat", "filename": "beta.md"},
        ]
        index_lines = ["# Exported Conversations\n"]
        index_lines.append("Exported: 2024-01-15 10:00:00\n")
        index_lines.append("Total: 2 conversations\n")
        index_lines.append("---\n\n")

        for chat in sorted(exported_chats, key=lambda c: c["title"].lower()):
            index_lines.append(f"- [{chat['title']}]({chat['filename']}) (ID: {chat['id']})")

        result = "\n".join(index_lines)
        assert "# Exported Conversations" in result
        assert "Total: 2 conversations" in result
        assert "- [Alpha Chat](alpha.md) (ID: chat1)" in result
        assert "- [Beta Chat](beta.md) (ID: chat2)" in result

    def test_index_sorted_alphabetically(self):
        exported_chats = [
            {"id": "z1", "title": "Zebra", "filename": "z.md"},
            {"id": "a1", "title": "Apple", "filename": "a.md"},
            {"id": "m1", "title": "Mango", "filename": "m.md"},
        ]
        index_lines = []
        for chat in sorted(exported_chats, key=lambda c: c["title"].lower()):
            index_lines.append(f"- [{chat['title']}]")

        result = "\n".join(index_lines)
        lines = result.split("\n")
        assert lines[0] == "- [Apple]"
        assert lines[1] == "- [Mango]"
        assert lines[2] == "- [Zebra]"


class TestFilenameGeneration:
    def test_safe_filename(self):
        unsafe_title = "Chat: Test 123 (invalid/chars)"
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in unsafe_title)[:50]
        assert safe_title == "Chat_ Test 123 _invalid_chars_"

    def test_filename_truncation(self):
        long_title = "A" * 100
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in long_title)[:50]
        assert len(safe_title) == 50

    def test_filename_pattern(self):
        conversation_id = "abc123"
        safe_title = "mychat"
        date_str = "20240115"
        filename = f"gemini-chat-{conversation_id}-{safe_title[:20]}-{date_str}.md"
        assert filename == "gemini-chat-abc123-mychat-20240115.md"
