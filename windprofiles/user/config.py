from pathlib import Path
import json
from platformdirs import user_config_dir

_key_options = {"gmaps"}

CONFIG_DIR = Path(user_config_dir("windprofiles", appauthor=False, ensure_exists=True))
CONFIG_FILE = CONFIG_DIR / "config.json"


def _validate_type(which: str):
    if which not in _key_options:
        raise ValueError(f"{which} is not a valid api key type")


def _read_keyring():
    if not CONFIG_FILE.exists() or CONFIG_FILE.stat().st_size == 0:
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_api_key(which: str) -> str:
    _validate_type(which)
    result = _read_keyring()
    match which:
        case "gmaps":
            return result.get("gmaps_api_key")


def set_api_key(which: str, value: str):
    _validate_type(which)
    current = _read_keyring()
    match which:
        case "gmaps":
            current.update({"gmaps_api_key": value})
    with open(CONFIG_FILE, "w") as f:
        json.dump(current, f)
