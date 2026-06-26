from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FreeCADDaemon:
    watch_path: Path
    running: bool = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def scan(self) -> list[dict]:
        events: list[dict] = []
        for file in self.watch_path.glob("*.FCStd"):
            events.append(
                {
                    "event_type": "cad.document_modified",
                    "payload": {"path": str(file), "name": file.name},
                }
            )
        return events

    def ping(self) -> dict[str, str]:
        return {"status": "ok", "daemon": "freecad"}
