"""UPDATE CATIA pós-medição (artefato determinístico + endpoint LLM)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from reqvallive.main import app
from reqvallive.models.session import store

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_stop_builds_catia_update_and_llm_optional():
    client = TestClient(app)
    sysml = (EXAMPLES / "catia_export_go_to_verification.sysml").read_text(encoding="utf-8")
    created = client.post(
        "/api/requirements/from-sysml",
        json={"sysml_text": sysml, "mqtt_broker": "127.0.0.1", "mqtt_topic": "t"},
    )
    sid = created.json()["id"]
    session = store.get(sid)
    assert session is not None
    session.connected = True
    client.post(f"/api/sessions/{sid}/gse/mount")
    client.post(f"/api/sessions/{sid}/start")
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 12})
    session.ingest_payload({"droneName": "alpha", "batteryLevel": 30})

    stopped = client.post(f"/api/sessions/{sid}/stop")
    assert stopped.status_code == 200
    body = stopped.json()
    assert body["measurement_ended"] is True
    assert body["has_catia_update"] is True
    assert body["catia_update"]["overall_ok"] is False
    assert body["catia_update"]["overall_tag"] == "_verification_FAIL"
    assert body["catia_update"]["requirements"][0]["verification_tag"] == "_verification_FAIL"
    assert "_go_to_verification" in body["catia_update"]["requirements"][0]["catia_doc_append"]

    # Sem LLM (CI / casa offline)
    upd = client.post(f"/api/sessions/{sid}/catia/update?use_llm=false")
    assert upd.status_code == 200
    assert upd.json()["catia_update"]["llm_enrichment"] is None

    got = client.get(f"/api/sessions/{sid}/catia/update")
    assert got.status_code == 200
    assert got.json()["session_id"] == sid
