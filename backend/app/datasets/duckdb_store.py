from __future__ import annotations

from pathlib import Path
from typing import Optional
import duckdb


class DuckDBStore:
    """Manages DuckDB database connections. Supports in-memory (default) or persistent file."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Returns a DuckDB connection. Caller is responsible for closing it."""
        return duckdb.connect(self.db_path)
