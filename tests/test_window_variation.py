"""Variação genérica na janela (statistical aggregation=range) sobre qualquer métrica MQTT."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.criteria_gate import GateStatus, evaluate_requirement_criteria
from reqvallive.eval.live import evaluate_sample, is_mvp_supported, window_observed
from reqvallive.main import app
from reqvallive.metrics.registry import extract_metric_from_payload
from reqvallive.models.session import store

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _altitude_range_req(*, value: float = 1.0) -> dict:
    return {
        "req_id": "RQ-ALT-VAR-001",
        "title": "Variação de altitude",
        "text": "A altitudeAGL de cada drone não deve variar mais de 1 meter durante a missão",
        "rationale": "Manter envelope de voo estável",
        "level": "system",
        "vv_method": "test",
        "priority": "high",
        "conops_ref": "CONOPS-UTM §4",
        "source": "test",
        "success_criteria": {
            "type": "statistical",
            "metric": "altitudeAGL",
            "aggregation": "range",
            "operator": "<=",
            "value": value,
            "unit": "meters",
        },
        "tags": ["altitude", "variation"],
    }


def test_window_observed_range_generic():
    assert window_observed("range", 10.0, 10.5) == 0.5
    assert window_observed("max", 10.0, 12.0) == 12.0
    assert window_observed("min", 10.0, 12.0) == 10.0


def test_gate_accepts_statistical_range():
    req = RequirementRecord.model_validate(_altitude_range_req())
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.ACCEPT, [r.to_dict() for r in result.errors]
    assert result.criteria_type == "statistical"
    assert is_mvp_supported(req) is True


def test_gate_rejects_statistical_mean():
    data = _altitude_range_req()
    data["success_criteria"]["aggregation"] = "mean"
    data["text"] = "A média de altitudeAGL deve ser <= 50 meters"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert any(r.code == "SC_AGGREGATION_UNSUPPORTED" for r in result.errors)


def test_altitude_from_location_only():
    payload = {"droneName": "alpha", "location": {"latitude": -23.0, "longitude": -45.0, "altitude": 42.5}}
    assert extract_metric_from_payload("altitudeAGL", payload) == 42.5


def test_altitude_variation_fail_when_span_exceeds_limit():
    client = TestClient(app)
    req = _altitude_range_req(value=1.0)
    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.status_code == 200
    assert create.json()["criteria_gate"]["global_status"] == "ACCEPT"
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()

    session.ingest_payload(
        {"droneName": "alpha", "altitudeAGL": 20.0, "location": {"latitude": 1, "longitude": 1, "altitude": 20.0}}
    )
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is True
    assert session.drones["alpha"].last_actual_by_req[req["req_id"]] == 0.0

    session.ingest_payload(
        {"droneName": "alpha", "altitudeAGL": 20.4, "location": {"latitude": 1, "longitude": 1, "altitude": 20.4}}
    )
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is True
    assert abs(session.drones["alpha"].last_actual_by_req[req["req_id"]] - 0.4) < 1e-9

    session.ingest_payload(
        {"droneName": "alpha", "altitudeAGL": 21.5, "location": {"latitude": 1, "longitude": 1, "altitude": 21.5}}
    )
    # range = 1.5 > 1.0 → FAIL
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is False
    assert abs(session.drones["alpha"].last_actual_by_req[req["req_id"]] - 1.5) < 1e-9
    assert session.drones["alpha"].min_actual_by_req[req["req_id"]] == 20.0
    assert session.drones["alpha"].max_actual_by_req[req["req_id"]] == 21.5

    # estabiliza — continua FAIL (latch)
    session.ingest_payload(
        {"droneName": "alpha", "altitudeAGL": 21.0, "location": {"latitude": 1, "longitude": 1, "altitude": 21.0}}
    )
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is False
    assert session.overall_ok() is False


def test_battery_variation_same_mechanism():
    """Mesmo mecanismo genérico: range(batteryLevel) <= 5 — não é métrica nova."""
    data = {
        "req_id": "RQ-BAT-VAR-001",
        "title": "Bateria estável",
        "text": "batteryLevel não deve variar mais de 5 percent em cada drone",
        "rationale": "descarga controlada",
        "level": "system",
        "vv_method": "test",
        "priority": "high",
        "conops_ref": "CONOPS",
        "source": "test",
        "success_criteria": {
            "type": "statistical",
            "metric": "batteryLevel",
            "aggregation": "range",
            "operator": "<=",
            "value": 5.0,
            "unit": "percent",
        },
        "tags": ["battery"],
    }
    req = RequirementRecord.model_validate(data)
    assert evaluate_requirement_criteria(req).status == GateStatus.ACCEPT

    client = TestClient(app)
    create = client.post(
        "/api/sessions",
        json={"requirement": data, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()
    session.ingest_payload({"droneName": "bravo", "batteryLevel": 80})
    session.ingest_payload({"droneName": "bravo", "batteryLevel": 76})
    assert session.drones["bravo"].ok_by_req[data["req_id"]] is True
    session.ingest_payload({"droneName": "bravo", "batteryLevel": 70})
    assert session.drones["bravo"].ok_by_req[data["req_id"]] is False
    assert abs(session.drones["bravo"].last_actual_by_req[data["req_id"]] - 10.0) < 1e-9


def test_evaluate_sample_range_detail():
    req = RequirementRecord.model_validate(_altitude_range_req(value=1.0))
    v = evaluate_sample(req, 21.5, sample_min=20.0, sample_max=21.5)
    assert v.supported is True
    assert v.ok is False
    assert v.value == 1.5
    assert "range" in v.detail
