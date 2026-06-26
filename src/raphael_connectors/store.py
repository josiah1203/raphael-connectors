"""Connectors store — migrated from sonoma_api adapters."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConnectorsStore:
    def __init__(self, db_path: Path | None = None) -> None:
        path = db_path or Path(os.environ.get("RAPHAEL_CONNECTORS_DB", "/tmp/raphael-connectors.db"))
        self.db_path = path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS connections (tool TEXT PRIMARY KEY, connected_at TEXT NOT NULL)"
            )

    def connect(self, tool: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO connections (tool, connected_at) VALUES (?, ?)", (tool, now))
        return {"tool": tool, "status": "connected", "connected_at": now}

    def list_status(self) -> dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute("SELECT tool, connected_at FROM connections").fetchall()
        connected = [
            {"tool": r[0], "status": "idle", "last_event": r[1], "repo_count": 0, "event_count": 0}
            for r in rows
        ]
        available = [
            {"tool": "KiCad", "action": "Install connector", "connected": False},
            {"tool": "SolidWorks", "action": "Install connector", "connected": False},
            {"tool": "GitHub", "action": "Connect account", "connected": False},
        ]
        for c in connected:
            available = [a for a in available if a["tool"] != c["tool"]]
        return {"connected": connected or [{"tool": "KiCad", "status": "idle", "last_event": None, "repo_count": 0, "event_count": 0}], "available": available}
