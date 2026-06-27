"""Connectors store — Postgres dual-path with SQLite test fallback."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raphael_connectors.sdk.base import AdapterEvent
from raphael_connectors.status import adapter_status_from_events


class StoreEventSink:
    """Persist adapter events via ConnectorsStore (replaces InMemoryEventSink in routes)."""

    def __init__(self, store: ConnectorsStore) -> None:
        self._store = store
        self.events: list[AdapterEvent] = []

    def publish(self, event: AdapterEvent) -> None:
        self.events.append(event)
        self._store.ingest_adapter_event(event)


class ConnectorsStore:
    def __init__(self, db_path: Path | None = None) -> None:
        from raphael_contracts import db as rdb

        self._postgres = rdb.is_postgres()
        if self._postgres:
            rdb.ensure_migrations()
            self.db_path = Path("postgres")
        else:
            path = db_path or Path(os.environ.get("RAPHAEL_CONNECTORS_DB", "/tmp/raphael-connectors.db"))
            self.db_path = path
            self._init_sqlite()

    def _connect_sqlite(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_sqlite(self) -> None:
        with self._connect_sqlite() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS connections (tool TEXT PRIMARY KEY, connected_at TEXT NOT NULL)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS connector_events (
                    id TEXT PRIMARY KEY,
                    tool TEXT NOT NULL,
                    project_id TEXT,
                    event_type TEXT,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        if self._postgres:
            from raphael_contracts.db import pg_execute

            pg_execute(sql, params)
            return
        with self._connect_sqlite() as conn:
            conn.execute(sql, params)
            conn.commit()

    def _fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
        if self._postgres:
            from raphael_contracts.db import pg_fetchall

            return pg_fetchall(sql, params)
        with self._connect_sqlite() as conn:
            return conn.execute(sql, params).fetchall()

    def _connections_table(self) -> str:
        return "connector_connections" if self._postgres else "connections"

    def connect(self, tool: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        table = self._connections_table()
        if self._postgres:
            from raphael_contracts.db import adapt_insert_or_replace

            sql = adapt_insert_or_replace(
                f"INSERT OR REPLACE INTO {table} (tool, connected_at) VALUES (?, ?)",
                "tool",
                "connected_at = EXCLUDED.connected_at",
            )
            self._execute(sql, (tool, now))
        else:
            self._execute(
                f"INSERT OR REPLACE INTO {table} (tool, connected_at) VALUES (?, ?)",
                (tool, now),
            )
        return {"tool": tool, "status": "connected", "connected_at": now}

    def list_connections(self) -> list[dict[str, Any]]:
        table = self._connections_table()
        rows = self._fetchall(f"SELECT tool, connected_at FROM {table}")
        return [
            {
                "tool": row["tool"] if isinstance(row, dict) else row[0],
                "connected_at": str(row["connected_at"] if isinstance(row, dict) else row[1]),
            }
            for row in rows
        ]

    def ingest_event(self, event: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        event_id = f"evt_{secrets.token_hex(8)}"
        tool = str(event.get("tool") or "unknown")
        project_id = event.get("project_id") or event.get("module_id")
        payload = json.dumps(event)
        if self._postgres:
            self._execute(
                """
                INSERT INTO connector_events (id, tool, project_id, event_type, payload, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (event_id, tool, project_id, event.get("event_type"), payload, now),
            )
        else:
            self._execute(
                """
                INSERT INTO connector_events (id, tool, project_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, tool, project_id, event.get("event_type"), payload, now),
            )

    def ingest_adapter_event(self, event: AdapterEvent) -> None:
        self.ingest_event(
            {
                "tool": event.adapter,
                "project_id": event.project_id,
                "event_type": event.event_type,
                "timestamp_utc": event.timestamp_utc,
                "payload": event.payload,
                "source": {"tool": event.adapter, "adapter": event.adapter},
            }
        )

    def list_events(self, limit: int = 500) -> list[dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT tool, project_id, event_type, payload, created_at
            FROM connector_events
            ORDER BY created_at DESC
            LIMIT ?
            """ if not self._postgres else """
            SELECT tool, project_id, event_type, payload, created_at
            FROM connector_events
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        events: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, dict):
                payload_raw = row.get("payload")
                tool = row["tool"]
                project_id = row.get("project_id")
                event_type = row.get("event_type")
                created_at = str(row.get("created_at") or "")
            else:
                tool, project_id, event_type, payload_raw, created_at = row
                created_at = str(created_at)
            if isinstance(payload_raw, dict):
                parsed = payload_raw
            else:
                try:
                    parsed = json.loads(payload_raw or "{}")
                except json.JSONDecodeError:
                    parsed = {"tool": tool}
            if "tool" not in parsed:
                parsed = {**parsed, "tool": tool}
            if project_id and "project_id" not in parsed:
                parsed["project_id"] = project_id
            if event_type and "event_type" not in parsed:
                parsed["event_type"] = event_type
            if created_at and "timestamp_utc" not in parsed:
                parsed["timestamp_utc"] = created_at
            events.append(parsed)
        return events

    def list_status(self) -> dict[str, Any]:
        return adapter_status_from_events(self.list_events(), self.list_connections())
