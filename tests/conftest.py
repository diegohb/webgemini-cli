import pytest


@pytest.fixture
def active_profiles():
    return [
        {
            "name": "default",
            "is_active": True,
            "exists": True,
            "expires_at": None,
            "needs_refresh": False,
            "is_default": True,
        },
    ]
