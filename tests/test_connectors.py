"""Connectors API tests."""

from fastapi.testclient import TestClient

from raphael_connectors.app import app

client = TestClient(app)


def test_list_connectors() -> None:
    res = client.get("/v1/connectors")
    assert res.status_code == 200
    body = res.json()
    assert "connected" in body and "available" in body


def test_connect_adapter() -> None:
    res = client.post("/v1/connectors/KiCad/connect")
    assert res.status_code == 200
    assert res.json()["status"] == "connected"


def test_webhook_ingest() -> None:
    res = client.post("/v1/connectors/webhooks/github", json={"event": "push"})
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"


def test_kicad_ingest_parses_content() -> None:
    res = client.post(
        "/v1/connectors/ingest/kicad",
        json={
            "module_id": "power-board-v2",
            "content": '(footprint "QFN-32" (property "Reference" "U1")) (net 1 "VCC")',
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["parsed"]["valid"] is True
    assert body["events_emitted"] >= 1


def test_altium_ingest_validates_payload() -> None:
    res = client.post(
        "/v1/connectors/ingest/altium",
        json={
            "module_id": "board-1",
            "document_id": "brd-1",
            "components": [{"designator": "U1"}],
        },
    )
    assert res.status_code == 200
    assert res.json()["events"] >= 1
