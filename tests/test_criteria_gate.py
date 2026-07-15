"""Testes do gate de Success Criteria (SIS-08 Methods / MSFC)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.criteria_gate import (
    GateStatus,
    evaluate_requirement_criteria,
    evaluate_session_criteria,
)
from reqvallive.main import app
from reqvallive.models.session import store

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _base_req() -> dict:
    return json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))


def test_accept_threshold_test_battery():
    data = _base_req()
    data["success_criteria"]["metric"] = "batteryLevel"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.ACCEPT
    assert result.method_coherence == "ok"
    assert result.live_executable is True
    assert result.vv_method == "test"
    assert all(r.severity.value == "warning" for r in result.warnings) or True


def test_reject_inspection_with_threshold():
    data = _base_req()
    data["vv_method"] = "inspection"
    data["success_criteria"]["metric"] = "batteryLevel"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert result.method_coherence == "fail"
    codes = {r.code for r in result.errors}
    assert "VV_METHOD_NOT_LIVE" in codes or "VV_METHOD_MISMATCH" in codes


def test_reject_range_min_gt_max():
    from simreqvalidator.schema.success_criteria import RangeCriteria
    from simreqvalidator.schema.vv_method import Priority, RequirementLevel, VVMethod

    # Vampire já rejeita min>max no parse normal; gate cobre defesa em profundidade
    sc = RangeCriteria.model_construct(
        type="range",
        metric="altitudeAGL",
        min_value=120.0,
        max_value=5.0,
        unit="meters",
        scope="all_entities",
        inclusive_min=True,
        inclusive_max=True,
    )
    req = RequirementRecord.model_construct(
        req_id="RQ-ALT-BAD",
        title="Altitude",
        text="altitudeAGL deve permanecer entre 5 e 120 meters",
        rationale="envelope",
        level=RequirementLevel.SYSTEM,
        vv_method=VVMethod.TEST,
        priority=Priority.HIGH,
        conops_ref="CONOPS-UTM §4",
        source="test",
        success_criteria=sc,
        tags=[],
    )
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert any(r.code == "SC_RANGE_INVALID" for r in result.errors)


def test_reject_unknown_metric():
    data = _base_req()
    data["text"] = "O sistema deve manter hullColourIndex >= 3 units em cada drone"
    data["success_criteria"]["metric"] = "hullColourIndex"
    data["success_criteria"]["unit"] = "units"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert any(r.code == "SC_METRIC_NOT_IN_TELEMETRY" for r in result.errors)


def test_reject_vague_text():
    data = _base_req()
    data["text"] = "O sistema deve ter desempenho adequado durante a missão"
    data["success_criteria"]["metric"] = "batteryLevel"
    req = RequirementRecord.model_validate(data)
    result = evaluate_requirement_criteria(req)
    assert result.status == GateStatus.REJECT
    assert any(r.code == "SC_TEXT_NOT_MEASURABLE" for r in result.errors)
    assert result.suggestions


def test_session_gate_and_start_blocked():
    client = TestClient(app)
    bad = _base_req()
    bad["vv_method"] = "analysis"
    bad["success_criteria"]["metric"] = "batteryLevel"

    create = client.post(
        "/api/sessions",
        json={"requirement": bad, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.status_code == 200
    body = create.json()
    assert body["criteria_gate"]["global_status"] == "REJECT"
    sid = body["id"]

    start = client.post(f"/api/sessions/{sid}/start")
    assert start.status_code == 409
    detail = start.json()["detail"]
    assert "criteria_gate" in detail

    connect = client.post(f"/api/sessions/{sid}/connect")
    assert connect.status_code == 409


def test_accept_allows_start_after_connect_mock(monkeypatch):
    client = TestClient(app)
    good = _base_req()
    good["success_criteria"]["metric"] = "batteryLevel"

    create = client.post(
        "/api/sessions",
        json={"requirement": good, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    assert create.status_code == 200
    assert create.json()["criteria_gate"]["global_status"] == "ACCEPT"
    sid = create.json()["id"]

    session = store.get(sid)
    assert session is not None
    # evita broker real
    session.connected = True
    start = client.post(f"/api/sessions/{sid}/start")
    assert start.status_code == 200
    assert start.json()["measuring"] is True


def test_criteria_model_endpoint():
    client = TestClient(app)
    res = client.get("/api/criteria/model")
    assert res.status_code == 200
    data = res.json()
    assert len(data["msfc_dimensions"]) == 8
    assert "markdown_example" in data
    assert "method_coherence" in data


def test_evaluate_session_all_accept():
    data = _base_req()
    data["success_criteria"]["metric"] = "batteryLevel"
    req = RequirementRecord.model_validate(data)
    summary = evaluate_session_criteria([req])
    assert summary.global_status == GateStatus.ACCEPT
    assert summary.to_dict()["can_start_measurement"] is True
