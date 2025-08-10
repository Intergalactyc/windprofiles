from collections.abc import Sequence

from pathlib import Path
from urllib.request import urlopen
from platformdirs import user_cache_dir
import json
import os

DATA_DIR = Path(user_cache_dir("windprofiles", appauthor=False, ensure_exists=True))
os.makedirs(DATA_DIR, exist_ok=True)
REQUEST_CACHE_FILE = DATA_DIR / "request_cache.json"


class APIException(Exception):
    pass


def _read_request_cache():
    if not REQUEST_CACHE_FILE.exists() or REQUEST_CACHE_FILE.stat().st_size == 0:
        return {}
    with REQUEST_CACHE_FILE.open() as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _check_request_cache(request):
    cache = _read_request_cache()
    return cache.get(request)


def _add_to_request_cache(cache_key, value):
    current = _read_request_cache()
    current.update({cache_key: value})
    with open(REQUEST_CACHE_FILE, "w") as f:
        json.dump(current, f)


def urlopen_with_cache(request: str, parameters: Sequence = None):
    cache_key = ";".join([str(p) for p in parameters]) if parameters else request
    if (cached := _check_request_cache(cache_key)) is not None:
        return cached
    response = urlopen(request)
    results = json.load(response)
    _add_to_request_cache(cache_key, results)
    return results
