from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event


class RhinoAdapter:
    name = "rhino"

    def map_payload(self, payload: dict) -> list[dict]:
        return [{"event_type": "geometry.surface_modified", "payload": payload, "tool": {"identifier": self.name}}]

    def map_geometry_change(
        self, payload: dict[str, Any], *, session_id: str, user_id: str, project_id: str
    ) -> list[dict]:
        event = build_event(
            event_type="geometry.feature_modified",
            payload=payload,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            tool_identifier=self.name,
        )
        event["event_type"] = "geometry.rhino_object_modified"
        return [event]
