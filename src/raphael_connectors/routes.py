"""Connectors API — /v1/connectors/* (compat /v1/adapters via gateway)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from raphael_connectors.adapters.kicad.adapter import KiCadAdapter
from raphael_connectors.adapters.mappers import AltiumMapperAdapter, SolidWorksMapperAdapter
from raphael_connectors.sdk.base import AdapterContext
from raphael_connectors.store import ConnectorsStore, StoreEventSink

router = APIRouter(tags=["connectors"])
_store = ConnectorsStore()
_kicad_sink = StoreEventSink(_store)
_kicad_adapter = KiCadAdapter(_kicad_sink)
_altium_mapper = AltiumMapperAdapter()
_solidworks_mapper = SolidWorksMapperAdapter()


@router.get("")
def list_connectors() -> dict:
    return _store.list_status()


@router.post("/{tool}/connect")
def connect(tool: str) -> dict:
    return _store.connect(tool)


@router.post("/webhooks/{tool}")
async def webhook(tool: str, request: Request) -> dict[str, str]:
    body = await request.json()
    _store.ingest_event({"tool": tool, **body})
    return {"status": "accepted", "tool": tool}


@router.post("/ingest/kicad")
async def ingest_kicad(request: Request) -> dict[str, Any]:
    body = await request.json()
    parsed = _kicad_adapter.ingest(body, project_id=str(body.get("module_id") or body.get("project_id") or "default"))
    _store.ingest_event({"tool": "kicad", "parsed": parsed, **body})
    return {"status": "accepted", "tool": "kicad", "parsed": parsed, "events_emitted": len(_kicad_sink.events)}


@router.post("/ingest/altium")
async def ingest_altium(request: Request) -> dict[str, Any]:
    body = await request.json()
    ctx = AdapterContext(
        tenant_id=str(body.get("tenant_id", "local")),
        project_id=str(body.get("module_id") or body.get("project_id") or "default"),
        user_id=str(body.get("user_id", "connector")),
    )
    try:
        events = _altium_mapper.map_payload(body, ctx)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    _store.ingest_event({"tool": "altium", "event_count": len(events), **body})
    return {"status": "accepted", "tool": "altium", "events": len(events)}


@router.post("/ingest/solidworks")
async def ingest_solidworks(request: Request) -> dict[str, Any]:
    body = await request.json()
    ctx = AdapterContext(
        tenant_id=str(body.get("tenant_id", "local")),
        project_id=str(body.get("module_id") or body.get("project_id") or "default"),
        user_id=str(body.get("user_id", "connector")),
    )
    try:
        events = _solidworks_mapper.map_payload(body, ctx)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    _store.ingest_event({"tool": "solidworks", "event_count": len(events), **body})
    return {"status": "accepted", "tool": "solidworks", "events": len(events)}
