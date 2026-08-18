"""Jefferson GSE: taxa (rate / ΔΔt) e dwell (persistência ≥ T ms)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.criteria_gate import GateStatus, evaluate_requirement_criteria
from reqvallive.eval.live import (
    evaluate_sample,
    is_mvp_supported,
    observed_rate,
)
from reqvallive.main import app
from reqvallive.models.session import store
from reqvallive.syson.model_sc import success_criteria_from_requirement_textual


def _rate_req(*, value: float = 2.0, abs_rate: bool = True) -> dict:
    return {
        "req_id": "RQ-BAT-RATE-001",
        "title": "Taxa de descarga",
        "text": "batteryLevel não deve descarregar mais de 2 percent/min em cada drone",
        "rationale": "Jefferson GSE natureza taxa (slew), distinta da amplitude na janela",
        "level": "system",
        "vv_method": "test",
        "priority": "high",
        "conops_ref": "CONOPS-UTM §4",
        "source": "test",
        "success_criteria": {
            "type": "rate",
            "metric": "batteryLevel",
            "operator": "<=",
            "value": value,
            "unit": "percent/min",
            "scope": "all_entities",
            "abs_rate": abs_rate,
            "min_dt_s": 0.05,
        },
        "tags": ["battery", "rate"],
    }


def _dwell_req(*, max_duration_ms: float = 2000.0) -> dict:
    return {
        "req_id": "RQ-BAT-DWELL-001",
        "title": "Bateria baixa persistente",
        "text": "batteryLevel < 20 percent por no máximo 2 seconds em cada drone",
        "rationale": "Jefferson GSE natureza tempo/dwell — transiente curto é permitido",
        "level": "system",
        "vv_method": "test",
        "priority": "high",
        "conops_ref": "CONOPS-UTM §4",
        "source": "test",
        "success_criteria": {
            "type": "dwell",
            "metric": "batteryLevel",
            "operator": "<",
            "value": 20.0,
            "unit": "percent",
            "scope": "all_entities",
            "max_duration_ms": max_duration_ms,
        },
        "tags": ["battery", "dwell"],
    }


def test_observed_rate_percent_per_min_abs():
    # −4 % em 60 s → 4 %/min em magnitude
    assert abs(observed_rate(80.0, 76.0, 60.0, "percent/min", True) - 4.0) < 1e-9
    # climb 6 m em 1 s
    assert abs(observed_rate(20.0, 26.0, 1.0, "m/s", False) - 6.0) < 1e-9


def test_gate_accepts_rate_and_dwell():
    rate = RequirementRecord.model_validate(_rate_req())
    dwell = RequirementRecord.model_validate(_dwell_req())
    r_rate = evaluate_requirement_criteria(rate)
    r_dwell = evaluate_requirement_criteria(dwell)
    assert r_rate.status == GateStatus.ACCEPT, [e.to_dict() for e in r_rate.errors]
    assert r_dwell.status == GateStatus.ACCEPT, [e.to_dict() for e in r_dwell.errors]
    assert r_rate.criteria_type == "rate"
    assert r_dwell.criteria_type == "dwell"
    assert is_mvp_supported(rate) and is_mvp_supported(dwell)


def test_gate_rejects_rate_without_rate_unit():
    data = _rate_req()
    data["success_criteria"]["unit"] = "percent"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert any(r.code == "SC_UNIT_MISSING" for r in result.errors)


def test_rate_fail_when_discharge_exceeds_limit():
    client = TestClient(app)
    req = _rate_req(value=2.0)
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

    t0 = 1_000_000.0
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 80}, now=t0)
    assert session.drones["alpha"].ok_by_req.get(req["req_id"]) is None

    # 4 %/min > 2 → FAIL
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 76}, now=t0 + 60.0)
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is False
    observed = session.drones["alpha"].last_actual_by_req[req["req_id"]]
    assert abs(observed - 4.0) < 1e-9

    # taxa diminui — latch mantém FAIL
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 75.5}, now=t0 + 120.0)
    assert session.drones["alpha"].ok_by_req[req["req_id"]] is False


def test_rate_pass_when_within_limit():
    client = TestClient(app)
    req = _rate_req(value=5.0)
    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()
    t0 = 2_000_000.0
    session.ingest_payload({"droneName": "bravo", "batteryLevel": 80}, now=t0)
    session.ingest_payload({"droneName": "bravo", "batteryLevel": 79}, now=t0 + 60.0)
    assert session.drones["bravo"].ok_by_req[req["req_id"]] is True
    assert abs(session.drones["bravo"].last_actual_by_req[req["req_id"]] - 1.0) < 1e-9


def test_dwell_brief_dip_passes_long_dip_fails():
    client = TestClient(app)
    req = _dwell_req(max_duration_ms=2000.0)
    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.json()["criteria_gate"]["global_status"] == "ACCEPT"
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()
    t0 = 3_000_000.0

    session.ingest_payload({"droneName": "charlie", "batteryLevel": 15}, now=t0)
    assert session.drones["charlie"].ok_by_req[req["req_id"]] is True

    session.ingest_payload({"droneName": "charlie", "batteryLevel": 16}, now=t0 + 1.0)
    assert session.drones["charlie"].ok_by_req[req["req_id"]] is True

    session.ingest_payload({"droneName": "charlie", "batteryLevel": 16}, now=t0 + 2.1)
    assert session.drones["charlie"].ok_by_req[req["req_id"]] is False


def test_dwell_recovers_if_condition_clears_before_limit():
    client = TestClient(app)
    req = _dwell_req(max_duration_ms=2000.0)
    create = client.post(
        "/api/sessions",
        json={"requirement": req, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    session.start_measurement()
    t0 = 4_000_000.0
    session.ingest_payload({"droneName": "delta", "batteryLevel": 15}, now=t0)
    session.ingest_payload({"droneName": "delta", "batteryLevel": 25}, now=t0 + 0.5)
    assert session.drones["delta"].ok_by_req[req["req_id"]] is True
    session.ingest_payload({"droneName": "delta", "batteryLevel": 26}, now=t0 + 5.0)
    assert session.drones["delta"].ok_by_req[req["req_id"]] is True


def test_evaluate_sample_dwell_pending_window():
    req = RequirementRecord.model_validate(_dwell_req())
    v0 = evaluate_sample(req, 15.0, now=0.0, dwell_since=None)
    assert v0.ok is True
    assert v0.dwell_since == 0.0
    v1 = evaluate_sample(req, 15.0, now=2.5, dwell_since=0.0)
    assert v1.ok is False


def test_textual_rate_and_dwell_from_syson_item():
    rate_body = """
        doc /* _go_to_verification */
        item SuccessCriteria {
            attribute scType = "rate";
            attribute metric = "batteryLevel";
            attribute operator = "<=";
            attribute value = 2.0;
            attribute unit = "percent/min";
            attribute abs_rate = true;
        }
    """
    sc_r = success_criteria_from_requirement_textual(rate_body)
    assert sc_r is not None
    assert sc_r["type"] == "rate"
    assert sc_r["abs_rate"] is True
    assert sc_r["unit"] == "percent/min"

    dwell_body = """
        doc /* _go_to_verification */
        item SuccessCriteria {
            attribute scType = "dwell";
            attribute metric = "batteryLevel";
            attribute operator = "<";
            attribute value = 20.0;
            attribute unit = "percent";
            attribute max_duration_ms = 2000;
        }
    """
    sc_d = success_criteria_from_requirement_textual(dwell_body)
    assert sc_d is not None
    assert sc_d["type"] == "dwell"
    assert sc_d["max_duration_ms"] == 2000
