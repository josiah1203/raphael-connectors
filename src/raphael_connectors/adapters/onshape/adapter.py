"""Onshape webhook mapper (Phase 1a)."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_connectors.adapters.common.webhook_base import WebhookAdapterBase


class OnshapeWebhookAdapter(WebhookAdapterBase):
    tool_identifier = "onshape"
    adapter_version = "0.1.0"

    def map_payload(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
        *,
        session_id: str,
        user_id: str,
        project_id: str,
        tenant_id: str = "local",
    ) -> list[dict[str, Any]]:
        message = payload.get("messageName", payload.get("event", ""))
        document_id = payload.get("documentId", payload.get("document_id", project_id))
        feature_id = payload.get("featureId", payload.get("elementId", "unknown"))

        event_type = "geometry.feature_modified"
        if "create" in message.lower():
            event_type = "geometry.feature_created"
        elif "delete" in message.lower():
            event_type = "geometry.feature_deleted"

        return [
            build_event(
                event_type=event_type,
                payload={
                    "document_id": str(document_id),
                    "feature_id": str(feature_id),
                    "feature_name": payload.get("name", ""),
                    "feature_type": payload.get("featureType", "onshape"),
                    "properties": payload.get("parameters", {}),
                    "onshape_message": message,
                },
                session_id=session_id,
                user_id=user_id,
                project_id=str(document_id),
                tool_identifier=self.tool_identifier,
                tenant_id=tenant_id,
            )
        ]

    def map_part_studio_event(
        self,
        payload: dict[str, Any],
        *,
        session_id: str,
        user_id: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """Enhanced: Part Studio microversion events."""
        return [
            build_event(
                event_type="geometry.feature_modified",
                payload={
                    "document_id": payload.get("documentId", project_id),
                    "microversion": payload.get("microversion"),
                    "part_studio_id": payload.get("partStudioId"),
                },
                session_id=session_id,
                user_id=user_id,
                project_id=project_id,
                tool_identifier=self.tool_identifier,
            )
        ]

    def daemon_status(self) -> dict[str, Any]:
        return {"adapter": "onshape", "version": self.adapter_version, "domain": "FormFlow"}
