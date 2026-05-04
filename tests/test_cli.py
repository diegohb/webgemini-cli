from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from gemiterm.cli import cli


class TestProfileRenameWithId:
    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    @patch("gemiterm.cli.rename_profile")
    def test_rename_accepts_id_from_prompt(
        self, mock_rename, mock_default, mock_statuses, tmp_path
    ):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        with patch("gemiterm.cli.console.input", side_effect=["2", "work-account"]):
            result = runner.invoke(cli, ["profile", "rename"], input="2\nwork-account\n")

        mock_rename.assert_called_once_with("work", "work-account")
        assert "work" in result.output
        assert "work-account" in result.output

    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    @patch("gemiterm.cli.rename_profile")
    def test_rename_with_id_argument(
        self, mock_rename, mock_default, mock_statuses
    ):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        with patch("gemiterm.cli.console.input", side_effect=["work-account"]):
            result = runner.invoke(cli, ["profile", "rename", "2", "work-account"])

        mock_rename.assert_called_once_with("work", "work-account")
        assert result.exit_code == 0

    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    def test_rename_with_invalid_id(self, mock_default, mock_statuses):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        with patch("gemiterm.cli.console.input", side_effect=["work-account"]):
            result = runner.invoke(cli, ["profile", "rename"], input="99\n2\nwork-account\n")

        assert "Invalid profile ID" in result.output

    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    def test_rename_table_has_id_column(self, mock_default, mock_statuses, capsys):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        with patch("gemiterm.cli.console.input", side_effect=["2", "work-account"]):
            result = runner.invoke(cli, ["profile", "rename"], input="2\nwork-account\n")

        assert "1" in result.output
        assert "2" in result.output
        assert "personal" in result.output
        assert "work" in result.output


class TestAuthMenuRenameWithId:
    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    @patch("gemiterm.cli.rename_profile")
    def test_auth_rename_accepts_id(self, mock_rename, mock_default, mock_statuses):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        result = runner.invoke(cli, ["auth"], input="R\n2\nwork-account\n")

        mock_rename.assert_called_once_with("work", "work-account")
        assert "work" in result.output

    @patch("gemiterm.cli.list_profile_statuses")
    @patch("gemiterm.cli.get_default_profile_name")
    def test_auth_rename_invalid_id(self, mock_default, mock_statuses):
        mock_statuses.return_value = [
            {"name": "personal", "is_active": True, "exists": True, "expires_at": "N/A"},
            {"name": "work", "is_active": True, "exists": True, "expires_at": "N/A"},
        ]
        mock_default.return_value = "personal"

        runner = CliRunner()
        result = runner.invoke(cli, ["auth"], input="R\n99\n2\nwork-account\n")

        assert "Invalid profile ID" in result.output
