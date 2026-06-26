"""Jira webhook adapter (Phase 2b)."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_connectors.adapters.common.webhook_base import WebhookAdapterBase


class JiraWebhookAdapter(WebhookAdapterBase):
    tool_identifier = "jira"
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
        event_name = payload.get("webhookEvent", "")
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})
        key = issue.get("key", project_id)
        proj_key = fields.get("project", {}).get("key", project_id)
        status = fields.get("status", {}).get("name", "")
        issue_type = fields.get("issuetype", {}).get("name", "")

        type_map = {
            "jira:issue_created": "project.issue_created",
            "jira:issue_updated": "project.issue_updated",
        }
        event_type = type_map.get(event_name, "project.issue_updated")
        if "transition" in event_name.lower() or payload.get("changelog", {}).get("items"):
            for item in payload.get("changelog", {}).get("items", []):
                if item.get("field") == "status":
                    event_type = "project.issue_transitioned"
                    status = item.get("toString", status)

        return [
            build_event(
                event_type=event_type,
                payload={
                    "issue_key": key,
                    "issue_type": issue_type,
                    "status": status,
                    "summary": fields.get("summary", ""),
                    "webhook_event": event_name,
                },
                session_id=session_id,
                user_id=user_id,
                project_id=proj_key,
                tool_identifier=self.tool_identifier,
                tenant_id=tenant_id,
                use_deterministic_id=True,
                object_id=f"{key}:{event_name}:{status}",
            )
        ]
