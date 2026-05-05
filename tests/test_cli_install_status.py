"""Tests for install-browser, status commands and root cli group."""
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gemiterm.cli import cli


class TestRootCliGroup:
    """Tests for the root cli group."""
   
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

    def test_status_no_profiles(self):
        """Test status when no profiles exist."""
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 2
            assert "No profiles found" in result.output

    def test_status_with_active_profile(self):
        """Test status shows profile table when profiles exist."""
        statuses = [
            {
                "name": "work",
                "is_active": True,
                "exists": True,
                "expires_at": "1/15/2026 3:00PM (Wednesday)",
                "is_default": True,
            },
        ]
        with patch("gemiterm.cli.list_profile_statuses", return_value=statuses):
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 0
            assert "work" in result.output
            assert "Active" in result.output

    def test_status_with_expired_profile(self):
        """Test status shows expired profile."""
        statuses = [
            {
                "name": "old",
                "is_active": False,
                "exists": True,
                "expires_at": None,
                "is_default": True,
            },
        ]
        with patch("gemiterm.cli.list_profile_statuses", return_value=statuses):
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 0
            assert "old" in result.output
            assert "Refresh needed" in result.output