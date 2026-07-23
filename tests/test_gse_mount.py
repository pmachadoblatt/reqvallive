"""Montar GSE após gate ACCEPT."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from reqvallive.main import app

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_mount_gse_after_accept():
    client = TestClient(app)
    sysml = (EXAMPLES / "catia_export_go_to_verification.sysml").read_text(encoding="utf-8")
    created = client.post(
        "/api/requirements/from-sysml",
        json={"sysml_text": sysml, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert created.status_code == 200
    sid = created.json()["id"]

    status = client.get(f"/api/sessions/{sid}/validation-status")
    assert status.status_code == 200
    assert status.json()["ok"] is True
    assert status.json()["can_mount_gse"] is True

    before = client.get(f"/api/sessions/{sid}/gse")
    assert before.status_code == 404

    mounted = client.post(f"/api/sessions/{sid}/gse/mount")
    assert mounted.status_code == 200
    body = mounted.json()
    assert body["gse_mounted"] is True
    assert body["gse_config"]["mqtt"]["topic"] == "t"
    assert "batteryLevel" in body["gse_config"]["metrics"]

    gse = client.get(f"/api/sessions/{sid}/gse")
    assert gse.status_code == 200
    assert gse.json()["role"] == "GSE"
