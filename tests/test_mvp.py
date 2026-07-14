"""Testes MVP (sem broker / sem LLM real)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.live import evaluate_value, is_mvp_supported
from reqvallive.main import app
from reqvallive.metrics.registry import drone_id, extract_battery, extract_metric, min_separation_from_positions
from reqvallive.sysml.generator import generate_sysml

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def battery_req() -> dict:
    return json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_evaluate_threshold_pass_fail(battery_req: dict):
    # Adapt metric name if needed
    req = RequirementRecord.model_validate(battery_req)
    assert is_mvp_supported(req)
    assert evaluate_value(req, 50.0).ok is True
    assert evaluate_value(req, 10.0).ok is False


def test_sysml_contains_constraint(battery_req: dict):
    req = RequirementRecord.model_validate(battery_req)
    text = generate_sysml(req, "conceptio/reqval")
    assert "requirement def" in text
    assert "SystemUnderTest" in text
    assert "verification def" in text


def test_lab_payload_battery_and_drone():
    payload = {
        "droneName": "dji_mini_4_pro",
        "batteryLevel": 86,
        "location": {"latitude": -23.18, "longitude": -45.88, "altitude": 600},
    }
    assert drone_id(payload) == "dji_mini_4_pro"
    assert extract_battery(payload) == 86.0
    assert extract_metric("batteryLevel", payload) == 86.0


def test_multi_drone_separation():
    positions = {
        "a": (-23.189612, -45.884123),
        "b": (-23.189700, -45.884200),
    }
    dist = min_separation_from_positions(positions)
    assert dist is not None
    assert dist > 0


def test_session_multi_drone(client: TestClient, battery_req: dict):
    # Use batteryLevel metric like lab
    battery_req = dict(battery_req)
    battery_req["success_criteria"] = dict(battery_req["success_criteria"])
    battery_req["success_criteria"]["metric"] = "batteryLevel"

    create = client.post(
        "/api/sessions",
        json={
            "requirement": battery_req,
            "mqtt_broker": "127.0.0.1",
            "mqtt_topic": "conceptio/reqval",
        },
    )
    assert create.status_code == 200, create.text
    sid = create.json()["id"]

    from reqvallive.models.session import store

    session = store.get(sid)
    assert session is not None
    session.start_measurement()
    session.ingest_payload(
        {
            "droneName": "drone_a",
            "batteryLevel": 90,
            "location": {"latitude": -23.1896, "longitude": -45.8841, "altitude": 600},
        }
    )
    session.ingest_payload(
        {
            "droneName": "drone_b",
            "batteryLevel": 15,
            "location": {"latitude": -23.1897, "longitude": -45.8842, "altitude": 600},
        }
    )

    public = client.get(f"/api/sessions/{sid}").json()
    assert public["summary"]["drone_count"] == 2
    assert public["overall_ok"] is False

    md = client.get(f"/api/sessions/{sid}/model.md")
    assert md.status_code == 200
    assert b"# Modelo ReqValLive" in md.content

    report = client.get(f"/api/sessions/{sid}/report")
    assert report.status_code == 200
    assert b"FAIL" in report.content
