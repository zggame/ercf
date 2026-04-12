from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import SOURCE_FREDDIE_MAC
from .curated_store import CuratedStore


def load_freddie_mac_rows(root: Path, snapshot: str) -> list[dict[str, Any]]:
    return CuratedStore(root).load_rows(SOURCE_FREDDIE_MAC, snapshot)
