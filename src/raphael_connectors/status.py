"""Adapter status from event stream — ported from sonoma_api."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def adapter_status_from_events(
    events: list[dict[str, Any]],
    connections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    by_tool: dict[str, dict[str, Any]] = {}
    now = datetime.now(timezone.utc)
    for event in events:
        source = event.get("source") or {}
        tool = source.get("tool") or source.get("adapter") or event.get("tool") or "unknown"
        if tool == "unknown":
            continue
        project = event.get("project_id") or "default"
        ts = event.get("timestamp_utc") or event.get("created_at") or ""
        entry = by_tool.setdefault(tool, {"tool": tool, "last_event_at": ts, "repos": set(), "event_count": 0})
        entry["event_count"] += 1
        entry["repos"].add(project)
        if ts > entry["last_event_at"]:
            entry["last_event_at"] = ts

    available = [
        {"tool": "KiCad", "action": "Install connector", "connected": False},
        {"tool": "SolidWorks", "action": "Install connector", "connected": False},
        {"tool": "GitHub", "action": "Connect account", "connected": False},
    ]

    connected = []
    for tool, data in sorted(by_tool.items()):
        live = False
        if data["last_event_at"]:
            try:
                last = datetime.fromisoformat(data["last_event_at"].replace("Z", "+00:00"))
                live = (now - last).total_seconds() < 300
            except ValueError:
                live = False
        connected.append(
            {
                "tool": tool,
                "status": "live" if live else "idle",
                "last_event": data["last_event_at"],
                "repo_count": len(data["repos"]),
                "event_count": data["event_count"],
            }
        )

    if connections:
        for c in connections:
            tool = c["tool"]
            if not any(x["tool"] == tool for x in connected):
                connected.append(
                    {
                        "tool": tool,
                        "status": "idle",
                        "last_event": c.get("connected_at"),
                        "repo_count": 0,
                        "event_count": 0,
                    }
                )

    for c in connected:
        available = [a for a in available if a["tool"] != c["tool"]]

    if not connected:
        connected = [{"tool": "KiCad", "status": "idle", "last_event": None, "repo_count": 0, "event_count": 0}]

    return {"connected": connected, "available": available}
