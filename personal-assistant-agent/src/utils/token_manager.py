import json
import os
from typing import Any, Optional


def _token_path() -> str:
    return os.environ.get("TOKEN_PATH", "token.json")


def save_token(token: object) -> None:
    with open(_token_path(), "w", encoding="utf-8") as f:
        json.dump(token, f)


def load_token() -> Optional[Any]:
    path = _token_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None
