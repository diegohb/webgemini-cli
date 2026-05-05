"""Tests for multi-profile authentication support."""
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gemiterm.cli import cli
from gemiterm.config import (
    get_default_profile_name,
    get_profile_path,
    get_profiles_dir,
    list_profiles,
    set_default_profile_name,
)


class TestConfigProfileFunctions:
    def test_get_profiles_dir(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            assert get_profiles_dir() == tmp_path / "profiles"

    def test_get_profile_path(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            expected = tmp_path / "profiles" / "work" / "storage_state.json"
            assert get_profile_path("work") == expected

    def test_get_default_profile_name_no_marker(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            assert get_default_profile_name() == "default"

    def test_get_default_profile_name_with_marker(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            profiles_dir.mkdir(parents=True)
            (profiles_dir / ".default").write_text("work")
            assert get_default_profile_name() == "work"

    def test_set_default_profile_name(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            set_default_profile_name("personal")
            marker = tmp_path / "profiles" / ".default"
            assert marker.read_text() == "personal"

    def test_list_profiles_empty(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            assert list_profiles() == []

    def test_list_profiles_with_dirs(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "work").mkdir()
            (profiles_dir / "personal").mkdir()
            (profiles_dir / ".default").write_text("work")
            result = list_profiles()
            assert result == ["personal", "work"]

    def test_ensure_config_dir_creates_profiles_dir(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            from gemiterm.config import ensure_config_dir

            ensure_config_dir()
            assert (tmp_path / "profiles").exists()


class TestAuthManagerProfiles:
    def _make_fresh_cookies(self, days_offset=30):
        expires = (datetime.now() + timedelta(days=days_offset)).timestamp()
        return {
            "cookies": [
                {"name": "__Secure-1PSID", "value": "sid123"},
                {"name": "__Secure-1PSIDTS", "value": "ts123", "expires": expires},
            ]
        }

    def test_load_cookies_with_profile(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profile_dir = tmp_path / "profiles" / "work"
            profile_dir.mkdir(parents=True)
            cookies = self._make_fresh_cookies()
            (profile_dir / "storage_state.json").write_text(json.dumps(cookies))

            from gemiterm.auth_manager import load_cookies

            sid, ts = load_cookies("work")
            assert sid == "sid123"
            assert ts == "ts123"

    def test_load_cookies_default_profile(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            default_dir = profiles_dir / "default"
            default_dir.mkdir(parents=True)
            cookies = self._make_fresh_cookies()
            (default_dir / "storage_state.json").write_text(json.dumps(cookies))
            (profiles_dir / ".default").write_text("default")

            from gemiterm.auth_manager import load_cookies

            sid, ts = load_cookies()
            assert sid == "sid123"

    def test_load_cookies_missing_profile(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            from gemiterm.auth_manager import load_cookies
            from gemiterm.exceptions import AuthenticationError

            with pytest.raises(AuthenticationError, match="Authentication required"):
                load_cookies("nonexistent")

    def test_get_profile_status_active(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profile_dir = tmp_path / "profiles" / "work"
            profile_dir.mkdir(parents=True)
            cookies = self._make_fresh_cookies(days_offset=30)
            (profile_dir / "storage_state.json").write_text(json.dumps(cookies))

            from gemiterm.auth_manager import get_profile_status

            status = get_profile_status("work")
            assert status["exists"] is True
            assert status["is_active"] is True
            assert status["needs_refresh"] is False

    def test_get_profile_status_expired(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profile_dir = tmp_path / "profiles" / "old"
            profile_dir.mkdir(parents=True)
            cookies = self._make_fresh_cookies(days_offset=-5)
            (profile_dir / "storage_state.json").write_text(json.dumps(cookies))

            from gemiterm.auth_manager import get_profile_status

            status = get_profile_status("old")
            assert status["exists"] is True
            assert status["is_active"] is False
            assert status["needs_refresh"] is True

    def test_get_profile_status_missing(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            from gemiterm.auth_manager import get_profile_status

            status = get_profile_status("missing")
            assert status["exists"] is False

    def test_delete_profile(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            work_dir = profiles_dir / "work"
            work_dir.mkdir(parents=True)
            (work_dir / "storage_state.json").write_text("{}")
            (profiles_dir / ".default").write_text("default")

            from gemiterm.auth_manager import delete_profile

            delete_profile("work")
            assert not work_dir.exists()

    def test_delete_default_profile_reassigns(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            work_dir = profiles_dir / "work"
            personal_dir = profiles_dir / "personal"
            work_dir.mkdir(parents=True)
            personal_dir.mkdir(parents=True)
            (profiles_dir / ".default").write_text("work")

            from gemiterm.auth_manager import delete_profile

            delete_profile("work")
            assert get_default_profile_name() == "personal"

    def test_rename_profile(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            old_dir = profiles_dir / "old_name"
            old_dir.mkdir(parents=True)
            (old_dir / "storage_state.json").write_text("{}")

            from gemiterm.auth_manager import rename_profile

            rename_profile("old_name", "new_name")
            assert not old_dir.exists()
            assert (profiles_dir / "new_name").exists()

    def test_list_profile_statuses(self, tmp_path):
        with patch("gemiterm.config._get_config_dir", return_value=tmp_path):
            profiles_dir = tmp_path / "profiles"
            work_dir = profiles_dir / "work"
            work_dir.mkdir(parents=True)
            cookies = self._make_fresh_cookies(days_offset=30)
            (work_dir / "storage_state.json").write_text(json.dumps(cookies))
            (profiles_dir / ".default").write_text("work")

            from gemiterm.auth_manager import list_profile_statuses

            statuses = list_profile_statuses()
            assert len(statuses) == 1
            assert statuses[0]["name"] == "work"
            assert statuses[0]["is_default"] is True
            assert statuses[0]["is_active"] is True


class TestProfileCommand:
    def test_profile_list_empty(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["profile", "list"])
            assert result.exit_code == 0
            assert "No profiles found" in result.output

    def test_profile_list_with_profiles(self):
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
            result = runner.invoke(cli, ["profile", "list"])
            assert result.exit_code == 0
            assert "work" in result.output
            assert "Active" in result.output


class TestAuthCommandMultiProfile:
    def test_auth_first_run_creates_default(self):
        cookies_list = [{"name": "cookie1"}, {"name": "cookie2"}]
        with (
            patch("gemiterm.cli.list_profiles", return_value=[]),
            patch("asyncio.run", return_value=cookies_list),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["auth"])
            assert result.exit_code == 0
            assert "No profiles found" in result.output
            assert "Created 'default' profile" in result.output

    def test_auth_shows_menu_when_profiles_exist(self):
        statuses = [
            {
                "name": "work",
                "is_active": True,
                "exists": True,
                "expires_at": None,
                "is_default": True,
            },
        ]
        with (
            patch("gemiterm.cli.list_profiles", return_value=["work"]),
            patch("gemiterm.cli.list_profile_statuses", return_value=statuses),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["auth"], input="X\n")
            assert result.exit_code == 0
            assert "Select an action" in result.output
            assert "work" in result.output


class TestListAllProfiles:
    def test_list_all_profiles_no_active(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["list", "--all-profiles"])
            assert result.exit_code == 2
            assert "No active profiles found" in result.output

    def test_list_all_profiles_with_chats(self):
        statuses = [
            {
                "name": "work",
                "is_active": True,
                "exists": True,
                "expires_at": None,
                "is_default": True,
            },
        ]
        mock_client = MagicMock()
        mock_client.list_chats.return_value = [
            {"id": "c1", "title": "Chat 1", "is_pinned": False, "timestamp": 1700000000},
        ]
        with (
            patch("gemiterm.cli.list_profile_statuses", return_value=statuses),
            patch("gemiterm.cli.load_cookies", return_value=("sid", "ts")),
            patch("gemiterm.cli.GeminiClient") as mock_client_class,
        ):
            mock_client_class.return_value = mock_client
            runner = CliRunner()
            result = runner.invoke(cli, ["list", "--all-profiles"])
            assert result.exit_code == 0
            assert "Chat 1" in result.output
            assert "work" in result.output


class TestStatusMultiProfile:
    def test_status_no_profiles(self):
        with patch("gemiterm.cli.list_profile_statuses", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 2
            assert "No profiles found" in result.output

    def test_status_with_profiles(self):
        statuses = [
            {
                "name": "work",
                "is_active": True,
                "exists": True,
                "expires_at": None,
                "is_default": True,
            },
        ]
        with patch("gemiterm.cli.list_profile_statuses", return_value=statuses):
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 0
            assert "work" in result.output
