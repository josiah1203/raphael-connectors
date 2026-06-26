from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class AdapterContext:
    tenant_id: str
    project_id: str
    user_id: str


@dataclass(frozen=True)
class AdapterMetadata:
    name: str
    version: str
    domain: str


@dataclass(frozen=True)
class AdapterEvent:
    event_type: str
    payload: dict
    project_id: str
    timestamp_utc: str
    adapter: str


class EventSink(Protocol):
    def publish(self, event: AdapterEvent) -> None:
        ...


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: list[AdapterEvent] = []

    def publish(self, event: AdapterEvent) -> None:
        self.events.append(event)


class BaseAdapter:
    metadata: AdapterMetadata

    def __init__(self, sink: EventSink) -> None:
        self._sink = sink

    def emit(self, event_type: str, payload: dict, *, project_id: str) -> AdapterEvent:
        event = AdapterEvent(
            event_type=event_type,
            payload=payload,
            project_id=project_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            adapter=self.metadata.name,
        )
        self._sink.publish(event)
        return event

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class MapperAdapter(Protocol):
    name: str

    def validate(self, payload: dict) -> list[str]:
        ...

    def map_payload(self, payload: dict, context: AdapterContext) -> list[dict]:
        ...
