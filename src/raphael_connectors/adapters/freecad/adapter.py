from __future__ import annotations


class FreeCADAdapter:
    name = "freecad"

    def map_payload(self, payload: dict) -> list[dict]:
        return [{"event_type": "geometry.feature_modified", "payload": payload, "tool": {"identifier": self.name}}]
