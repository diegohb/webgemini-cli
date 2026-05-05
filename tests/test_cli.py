from unittest.mock import MagicMock, patch
import json

import pytest
from click.testing import CliRunner

from gemiterm.cli import cli


class TestListCommand:
    """Tests for the list command."""

    @pytest.fixture
    def mock_cookies(self):
        with patch("gemiterm.cli.load_cookies") as mock:
            mock.return_value = ("mock_1psid", "mock_1psidts")
            yield mock

    @pytest.fixture
    def mock_gemini_client(self):
        with patch("gemiterm.cli.GeminiClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list_chats.return_value = [
                {
                    "id": "c_1",
                    "title": "Test Chat 1",
                    "is_pinned": True,
                    "timestamp": 1234567890.0,
                },
                {
                    "id": "c_2",
                    "title": "Test Chat 2",
                    "is_pinned": False,
                    "timestamp": 9876543210.0,
                },
            ]
            mock_client_class.return_value = mock_client
            yield mock_client

    def test_list_default_format(self, mock_cookies, mock_gemini_client):
        """Test list command with default text format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "Test Chat 1" in result.output
        assert "Test Chat 2" in result.output
        assert "c_1" in result.output

    def test_list_json_format(self, mock_cookies, mock_gemini_client):
        """Test list command with JSON format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "c_1"
        assert data[0]["title"] == "Test Chat 1"

    def test_list_json_format_short_flag(self, mock_cookies, mock_gemini_client):
        """Test list command with -f json flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "-f", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    def test_list_with_path_option(self, mock_cookies, mock_gemini_client, tmp_path):
        """Test list command saves to file with --path."""
        output_file = tmp_path / "chats.txt"
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Chat 1" in content
        assert "c_1" in content

    def test_list_with_path_and_json(self, mock_cookies, mock_gemini_client, tmp_path):
        """Test list command with --path and --format json."""
        output_file = tmp_path / "chats.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(output_file), "--format", "json"])

        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_with_short_path_flag(self, mock_cookies, mock_gemini_client, tmp_path):
        """Test list command saves to file with -p."""
        output_file = tmp_path / "chats.txt"
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "-p", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_list_json_stdin_alias(self, mock_cookies, mock_gemini_client):
        """Test that -f/--format work the same as in fetch command."""
        runner = CliRunner()

        result1 = runner.invoke(cli, ["list", "--format", "json"])
        assert result1.exit_code == 0

        result2 = runner.invoke(cli, ["list", "-f", "json"])
        assert result2.exit_code == 0

        assert json.loads(result1.output) == json.loads(result2.output)

    def test_list_path_creates_parent_dirs(self, mock_cookies, mock_gemini_client, tmp_path):
        """Test that --path creates parent directories if they don't exist."""
        output_file = tmp_path / "subdir" / "deep" / "chats.txt"
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_list_empty_chats(self, mock_cookies, mock_gemini_client):
        """Test list command when no chats exist."""
        mock_gemini_client.list_chats.return_value = []
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No chats found" in result.output

    def test_list_json_empty_chats(self, mock_cookies, mock_gemini_client):
        """Test list command with JSON format when no chats exist."""
        mock_gemini_client.list_chats.return_value = []
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []