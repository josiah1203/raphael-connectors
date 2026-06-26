"""Connectors API — /v1/connectors/* (compat /v1/adapters via gateway)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from raphael_connectors.store import ConnectorsStore

router = APIRouter(tags=["connectors"])
_store = ConnectorsStore()


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
