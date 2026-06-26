"""Connectors store — migrated from sonoma_api adapters."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raphael_connectors.status import adapter_status_from_events


class ConnectorsStore:
    def __init__(self, db_path: Path | None = None) -> None:
        path = db_path or Path(os.environ.get("RAPHAEL_CONNECTORS_DB", "/tmp/raphael-connectors.db"))
        self.db_path = path
        self._init_db()
        self._events: list[dict[str, Any]] = []

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS connections (tool TEXT PRIMARY KEY, connected_at TEXT NOT NULL)")

    def connect(self, tool: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO connections (tool, connected_at) VALUES (?, ?)", (tool, now))
        return {"tool": tool, "status": "connected", "connected_at": now}

    def list_connections(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT tool, connected_at FROM connections").fetchall()
        return [{"tool": r[0], "connected_at": r[1]} for r in rows]

    def ingest_event(self, event: dict[str, Any]) -> None:
        self._events.append(event)

    def list_status(self) -> dict[str, Any]:
        return adapter_status_from_events(self._events, self.list_connections())
