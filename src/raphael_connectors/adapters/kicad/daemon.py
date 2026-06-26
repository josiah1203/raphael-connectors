from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class KiCadDaemon:
    watch_path: Path
    running: bool = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def health(self) -> dict[str, str]:
        return {"status": "ok", "watch_path": str(self.watch_path)}

    def status(self) -> dict[str, str | bool]:
        return {"adapter": "kicad", "running": self.running, "watch_path": str(self.watch_path)}
