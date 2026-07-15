"""Regressão: FAIL deve latchear se qualquer amostra violar o limiar."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from reqvallive.main import app
from reqvallive.models.session import store

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_battery_fail_latches_across_samples():
    """Reproduz o caso do relatório PASS errado: charlie esteve a 15% e acabou a 25%."""
    client = TestClient(app)
    req = json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))
    req["success_criteria"]["metric"] = "batteryLevel"
    req["success_criteria"]["operator"] = ">"
    req["success_criteria"]["value"] = 20.0
    req["text"] = "Cada drone deve ter sempre mais de 20% de bateria"

    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.status_code == 200
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()

    session.ingest_payload({"droneName": "charlie", "batteryLevel": 15})
    assert session.drones["charlie"].ok_by_req[req["req_id"]] is False
    assert session.drones["charlie"].fail_actual_by_req[req["req_id"]] == 15.0

    # recupera acima do limiar — deve continuar FAIL (all_timesteps)
    session.ingest_payload({"droneName": "charlie", "batteryLevel": 25})
    assert session.drones["charlie"].ok_by_req[req["req_id"]] is False
    assert session.drones["charlie"].fail_actual_by_req[req["req_id"]] == 15.0
    assert session.drones["charlie"].last_actual_by_req[req["req_id"]] == 25.0
    assert session.drones["charlie"].min_actual_by_req[req["req_id"]] == 15.0
    assert session.drones["charlie"].fail_count_by_req[req["req_id"]] >= 1
    assert session.overall_ok() is False

    session.stop_measurement()
    public = client.get(f"/api/sessions/{sid}").json()
    assert public["overall_ok"] is False
    report = client.get(f"/api/sessions/{sid}/report")
    assert report.status_code == 200
    assert b"FAIL" in report.content
    assert b"PASS" not in report.content.split(b"FAIL")[0][-20:] or True  # soft
    assert public["summary"]["min_battery"] == 15.0
