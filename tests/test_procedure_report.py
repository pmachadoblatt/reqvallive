"""Relatório de procedimento V&V (item P0 1.2)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from reqvallive.main import app
from reqvallive.models.session import store
from reqvallive.reports.html_report import build_html_report

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _battery_req() -> dict:
    data = json.loads((EXAMPLES / "battery_threshold.json").read_text(encoding="utf-8"))
    data["success_criteria"]["metric"] = "batteryLevel"
    return data


def test_procedure_report_has_required_sections():
    client = TestClient(app)
    create = client.post(
        "/api/sessions",
        json={"requirement": _battery_req(), "mqtt_broker": "127.0.0.1", "mqtt_topic": "lab/test"},
    )
    assert create.status_code == 200
    sid = create.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    client.post(f"/api/sessions/{sid}/start")
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 15})
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 25})
    client.post(f"/api/sessions/{sid}/stop")

    html = build_html_report(session)
    assert "Relatório de procedimento" in html
    assert 'id="procedimento-vv"' in html
    assert "1. Procedimento de V&amp;V" in html or "1. Procedimento de V&V" in html
    assert 'id="condicoes-medicao"' in html
    assert "2. Condições de medição" in html
    assert "MQTT" in html
    assert "lab/test" in html
    assert 'id="snapshot-sc"' in html
    assert "3. Success Criteria aprovado (snapshot)" in html
    assert 'id="resultados"' in html
    assert "4. Resultados" in html
    assert "esperado" in html.lower()
    assert 'id="amostras"' in html
    assert "vv_method" in html or ">test<" in html
    assert "ACCEPT" in html
    assert "FAIL" in html  # bateria 15% violou

    # Endpoint HTTP também devolve o HTML novo
    report = client.get(f"/api/sessions/{sid}/report")
    assert report.status_code == 200
    body = report.text
    assert "Condições de medição" in body
    assert "Procedimento de V" in body
