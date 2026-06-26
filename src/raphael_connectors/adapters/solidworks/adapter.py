"""SolidWorks design_snapshot adapter backend."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_audit.schema.validator import validate_addon_snapshot


class SolidWorksAdapter:
    """Accept design_snapshot JSON (same schema as Fusion)."""

    tool_identifier = "solidworks"
    application = "FormFlow"
    adapter_version = "0.1.0"

    def map_snapshot(
        self,
        snapshot: dict[str, Any],
        *,
        session_id: str,
        user_id: str,
        project_id: str | None = None,
        tenant_id: str = "local",
    ) -> tuple[list[dict[str, Any]], list[str]]:
        errors = validate_addon_snapshot("solidworks", snapshot)
        if errors:
            return [], errors
        document_id = snapshot.get("document_id", "solidworks-doc")
        proj = project_id or snapshot.get("project_id", document_id)
        events: list[dict[str, Any]] = []
        for feature in snapshot.get("features", []):
            events.append(
                build_event(
                    event_type="geometry.feature_created",
                    payload={
                        "document_id": document_id,
                        "document_name": snapshot.get("document_name", ""),
                        "feature_id": feature.get("id", feature.get("name", "unknown")),
                        "feature_name": feature.get("name", ""),
                        "feature_type": feature.get("type", "unknown"),
                        "properties": feature.get("properties", {}),
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=proj,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                )
            )
        if not events:
            events.append(
                build_event(
                    event_type="geometry.design_snapshot_captured",
                    payload={
                        "document_id": document_id,
                        "document_name": snapshot.get("document_name", ""),
                        "feature_count": len(snapshot.get("features", [])),
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=proj,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                )
            )
        return events, []

    def map_assembly_tree(
        self,
        tree: dict[str, Any],
        *,
        session_id: str,
        user_id: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """Enhanced: map SolidWorks assembly hierarchy."""
        events: list[dict[str, Any]] = []
        for component in tree.get("components", []):
            events.append(
                build_event(
                    event_type="geometry.feature_created",
                    payload={
                        "document_id": tree.get("document_id", "assembly"),
                        "component_id": component.get("id"),
                        "component_name": component.get("name"),
                        "parent_id": component.get("parent_id"),
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=project_id,
                    tool_identifier=self.tool_identifier,
                )
            )
        return events

    def daemon_status(self) -> dict[str, Any]:
        return {"adapter": "solidworks", "version": self.adapter_version, "domain": self.application}
