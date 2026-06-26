"""Simulation script adapters for Ansys and COMSOL."""

from __future__ import annotations

from typing import Any

from raphael_audit.core.event_builder import build_event


class SimulationScriptAdapter:
    """Shared mapping for simulation setup/result JSON summaries."""

    def __init__(self, tool: str) -> None:
        self.tool_identifier = tool
        self.application = "LabFlow"

    def map_summary(
        self,
        summary: dict[str, Any],
        *,
        session_id: str,
        user_id: str,
        project_id: str | None = None,
        tenant_id: str = "local",
    ) -> list[dict[str, Any]]:
        proj = project_id or summary.get("project_id", "simulation")
        doc_id = summary.get("document_id", proj)
        events: list[dict[str, Any]] = []
        if summary.get("setup"):
            events.append(
                build_event(
                    event_type="simulation.setup_captured",
                    payload={**summary["setup"], "document_id": doc_id},
                    session_id=session_id,
                    user_id=user_id,
                    project_id=proj,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                    application=self.application,
                )
            )
        if summary.get("result"):
            events.append(
                build_event(
                    event_type="simulation.result_captured",
                    payload={**summary["result"], "document_id": doc_id},
                    session_id=session_id,
                    user_id=user_id,
                    project_id=proj,
                    tool_identifier=self.tool_identifier,
                    tenant_id=tenant_id,
                    application=self.application,
                )
            )
        return events


class AnsysSimulationAdapter(SimulationScriptAdapter):
    def __init__(self) -> None:
        super().__init__("ansys")


class ComsolSimulationAdapter(SimulationScriptAdapter):
    def __init__(self) -> None:
        super().__init__("comsol")
