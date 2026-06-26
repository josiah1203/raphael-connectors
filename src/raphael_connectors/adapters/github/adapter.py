"""GitHub webhook adapter (Phase 1b)."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_connectors.adapters.common.webhook_base import WebhookAdapterBase


class GitHubWebhookAdapter(WebhookAdapterBase):
    tool_identifier = "github"
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
        event_name = headers.get("X-GitHub-Event", headers.get("x-github-event", ""))
        repo = payload.get("repository", {})
        repo_name = repo.get("full_name", project_id)
        events: list[dict[str, Any]] = []

        if event_name == "push":
            head = payload.get("after", "")
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            author = payload.get("pusher", {}).get("name", user_id)
            events.append(
                build_event(
                    event_type="software.commit_pushed",
                    payload={
                        "repository": repo_name,
                        "branch": branch,
                        "commit_sha": head,
                        "author": author,
                        "ref": ref,
                        "commits_count": len(payload.get("commits", [])),
                    },
                    session_id=session_id,
                    user_id=user_id,
                    project_id=repo_name,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                    use_deterministic_id=True,
                    object_id=f"{repo_name}:{head}",
                    timestamp_utc="1970-01-01T00:00:00Z",
                )
            )
        elif event_name == "pull_request":
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})
            base = pr.get("base", {}).get("ref", "main")
            pr_payload = {
                "repository": repo_name,
                "branch": base,
                "pull_request_number": pr.get("number"),
                "title": pr.get("title", ""),
                "action": action,
            }
            type_map = {
                "opened": "software.pull_request_opened",
                "closed": "software.pull_request_closed",
            }
            if action == "closed" and pr.get("merged"):
                event_type = "software.pull_request_merged"
            else:
                event_type = type_map.get(action, "software.pull_request_opened")
            events.append(
                build_event(
                    event_type=event_type,
                    payload=pr_payload,
                    session_id=session_id,
                    user_id=user_id,
                    project_id=repo_name,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                )
            )
        return events
