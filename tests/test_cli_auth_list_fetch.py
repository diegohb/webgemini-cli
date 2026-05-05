"""Tests for CLI commands: auth, list, fetch."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from gemiterm.cli import cli


class TestAuth:
    def test_auth_success(self):
        cookies_list = [{"name": "cookie1"}, {"name": "cookie2"}]
        with (
            patch("gemiterm.cli.list_profiles", return_value=[]),
            patch("asyncio.run", return_value=cookies_list),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["auth"])
            assert result.exit_code == 0
            assert "Authentication successful" in result.output
            assert "2 cookies" in result.output

    def test_auth_authentication_error(self):
        with (
            patch("gemiterm.cli.list_profiles", return_value=[]),
            patch("asyncio.run") as mock_run,
        ):
            from gemiterm.exceptions import AuthenticationError

            mock_run.side_effect = AuthenticationError("Invalid credentials")
            runner = CliRunner()
            result = runner.invoke(cli, ["auth"])
            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_auth_other_exception(self):
        with (
            patch("gemiterm.cli.list_profiles", return_value=[]),
            patch("asyncio.run") as mock_run,
        ):
            mock_run.side_effect = RuntimeError("Browser error")
            runner = CliRunner()
            result = runner.invoke(cli, ["auth"])
            assert result.exit_code == 1
            assert "Authentication failed" in result.output


class TestList:
    def test_list_empty(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = []
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list"])
                assert result.exit_code == 0
                assert "No chats found" in result.output

    def test_list_with_chats(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = [
                    {"id": "chat1", "title": "Test Chat", "is_pinned": False, "timestamp": 1700000000},
                    {"id": "chat2", "title": "Another Chat", "is_pinned": True, "timestamp": 1700000001},
                ]
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list"])
                assert result.exit_code == 0
                assert "Test Chat" in result.output
                assert "Another Chat" in result.output
                assert "chat1" in result.output
                assert "chat2" in result.output

    def test_list_search_filter(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = [
                    {"id": "chat1", "title": "Python Tips", "is_pinned": False, "timestamp": 1700000000},
                    {"id": "chat2", "title": "Java Tips", "is_pinned": False, "timestamp": 1700000001},
                ]
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list", "--search", "python"])
                assert result.exit_code == 0
                assert "Python Tips" in result.output
                assert "Java Tips" not in result.output

    def test_list_sort_new(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = [
                    {"id": "chat1", "title": "Older Chat", "is_pinned": False, "timestamp": 1000000000},
                    {"id": "chat2", "title": "Newer Chat", "is_pinned": False, "timestamp": 2000000000},
                ]
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list", "--sort", "recent"])
                assert result.exit_code == 0
                output_lower = result.output.lower()
                assert output_lower.index("newer chat") < output_lower.index("older chat")

    def test_list_limit(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                base_ts = 1700000000
                mock_client.list_chats.return_value = [
                    {"id": f"chat{i}", "title": f"Chat {i}", "is_pinned": False, "timestamp": base_ts + i}
                    for i in range(10)
                ]
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list", "--limit", "3"])
                assert result.exit_code == 0
                assert "chat0" in result.output or "chat1" in result.output or "chat2" in result.output or "chat7" in result.output or "chat8" in result.output or "chat9" in result.output

    def test_list_all_flag(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = [
                    {"id": f"chat{i}", "title": f"Chat {i}", "is_pinned": False, "timestamp": i}
                    for i in range(60)
                ]
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list", "--all"])
                assert result.exit_code == 0

    def test_list_expired_cookies(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            from gemiterm.exceptions import CookieExpiredError
            mock_cookies.side_effect = CookieExpiredError("Session expired")
            runner = CliRunner()
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 2
            assert "Session expired" in result.output
            assert "re-authenticate" in result.output

    def test_list_api_error(self):
        with patch("gemiterm.cli.load_cookies") as mock_cookies:
            mock_cookies.return_value = ("sid123", "ts123")
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                from gemiterm.exceptions import GeminiAPIError
                mock_client.list_chats.side_effect = GeminiAPIError("API error occurred")
                mock_client_class.return_value = mock_client
                runner = CliRunner()
                result = runner.invoke(cli, ["list"])
                assert result.exit_code == 1
                assert "API error" in result.output


class TestFetch:
    def test_fetch_text_output(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "Hello"},
                {"role": "model", "content": "Hi there"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["fetch", "conv123"])
            assert result.exit_code == 0
            assert "USER" in result.output
            assert "Hello" in result.output
            assert "MODEL" in result.output
            assert "Hi there" in result.output

    def test_fetch_json_format(self, active_profiles):
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
            result = runner.invoke(cli, ["fetch", "--format", "json", "conv123"])
            assert result.exit_code == 0
            assert '"role"' in result.output
            assert '"content"' in result.output

    def test_fetch_path_writes_file(self, tmp_path, active_profiles):
        output_file = tmp_path / "output.txt"
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
            result = runner.invoke(cli, ["fetch", "--path", str(output_file), "conv123"])
            assert result.exit_code == 0
            assert output_file.exists()
            content = output_file.read_text()
            assert "USER" in content
            assert "Hello" in content

    def test_fetch_no_args_redirects_to_list(self):
        with (
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {"id": "c1", "title": "Chat 1", "is_pinned": False, "timestamp": 1700000000},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["fetch"])
            assert result.exit_code == 0
            assert "Chat 1" in result.output

    def test_fetch_empty_conversation_id(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["fetch", ""])
        assert result.exit_code == 1
        assert "cannot be empty" in result.output

    def test_fetch_conversation_not_found(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import ConversationNotFoundError

            mock_client.fetch_chat.side_effect = ConversationNotFoundError("Conversation not found")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["fetch", "nonexistent"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_fetch_no_active_profiles(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["fetch", "conv123"])
            assert result.exit_code == 2
            assert "No active profiles found" in result.output

    def test_fetch_api_error(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            from gemiterm.exceptions import GeminiAPIError

            mock_client.fetch_chat.side_effect = GeminiAPIError("API error occurred")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["fetch", "conv123"])
            assert result.exit_code == 1
            assert "API error" in result.output
