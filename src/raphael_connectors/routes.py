"""Connectors API — /v1/connectors/* (compat /v1/adapters via gateway)."""

from __future__ import annotations

from fastapi import APIRouter

from raphael_connectors.store import ConnectorsStore

router = APIRouter(tags=["connectors"])
_store = ConnectorsStore()


@router.get("")
def list_connectors() -> dict:
    return _store.list_status()


@router.post("/{tool}/connect")
def connect(tool: str) -> dict:
    return _store.connect(tool)
