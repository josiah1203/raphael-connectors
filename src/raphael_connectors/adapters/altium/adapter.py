"""Altium electrical fixture adapter backend."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_artifacts.calliope_schema.validator import validate_addon_snapshot


class AltiumAdapter:
    """Map electrical fixture JSON to events."""

    tool_identifier = "altium"
    application = "BoardFlow"
    adapter_version = "0.1.0"

    def map_payload(
        self,
        payload: dict[str, Any],
        *,
        session_id: str,
        user_id: str,
        project_id: str | None = None,
        tenant_id: str = "local",
    ) -> list[dict[str, Any]]:
        errors = validate_addon_snapshot("altium", payload)
        if errors:
            raise ValueError("; ".join(errors))
        document_id = payload.get("document_id", payload.get("board_id", "altium-board"))
        proj = project_id or payload.get("project_id", document_id)
        events: list[dict[str, Any]] = []

        for change in payload.get("changes", []):
            event_type = change.get("type", "electrical.footprint_modified")
            ev_payload = {
                "document_id": document_id,
                "document_name": payload.get("document_name", ""),
                **{k: v for k, v in change.items() if k != "type"},
            }
            events.append(
                build_event(
                    event_type=event_type,
                    payload=ev_payload,
                    session_id=session_id,
                    user_id=user_id,
                    project_id=proj,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                    application=self.application,
                )
            )

        if not events and payload.get("components"):
            for comp in payload["components"]:
                events.append(
                    build_event(
                        event_type="electrical.footprint_added",
                        payload={
                            "document_id": document_id,
                            "component_id": comp.get("id", comp.get("designator", "unknown")),
                            "designator": comp.get("designator", ""),
                            "footprint": comp.get("footprint", ""),
                        },
                        session_id=session_id,
                        user_id=user_id,
                        project_id=proj,
                        tool_identifier=self.tool_identifier,
                        tenant_id=tenant_id,
                    )
                )
        return events

    def map_netlist(self, netlist: dict[str, Any], *, session_id: str, user_id: str, project_id: str) -> list[dict[str, Any]]:
        """Enhanced: map Altium netlist export."""
        events: list[dict[str, Any]] = []
        for net in netlist.get("nets", []):
            events.append(
                build_event(
                    event_type="electrical.net_changed",
                    payload={"net_name": net.get("name"), "nodes": net.get("nodes", [])},
                    session_id=session_id,
                    user_id=user_id,
                    project_id=project_id,
                    tool_identifier=self.tool_identifier,
                    tenant_id="local",
                )
            )
        return events

    def daemon_status(self) -> dict[str, Any]:
        return {"adapter": "altium", "version": self.adapter_version, "domain": self.application}
