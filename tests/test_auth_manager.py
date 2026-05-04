import json
from datetime import datetime
from unittest.mock import patch

from gemiterm.auth_manager import get_profile_status


class TestGetProfileStatus:
    def test_expires_at_date_format_cross_platform(self, tmp_path):
        expires_timestamp = 1735689600

        with patch("gemiterm.auth_manager.get_profile_path") as mock_path:
            profile_file = tmp_path / "test_profile.json"
            mock_path.return_value = profile_file

            cookie_data = {
                "cookies": [
                    {
                        "name": "__Secure-1PSIDTS",
                        "value": "somevalue",
                        "expires": expires_timestamp,
                    }
                ]
            }
            with open(profile_file, "w") as f:
                json.dump(cookie_data, f)

            status = get_profile_status("test_profile")

            assert status["exists"] is True
            assert status["expires_at"] is not None

            dt = datetime.fromtimestamp(expires_timestamp)
            expected_month = str(dt.month)
            expected_day = str(dt.day)
            expected_hour = dt.strftime("%I").lstrip("0")

            assert f"{expected_month}/" in status["expires_at"]
            assert f"/{expected_day}/" in status["expires_at"]
            assert f" {expected_hour}:" in status["expires_at"]
            assert ")" in status["expires_at"]