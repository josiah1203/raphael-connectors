"""MapperAdapter wrappers for Altium and SolidWorks."""

from __future__ import annotations

from typing import Any

from raphael_connectors.adapters.altium.adapter import AltiumAdapter as _AltiumBackend
from raphael_connectors.adapters.solidworks.adapter import SolidWorksAdapter as _SolidWorksBackend
from raphael_connectors.sdk.base import AdapterContext


class AltiumMapperAdapter:
    name = "altium"

    def __init__(self) -> None:
        self._backend = _AltiumBackend()

    def validate(self, payload: dict[str, Any]) -> list[str]:
        from raphael_artifacts.calliope_schema.validator import validate_addon_snapshot

        return validate_addon_snapshot("altium", payload)

    def map_payload(self, payload: dict[str, Any], context: AdapterContext) -> list[dict[str, Any]]:
        errors = self.validate(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return self._backend.map_payload(
            payload,
            session_id=f"{context.tenant_id}:{context.user_id}",
            user_id=context.user_id,
            project_id=context.project_id,
            tenant_id=context.tenant_id,
        )


class SolidWorksMapperAdapter:
    name = "solidworks"

    def __init__(self) -> None:
        self._backend = _SolidWorksBackend()

    def validate(self, payload: dict[str, Any]) -> list[str]:
        from raphael_artifacts.calliope_schema.validator import validate_addon_snapshot

        return validate_addon_snapshot("solidworks", payload)

    def map_payload(self, payload: dict[str, Any], context: AdapterContext) -> list[dict[str, Any]]:
        events, errors = self._backend.map_snapshot(
            payload,
            session_id=f"{context.tenant_id}:{context.user_id}",
            user_id=context.user_id,
            project_id=context.project_id,
            tenant_id=context.tenant_id,
        )
        if errors:
            raise ValueError("; ".join(errors))
        return events
