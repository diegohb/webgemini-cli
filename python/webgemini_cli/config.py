import os
from pathlib import Path

CONFIG_DIR_DEFAULT = ".config/webgemini-cli"
STORAGE_STATE_FILE = "storage_state.json"


def _get_config_dir() -> Path:
    env_override = os.environ.get("WEBGEMINI_CONFIG_DIR")
    if env_override:
        return Path(env_override)
    return Path.home() / CONFIG_DIR_DEFAULT


def get_storage_state_path() -> Path:
    return _get_config_dir() / STORAGE_STATE_FILE


def ensure_config_dir() -> Path:
    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
