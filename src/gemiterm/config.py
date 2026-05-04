import os
from pathlib import Path

CONFIG_DIR_DEFAULT = ".config/gemiterm"
STORAGE_STATE_FILE = "storage_state.json"
PROFILES_DIR = "profiles"
DEFAULT_PROFILE_MARKER = ".default"


def _get_config_dir() -> Path:
    env_override = os.environ.get("GEMITERM_CONFIG_DIR")
    if env_override:
        return Path(env_override)
    return Path.home() / CONFIG_DIR_DEFAULT


def get_profiles_dir() -> Path:
    return _get_config_dir() / PROFILES_DIR


def get_profile_path(name: str) -> Path:
    return get_profiles_dir() / name / STORAGE_STATE_FILE


def get_default_profile_name() -> str:
    marker = get_profiles_dir() / DEFAULT_PROFILE_MARKER
    if marker.exists():
        return marker.read_text().strip()
    return "default"


def set_default_profile_name(name: str) -> None:
    marker = get_profiles_dir() / DEFAULT_PROFILE_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(name)


def list_profiles() -> list[str]:
    profiles_path = get_profiles_dir()
    if not profiles_path.exists():
        return []
    return [
        d.name for d in profiles_path.iterdir()
        if d.is_dir() and d.name != DEFAULT_PROFILE_MARKER
    ]


def get_storage_state_path() -> Path:
    return get_profile_path(get_default_profile_name())


def ensure_config_dir() -> Path:
    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    get_profiles_dir().mkdir(parents=True, exist_ok=True)
    return config_dir