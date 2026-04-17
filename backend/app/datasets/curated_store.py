from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from .canonical import SNAPSHOT_NAME_PATTERN, SUPPORTED_SOURCES
from .duckdb_store import DuckDBStore


class CuratedStore:
    def __init__(self, root: Path):
        self.root = root
        self.db = DuckDBStore()

    def get_parquet_path(self, source: str, snapshot: str) -> Path:
        if source not in SUPPORTED_SOURCES:
            raise ValueError(f"Unsupported curated source: {source}")
        if not SNAPSHOT_NAME_PATTERN.fullmatch(snapshot):
            raise ValueError(f"Invalid snapshot name: {snapshot}")

        base_dir = (self.root / source).resolve()
        parquet_path = (base_dir / f"{snapshot}.parquet").resolve()
        if parquet_path != base_dir and base_dir not in parquet_path.parents:
            raise ValueError(f"Invalid snapshot path: {snapshot}")

        if not parquet_path.exists():
            json_path = base_dir / f"{snapshot}.json"
            if json_path.exists():
                return json_path
        return parquet_path

    def load_rows(self, source: str, snapshot: str) -> list[dict[str, Any]]:
        path = self.get_parquet_path(source, snapshot)
        if path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)

        with self.db.connect() as conn:
            df = conn.execute(
                f"SELECT * FROM read_parquet('{path.as_posix()}')"
            ).fetch_df()
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")
