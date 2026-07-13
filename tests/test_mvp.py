"""Testes unitários ReqValLive (sem broker MQTT real)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.live import evaluate_value, is_mvp_supported
from reqvallive.main import app
from reqvallive.sysml.generator import generate_sysml

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def battery_req() -> dict:
    return json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_evaluate_threshold_pass_fail(battery_req: dict):
    req = RequirementRecord.model_validate(battery_req)
    assert is_mvp_supported(req)
    assert evaluate_value(req, 50.0).ok is True
    assert evaluate_value(req, 10.0).ok is False


def test_sysml_contains_constraint(battery_req: dict):
    req = RequirementRecord.model_validate(battery_req)
    text = generate_sysml(req, "conceptio/reqval")
    assert "requirement def" in text
    assert "currentValue >= 20.0" in text
    assert "conceptio/reqval" in text
    assert "batteryLevel" in text or "battery_level" in text


def test_validate_api(client: TestClient, battery_req: dict):
    res = client.post("/api/requirements/validate", json={"requirement": battery_req})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["supported_live"] is True
    assert body["metric"] == "battery_level"


def test_session_ingest_and_report(client: TestClient, battery_req: dict):
    create = client.post(
        "/api/sessions",
        json={
            "requirement": battery_req,
            "mqtt_broker": "127.0.0.1",
            "mqtt_topic": "conceptio/reqval",
        },
    )
    assert create.status_code == 200
    sid = create.json()["id"]

    sysml = client.get(f"/api/sessions/{sid}/sysml")
    assert sysml.status_code == 200
    assert b"package ReqValLive_" in sysml.content

    # Ingestão directa sem MQTT (simula payload)
    from reqvallive.models.session import store

    session = store.get(sid)
    assert session is not None
    session.measuring = True
    session.ingest_payload({"battery_level": 95.0, "timestamp": 1})
    session.ingest_payload({"battery_level": 15.0, "timestamp": 2})
    session.measuring = False

    public = client.get(f"/api/sessions/{sid}").json()
    assert public["summary"]["sample_count"] == 2
    assert public["summary"]["violations"] == 1
    assert public["summary"]["final_pass"] is False

    report = client.get(f"/api/sessions/{sid}/report")
    assert report.status_code == 200
    assert b"FAIL" in report.content
    assert b"RQ-BAT-001" in report.content
