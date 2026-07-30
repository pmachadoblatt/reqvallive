"""SysON client + demo .sysml alinhado ao parser CATIA."""

from __future__ import annotations

from pathlib import Path

from reqvallive.sysml.import_catia import parse_sysml_export
from reqvallive.syson.client import SysonClient, SysonSettings, probe_summary

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "models" / "syson" / "reqvallive_demo.sysml"


def test_demo_sysml_has_go_to_verification():
    text = DEMO.read_text(encoding="utf-8")
    parsed = parse_sysml_export(text)
    tagged = [r for r in parsed if r.tagged_for_verification]
    names = {r.name for r in tagged}
    assert "RQ_BAT_001" in names
    assert "RQ_01" in names
    bat = next(r for r in tagged if r.name == "RQ_BAT_001")
    assert bat.success_criteria is not None
    assert bat.success_criteria.get("metric") == "batteryLevel"


def test_syson_probe_against_running_server():
    """Integração: só corre se o Docker SysON estiver no ar."""
    import httpx

    try:
        r = httpx.get("http://127.0.0.1:8081/api/rest/projects", timeout=2.0)
    except httpx.HTTPError:
        import pytest

        pytest.skip("SysON nao esta a correr em :8081")
    if r.status_code != 200:
        import pytest

        pytest.skip(f"SysON API HTTP {r.status_code}")

    with SysonClient(SysonSettings()) as client:
        summary = probe_summary(client, req_filter="RQ_")
    assert summary["health"]["ok"] is True
    assert summary["health"]["project_count"] >= 1
    names = {x["name"] for x in summary["requirements"]}
    assert "RQ_01" in names or any("RQ_" in n for n in names)
