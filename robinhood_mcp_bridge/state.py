from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.state_dir / name

    def read_json(self, name: str) -> dict[str, Any] | None:
        path = self.path(name)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"State file {path} must contain a JSON object")
        return data

    def write_json(self, name: str, data: dict[str, Any], mode: int = 0o600) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        target = self.path(name)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{name}.", dir=self.state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.chmod(tmp_name, mode)
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
