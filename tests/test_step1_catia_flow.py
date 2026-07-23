"""Passo 1: export CATIA (.sysml) → sessão → gate ACCEPT (sem Magic aberto)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from reqvallive.main import app
from reqvallive.models.session import store

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_step1_catia_example_to_gate_accept_and_ready_to_measure():
    client = TestClient(app)
    sysml = (EXAMPLES / "catia_export_go_to_verification.sysml").read_text(encoding="utf-8")

    # 1) Inspecionar (parse only)
    parsed = client.post(
        "/api/requirements/parse-sysml",
        json={"sysml_text": sysml, "create_session": False},
    )
    assert parsed.status_code == 200
    summary = parsed.json()
    assert summary["tagged_for_verification"] == 1
    assert summary["ready_with_sc"] == 1

    # 2) Importar → criar sessão + gate
    created = client.post(
        "/api/requirements/from-sysml",
        json={
            "sysml_text": sysml,
            "create_session": True,
            "mqtt_broker": "127.0.0.1",
            "mqtt_topic": "conceptio/reqval",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["criteria_gate"]["global_status"] == "ACCEPT"
    assert body["requirements"][0]["req_id"] == "RQ_BAT_001"
    assert body["requirements"][0]["success_criteria"]["metric"] == "batteryLevel"
    sid = body["id"]

    # 3) Com ACCEPT, /start fica liberado (GSE/MQTT = próximos cliques na UI)
    session = store.get(sid)
    assert session is not None
    session.connected = True
    start = client.post(f"/api/sessions/{sid}/start")
    assert start.status_code == 200
    assert start.json()["sc_frozen"] is True
    assert start.json()["approved_sc_snapshot"]["gate_status"] == "ACCEPT"

    # 4) Uma amostra simulada (como se viesse do publisher)
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 55})
    assert session.drones["alpha"].ok_by_req["RQ_BAT_001"] is True
    session.stop_measurement()
    report = client.get(f"/api/sessions/{sid}/report")
    assert report.status_code == 200
    assert "Procedimento de V" in report.text
    assert "Success Criteria aprovado" in report.text
