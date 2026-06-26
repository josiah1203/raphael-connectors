"""Base webhook adapter with HMAC verification and idempotency."""

from __future__ import annotations

import hashlib
import hmac
import json
from abc import ABC, abstractmethod
from typing import Any

from raphael_audit.core.event_builder import build_event
from raphael_audit.core.uuid7 import uuid7_str


class WebhookAdapterBase(ABC):
    tool_identifier: str = "unknown"
    adapter_version: str = "0.1.0"

    def verify_signature(self, body: bytes, signature: str, secret: str) -> bool:
        if not secret:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        for prefix in ("sha256=", "v0="):
            if signature.startswith(prefix):
                return hmac.compare_digest(signature[len(prefix):], expected)
        return hmac.compare_digest(signature, expected)

    def verify_github_signature(self, body: bytes, signature: str, secret: str) -> bool:
        if not signature.startswith("sha256=") or not secret:
            return False
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    @abstractmethod
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
        ...

    def process_webhook(
        self,
        body: bytes,
        headers: dict[str, str],
        secret: str,
        *,
        user_id: str = "webhook",
        tenant_id: str = "local",
        project_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        signature = headers.get("X-Hub-Signature-256") or headers.get("X-Hub-Signature") or headers.get(
            "x-hub-signature-256", ""
        )
        if secret:
            if not signature or not self.verify_github_signature(body, signature, secret):
                return [], "invalid_signature"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return [], "invalid_json"

        delivery_id = idempotency_key or headers.get("X-GitHub-Delivery") or headers.get(
            "X-Atlassian-Webhook-Identifier"
        )
        session_id = delivery_id or uuid7_str()
        proj = project_id or payload.get("repository", {}).get("full_name") or payload.get("project", {}).get(
            "key"
        ) or "default"

        events = self.map_payload(
            payload,
            headers,
            session_id=session_id,
            user_id=user_id,
            project_id=str(proj),
            tenant_id=tenant_id,
        )
        if delivery_id:
            for event in events:
                event.setdefault("payload", {})["webhook_delivery_id"] = delivery_id
        return events, None
