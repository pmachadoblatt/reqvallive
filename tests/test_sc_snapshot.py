"""Snapshot imutável do Success Criteria aprovado no /start."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from simreqvalidator.schema.success_criteria import ThresholdCriteria

from reqvallive.main import app
from reqvallive.models.session import store
from reqvallive.reports.html_report import build_html_report

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _battery_req() -> dict:
    data = json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))
    data["success_criteria"]["metric"] = "batteryLevel"
    return data


def test_snapshot_absent_before_start():
    client = TestClient(app)
    create = client.post(
        "/api/sessions",
        json={"requirement": _battery_req(), "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.status_code == 200
    body = create.json()
    assert body["sc_frozen"] is False
    assert body["approved_sc_snapshot"] is None
    sid = body["id"]
    assert client.get(f"/api/sessions/{sid}/approved-sc").status_code == 404


def test_snapshot_frozen_on_start_survives_mutation():
    client = TestClient(app)
    req = _battery_req()
    original_value = float(req["success_criteria"]["value"])
    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True

    start = client.post(f"/api/sessions/{sid}/start")
    assert start.status_code == 200
    started = start.json()
    assert started["sc_frozen"] is True
    snap = started["approved_sc_snapshot"]
    assert snap is not None
    assert snap["gate_status"] == "ACCEPT"
    assert snap["requirements"][0]["success_criteria"]["value"] == original_value

    # Mutar a lista de trabalho NÃO altera o snapshot nem a avaliação da corrida
    sc = session.requirements[0].success_criteria
    assert isinstance(sc, ThresholdCriteria)
    sc.value = 99.0
    assert session.requirements[0].success_criteria.value == 99.0
    assert session.approved_sc_snapshot["requirements"][0]["success_criteria"]["value"] == original_value
    assert session.active_requirements()[0].success_criteria.value == original_value

    # Telemetria avaliada contra o limiar ORIGINAL (20), não 99
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 50})
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is True

    session.stop_measurement()
    public = client.get(f"/api/sessions/{sid}").json()
    assert public["sc_frozen"] is True
    assert public["approved_sc_snapshot"]["requirements"][0]["success_criteria"]["value"] == original_value

    dedicated = client.get(f"/api/sessions/{sid}/approved-sc")
    assert dedicated.status_code == 200
    assert dedicated.json()["requirements"][0]["success_criteria"]["value"] == original_value

    report = build_html_report(session)
    assert "Success Criteria aprovado (snapshot)" in report
    assert str(int(original_value)) in report or f"{original_value}" in report
    assert "Congelado" in report


def test_snapshot_survives_stop():
    client = TestClient(app)
    create = client.post(
        "/api/sessions",
        json={"requirement": _battery_req(), "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    client.post(f"/api/sessions/{sid}/start")
    frozen_at = session.approved_sc_snapshot["frozen_at"]
    client.post(f"/api/sessions/{sid}/stop")
    assert session.approved_sc_snapshot is not None
    assert session.approved_sc_snapshot["frozen_at"] == frozen_at
    assert session.measurement_ended is True
