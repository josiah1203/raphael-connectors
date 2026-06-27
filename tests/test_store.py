"""Connectors store domain tests."""

from pathlib import Path

import pytest

from raphael_connectors.sdk.base import AdapterEvent
from raphael_connectors.store import ConnectorsStore, StoreEventSink


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ConnectorsStore:
    monkeypatch.delenv("RAPHAEL_DATABASE_URL", raising=False)
    return ConnectorsStore(db_path=tmp_path / "connectors.db")


def test_connect_persists_connection(store: ConnectorsStore) -> None:
    result = store.connect("KiCad")
    assert result["status"] == "connected"
    connections = store.list_connections()
    assert any(c["tool"] == "KiCad" for c in connections)


def test_ingest_event_persists_and_appears_in_status(store: ConnectorsStore) -> None:
    store.ingest_event({"tool": "github", "project_id": "repo-1", "event": "push"})
    events = store.list_events()
    assert len(events) >= 1
    status = store.list_status()
    assert any(c["tool"] == "github" for c in status["connected"])


def test_store_event_sink_publishes_adapter_events(store: ConnectorsStore) -> None:
    sink = StoreEventSink(store)
    event = AdapterEvent(
        event_type="electrical.board_ingested",
        payload={"valid": True},
        project_id="board-1",
        timestamp_utc="2026-06-27T12:00:00+00:00",
        adapter="kicad",
    )
    sink.publish(event)
    assert len(sink.events) == 1
    persisted = store.list_events()
    assert any(e.get("tool") == "kicad" for e in persisted)


def test_webhook_ingest_survives_new_store_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAPHAEL_DATABASE_URL", raising=False)
    db = tmp_path / "connectors-persist.db"
    store1 = ConnectorsStore(db_path=db)
    store1.ingest_event({"tool": "altium", "event_count": 2})
    store2 = ConnectorsStore(db_path=db)
    assert any(e.get("tool") == "altium" for e in store2.list_events())
