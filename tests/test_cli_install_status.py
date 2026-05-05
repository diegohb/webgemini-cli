"""Tests for install-browser, status commands and root cli group."""
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest
from click.testing import CliRunner

from gemiterm.cli import cli


class TestRootCliGroup:
    """Tests for the root cli group."""

    def test_version_flag(self):
        """Test that --version shows the version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.2.2" in result.output

    def test_help_flag(self):
        """Test that --help shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_no_args_exits_with_2(self):
        """Test that running without args exits with code 2 (shows help)."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 2


class TestInstallBrowser:
    """Tests for the install-browser command (hidden)."""

    def test_install_browser_non_frozen_success(self):
        """Test install-browser with Python available runs playwright install successfully."""
        runner = CliRunner()
        with patch("sys.executable", "/usr/bin/python"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                result = runner.invoke(cli, ["install-browser"])
                assert result.exit_code == 0
                assert "Chromium installed successfully" in result.output

    def test_install_browser_non_frozen_failure(self):
        """Test install-browser with playwright install failure raises ClickException."""
        runner = CliRunner()
        with patch("sys.executable", "/usr/bin/python"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Installation failed")
                result = runner.invoke(cli, ["install-browser"])
                assert result.exit_code != 0

    def test_install_browser_frozen_fallback_to_py3(self):
        """Test install-browser in frozen env falls back to py -3 method."""
        runner = CliRunner()
        with patch("sys.frozen", True, create=True):
            with patch("shutil.which") as mock_which:
                def which_side_effect(cmd):
                    if cmd == "py":
                        return "C:/Windows/py.exe"
                    elif cmd in ("python", "python3"):
                        return None
                    return None

                mock_which.side_effect = which_side_effect

                with patch("subprocess.run") as mock_run:
                    def run_side_effect(cmd, **kwargs):
                        if "-3" in cmd and "--version" in cmd:
                            return MagicMock(returncode=0, stdout="Python 3.11.0", stderr="")
                        if "playwright" in cmd and "install" in cmd:
                            return MagicMock(returncode=0, stdout="", stderr="")
                        return MagicMock(returncode=0, stdout="", stderr="")

                    mock_run.side_effect = run_side_effect

                    result = runner.invoke(cli, ["install-browser"])
                    assert result.exit_code == 0
                    assert "Chromium installed successfully" in result.output

    def test_install_browser_falls_back_to_download_chromium(self):
        """Test install-browser when all playwright install attempts fail falls back to download."""
        runner = CliRunner()
        with patch("sys.frozen", True, create=True):
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")

                with patch("gemiterm.cli._check_existing_browser", return_value=False):
                    with patch("gemiterm.cli._download_chromium_fallback") as mock_download:
                        result = runner.invoke(cli, ["install-browser"])
                        assert result.exit_code == 0
                        assert "Chromium installed successfully" in result.output
                        mock_download.assert_called_once()

    def test_install_browser_all_download_urls_fail(self):
        """Test install-browser when all download URLs fail raises RuntimeError."""
        runner = CliRunner()
        with patch("sys.frozen", True, create=True):
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")

                with patch("gemiterm.cli._check_existing_browser", return_value=False):
                    with patch("gemiterm.cli._download_chromium_fallback") as mock_download:
                        mock_download.side_effect = RuntimeError("Failed to download Chromium from all sources")
                        result = runner.invoke(cli, ["install-browser"])
                        assert result.exit_code != 0


class TestStatus:
    """Tests for the status command."""

    @pytest.fixture
    def mock_paths(self, tmp_path):
        """Mock config paths to use temp directory."""
        storage_path = tmp_path / "storage_state.json"
        config_dir = tmp_path / ".config" / "gemiterm"
        config_dir.mkdir(parents=True, exist_ok=True)
        with patch("gemiterm.config.get_storage_state_path", return_value=storage_path):
            with patch("gemiterm.config._get_config_dir", return_value=config_dir):
                yield storage_path

    def test_status_not_authenticated(self, mock_paths):
        """Test status when storage file does not exist shows not authenticated."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 2
        assert "Not authenticated" in result.output

    def test_status_cookie_expired(self, mock_paths):
        """Test status when cookies are expired shows expired message."""
        from gemiterm.exceptions import CookieExpiredError

        storage_path = mock_paths
        storage_path.touch()

        runner = CliRunner()
        with patch("gemiterm.cli.load_cookies", side_effect=CookieExpiredError("Session expired")):
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 2
            assert "expired" in result.output.lower()

    def test_status_authentication_error(self, mock_paths):
        """Test status when authentication is invalid shows authentication invalid."""
        from gemiterm.exceptions import AuthenticationError

        storage_path = mock_paths
        storage_path.touch()

        runner = CliRunner()
        with patch("gemiterm.cli.load_cookies", side_effect=AuthenticationError("Invalid")):
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 2
            assert "invalid" in result.output.lower()

    def test_status_api_error(self, mock_paths):
        """Test status when API error occurs shows API connection issue."""
        from gemiterm.exceptions import GeminiAPIError

        storage_path = mock_paths
        storage_path.touch()

        runner = CliRunner()
        with patch("gemiterm.cli.load_cookies", return_value=("abc", "xyz")):
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.side_effect = GeminiAPIError("Connection failed")
                mock_client_class.return_value = mock_client
                result = runner.invoke(cli, ["status"])
                assert result.exit_code == 1
                assert "API" in result.output or "connection" in result.output.lower()

    def test_status_connected(self, mock_paths):
        """Test status when connected shows authenticated and connected."""
        storage_path = mock_paths
        storage_path.touch()

        runner = CliRunner()
        with patch("gemiterm.cli.load_cookies", return_value=("abc", "xyz")):
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.return_value = []
                mock_client_class.return_value = mock_client
                result = runner.invoke(cli, ["status"])
                assert result.exit_code == 0
                assert "connected" in result.output.lower()

    def test_status_unknown_error(self, mock_paths):
        """Test status when unknown error occurs shows generic error."""
        storage_path = mock_paths
        storage_path.touch()

        runner = CliRunner()
        with patch("gemiterm.cli.load_cookies", return_value=("abc", "xyz")):
            with patch("gemiterm.cli.GeminiClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.list_chats.side_effect = ValueError("Unexpected error")
                mock_client_class.return_value = mock_client
                result = runner.invoke(cli, ["status"])
                assert result.exit_code == 1
                assert "Unknown error" in result.output