"""KiCad directory watcher using watchdog (macOS FSEvents)."""

from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path
from typing import Any, Callable

from raphael_connectors.adapters.kicad.parser import diff_kicad_snapshots, parse_kicad_pcb

logger = logging.getLogger(__name__)


class KiCadWatcher:
    def __init__(
        self,
        watch_path: Path,
        ingest_url: str = "http://127.0.0.1:8742/v1/ingest/kicad",
        on_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.watch_path = watch_path
        self.ingest_url = ingest_url
        self.on_change = on_change
        self._shadow: dict[str, dict[str, Any]] = {}

    def _handle_file(self, path: Path) -> None:
        if path.suffix != ".kicad_pcb":
            return
        try:
            current = parse_kicad_pcb(str(path))
        except ValueError as e:
            if "partial_write" in str(e):
                return
            logger.warning("KiCad parse failed for %s: %s", path, e)
            return
        except Exception as e:
            logger.warning("KiCad parse error %s: %s", path, e)
            return

        key = str(path)
        previous = self._shadow.get(key)
        changes = diff_kicad_snapshots(previous, current)
        self._shadow[key] = current

        if not changes:
            return

        payload = {
            "document_id": key,
            "document_name": path.name,
            "project_id": str(self.watch_path),
            "changes": changes,
            "snapshot": current,
        }
        if self.on_change:
            self.on_change(payload)
        else:
            self._post(payload)

    def _post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.ingest_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-Calliope-Application": "BoardFlow",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                logger.info("KiCad ingest: %s", resp.read().decode())
        except Exception as e:
            logger.error("KiCad ingest failed: %s", e)

    def scan_once(self) -> int:
        count = 0
        for pcb in self.watch_path.rglob("*.kicad_pcb"):
            self._handle_file(pcb)
            count += 1
        return count

    def run_watchdog(self) -> None:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        watcher = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):  # noqa: N802
                if not event.is_directory:
                    watcher._handle_file(Path(event.src_path))

            def on_created(self, event):  # noqa: N802
                if not event.is_directory:
                    watcher._handle_file(Path(event.src_path))

        observer = Observer()
        observer.schedule(Handler(), str(self.watch_path), recursive=True)
        observer.start()
        logger.info("KiCad watcher on %s", self.watch_path)
        try:
            while observer.is_alive():
                observer.join(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
