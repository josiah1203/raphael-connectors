from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event


class CadenceAdapter:
    name = "cadence"

    def map_payload(self, payload: dict) -> list[dict]:
        return [{"event_type": "electrical.design_rule_checked", "payload": payload, "tool": {"identifier": self.name}}]

    def map_schematic_change(
        self, payload: dict[str, Any], *, session_id: str, user_id: str, project_id: str
    ) -> list[dict]:
        return [
            build_event(
                event_type="electrical.net_changed",
                payload=payload,
                session_id=session_id,
                user_id=user_id,
                project_id=project_id,
                tool_identifier=self.name,
            )
        ]
