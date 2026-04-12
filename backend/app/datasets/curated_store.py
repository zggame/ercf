from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CuratedStore:
    def __init__(self, root: Path):
        self.root = root

    def load_rows(self, source: str, snapshot: str) -> list[dict[str, Any]]:
        path = self.root / source / f"{snapshot}.json"
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
