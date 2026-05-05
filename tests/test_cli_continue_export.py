"""Tests for CLI commands: continue, export, export-all."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from gemiterm.cli import cli


class TestContinue:
    def test_continue_with_message_calls_single(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.continue_chat.return_value = "AI response here"
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["continue", "cid123", "Hello AI"])
            assert result.exit_code == 0
            assert "Response:" in result.output
            mock_client.continue_chat.assert_called_with("cid123", "Hello AI")

    def test_continue_with_no_message_starts_interactive(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["continue", "cid123"])
            assert result.exit_code == 0
            assert "Interactive chat session started" in result.output
            assert "Type your message" in result.output

    def test_continue_conversation_not_found(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import ConversationNotFoundError

            mock_client.continue_chat.side_effect = ConversationNotFoundError("Not found")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["continue", "nonexistent", "Hello"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_continue_no_active_profiles(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["continue", "cid123", "Hello"])
            assert result.exit_code == 2
            assert "No active profiles found" in result.output

    def test_continue_api_error(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import GeminiAPIError

            mock_client.continue_chat.side_effect = GeminiAPIError("API error")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["continue", "cid123", "Hello"])
            assert result.exit_code == 1
            assert "API error" in result.output


class TestExport:
    def test_export_auto_filename_in_cwd(self, tmp_path, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.Path.cwd", return_value=tmp_path),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
                {"role": "model", "content": "Hi there"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "cid123"])
            assert result.exit_code == 0
            assert "Exported to" in result.output
            files = list(tmp_path.glob("gemini-chat-cid123-*.md"))
            assert len(files) == 1

    def test_export_with_output_dir(self, tmp_path, active_profiles):
        output_file = tmp_path / "exported_chat.md"
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "--output", str(output_file), "cid123"])
            assert result.exit_code == 0
            assert "Exported to" in result.output
            assert output_file.exists()

    def test_export_json_format(self, tmp_path, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.Path.cwd", return_value=tmp_path),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "--format", "json", "cid123"])
            assert result.exit_code == 0
            files = list(tmp_path.glob("gemini-chat-cid123-*.json"))
            assert len(files) == 1
            content = files[0].read_text()
            assert '"conversation_id"' in content
            assert '"messages"' in content

    def test_export_markdown_format(self, tmp_path, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.Path.cwd", return_value=tmp_path),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "--format", "markdown", "cid123"])
            assert result.exit_code == 0
            files = list(tmp_path.glob("gemini-chat-cid123-*.md"))
            assert len(files) == 1

    def test_export_include_metadata(self, tmp_path, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.Path.cwd", return_value=tmp_path),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "--include-metadata", "cid123"])
            assert result.exit_code == 0
            files = list(tmp_path.glob("gemini-chat-cid123-*.md"))
            assert len(files) == 1
            content = files[0].read_text()
            assert "---" in content
            assert "title:" in content

    def test_export_conversation_not_found(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import ConversationNotFoundError

            mock_client.fetch_chat.side_effect = ConversationNotFoundError("Not found")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "nonexistent"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_export_no_active_profiles(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["export", "cid123"])
            assert result.exit_code == 2
            assert "No active profiles found" in result.output

    def test_export_file_io_error(self, tmp_path, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            unreadable_dir = tmp_path / "unreadable"
            unreadable_dir.mkdir()
            unreadable_dir.chmod(0o000)
            try:
                runner = CliRunner()
                result = runner.invoke(cli, ["export", "--output", str(unreadable_dir), "cid123"])
                assert result.exit_code == 1
            finally:
                unreadable_dir.chmod(0o755)


class TestExportAll:
    def test_export_all_no_chats(self):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = []
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all"])
            assert result.exit_code == 0
            assert "No chats found" in result.output

    def test_export_all_with_since_filter(self, tmp_path):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {"id": "chat1", "title": "Test Chat", "timestamp": 1700000000},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all", "--since", "2024-01-01"])
            assert result.exit_code == 0

    def test_export_all_with_output_dir_and_metadata(self, tmp_path):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {"id": "chat1", "title": "Test Chat", "timestamp": 1700000000},
            ]
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
                {"role": "model", "content": "Hi there"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(
                cli, ["export-all", "--output-dir", str(tmp_path), "--include-metadata"]
            )
            assert result.exit_code == 0
            assert "Exported 1 conversations" in result.output
            files = list(tmp_path.glob("gemini-chat-chat1-*.md"))
            assert len(files) == 1
            content = files[0].read_text()
            assert "---" in content
            index_file = tmp_path / "_index.md"
            assert index_file.exists()

    def test_export_all_include_metadata_flag(self, tmp_path):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {"id": "chat1", "title": "Test Chat", "timestamp": 1700000000},
            ]
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all", "--include-metadata"])
            assert result.exit_code == 0

    def test_export_all_expired_cookies(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            from gemiterm.exceptions import CookieExpiredError

            mock_cookies.side_effect = CookieExpiredError("Session expired")
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all"])
            assert result.exit_code == 2
            assert "Session expired" in result.output
            assert "re-authenticate" in result.output

    def test_export_all_api_error(self):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import GeminiAPIError

            mock_client.list_chats.side_effect = GeminiAPIError("API error")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all"])
            assert result.exit_code == 1
            assert "API error" in result.output

    def test_export_all_progress_bar(self, tmp_path):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {"id": "chat1", "title": "Test Chat", "timestamp": 1700000000},
            ]
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["export-all", "--output-dir", str(tmp_path)])
            assert result.exit_code == 0
            assert "Exporting" in result.output or "Exported" in result.output
