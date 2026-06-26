"""GitLab webhook adapter (Phase 1b extension)."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_connectors.adapters.common.webhook_base import WebhookAdapterBase


class GitLabWebhookAdapter(WebhookAdapterBase):
    tool_identifier = "gitlab"
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
        event_name = headers.get("X-Gitlab-Event", headers.get("x-gitlab-event", ""))
        project = payload.get("project", {})
        repo_name = project.get("path_with_namespace", project_id)
        events: list[dict[str, Any]] = []

        if event_name == "Push Hook":
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            events.append(
                build_event(
                    event_type="software.commit_pushed",
                    payload={
                        "repository": repo_name,
                        "branch": branch,
                        "commit_sha": payload.get("after", ""),
                        "author": payload.get("user_name", user_id),
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=repo_name,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                )
            )
        elif event_name == "Merge Request Hook":
            attrs = payload.get("object_attributes", {})
            action = attrs.get("action", "")
            event_type = "software.pull_request_opened"
            if action == "merge":
                event_type = "software.pull_request_merged"
            elif action == "close":
                event_type = "software.pull_request_closed"
            events.append(
                build_event(
                    event_type=event_type,
                    payload={
                        "repository": repo_name,
                        "branch": attrs.get("target_branch", "main"),
                        "pull_request_number": attrs.get("iid"),
                        "title": attrs.get("title", ""),
                        "action": action,
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=repo_name,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                )
            )
        return events
