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
