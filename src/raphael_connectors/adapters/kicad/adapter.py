"""KiCad connector adapter — concrete BaseAdapter using parser."""

from __future__ import annotations

from typing import Any

from raphael_connectors.adapters.kicad.parser import parse_kicad_pcb
from raphael_connectors.sdk.base import AdapterMetadata, BaseAdapter, EventSink


class KiCadAdapter(BaseAdapter):
    metadata = AdapterMetadata(name="kicad", version="0.1.0", domain="electrical")

    def __init__(self, sink: EventSink) -> None:
        super().__init__(sink)
        self._running = False

    def parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        content = payload.get("content") or payload.get("board") or ""
        file_path = payload.get("file_path")
        if content:
            import os
            import tempfile

            with tempfile.NamedTemporaryFile("w", suffix=".kicad_pcb", delete=False, encoding="utf-8") as handle:
                handle.write(content if content.strip().endswith(")") else f"(kicad_pcb (version 20240108) {content})")
                temp_path = handle.name
            try:
                parsed = parse_kicad_pcb(temp_path)
            finally:
                os.unlink(temp_path)
            return {"format": "kicad", "valid": True, **parsed}
        if file_path:
            parsed = parse_kicad_pcb(str(file_path))
            return {"format": "kicad", "valid": True, **parsed}
        return {"format": "kicad", "valid": False, "error": "missing content or file_path"}

    def ingest(self, payload: dict[str, Any], *, project_id: str) -> dict[str, Any]:
        parsed = self.parse_payload(payload)
        self.emit(
            "electrical.board_ingested",
            {"parsed": parsed, "module_id": payload.get("module_id"), "file_path": payload.get("file_path")},
            project_id=project_id,
        )
        return parsed

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running
