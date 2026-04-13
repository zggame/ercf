from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import SOURCE_FANNIE_MAE
from .curated_store import CuratedStore


def load_fannie_mae_rows(root: Path, snapshot: str) -> list[dict[str, Any]]:
    return CuratedStore(root).load_rows(SOURCE_FANNIE_MAE, snapshot)
