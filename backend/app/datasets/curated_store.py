from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import SNAPSHOT_NAME_PATTERN, SUPPORTED_SOURCES


class CuratedStore:
    def __init__(self, root: Path):
        self.root = root

    def load_rows(self, source: str, snapshot: str) -> list[dict[str, Any]]:
        if source not in SUPPORTED_SOURCES:
            raise ValueError(f"Unsupported curated source: {source}")
        if not SNAPSHOT_NAME_PATTERN.fullmatch(snapshot):
            raise ValueError(f"Invalid snapshot name: {snapshot}")

        base_dir = (self.root / source).resolve()
        path = (base_dir / f"{snapshot}.json").resolve()
        if path != base_dir and base_dir not in path.parents:
            raise ValueError(f"Invalid snapshot path: {snapshot}")

        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
