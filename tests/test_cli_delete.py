from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gemiterm.cli import cli
from gemiterm.exceptions import GeminiAPIError


class TestDelete:
    def test_delete_with_force(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "test"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "--force", "cid123"])
            assert result.exit_code == 0
            assert "Deleted" in result.output
            mock_client.delete_chat.assert_called_once_with("cid123")

    def test_delete_with_confirmation_yes(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.input_with_exit", return_value="yes"),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "test"},
            ]
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "cid123"])
            assert result.exit_code == 0
            assert "Deleted" in result.output
            mock_client.delete_chat.assert_called_once_with("cid123")

    def test_delete_with_confirmation_no(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
            patch("gemiterm.cli.input_with_exit", return_value="no"),
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "cid123"])
            assert result.exit_code == 0
            assert "Cancelled" in result.output
            mock_client.delete_chat.assert_not_called()

    def test_delete_conversation_not_found(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.side_effect = GeminiAPIError("Not found")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "--force", "nonexistent"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_delete_no_active_profiles(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "--force", "cid123"])
            assert result.exit_code == 2
            assert "No active profiles found" in result.output

    def test_delete_api_error(self, active_profiles):
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=active_profiles),
            patch("gemiterm.cli.load_cookies") as mock_cookies,
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_cookies.return_value = ("sid123", "ts123")
            mock_client = MagicMock()
            mock_client.fetch_chat.return_value = [
                {"role": "user", "content": "test"},
            ]
            mock_client.delete_chat.side_effect = GeminiAPIError("API error")
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "--force", "cid123"])
            assert result.exit_code == 1
            assert "API error" in result.output
