"""Success Criteria a partir do modelo SysON (não do Documentation)."""

from __future__ import annotations

from pathlib import Path

from reqvallive.sysml.import_catia import parse_sysml_export, requirements_for_verification
from reqvallive.syson.model_sc import (
    attr_key_and_value_from_element,
    success_criteria_from_requirement_textual,
    success_criteria_from_syson_elements,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "models" / "syson" / "reqvallive_demo.sysml"


def test_f2_inline_declared_name_assignment():
    """UI SysON: F2 grava `metric = \"batteryLevel\"` como declaredName (sem valuation)."""
    key, val = attr_key_and_value_from_element(
        {
            "@type": "AttributeUsage",
            "@id": "a1",
            "declaredName": 'metric = "batteryLevel"',
            "name": 'metric = "batteryLevel"',
        }
    )
    assert key == "metric"
    assert val == "batteryLevel"
    key2, val2 = attr_key_and_value_from_element(
        {
            "@type": "AttributeUsage",
            "@id": "a2",
            "declaredName": "value = 20.0",
            "name": "value = 20.0",
        }
    )
    assert key2 == "value"
    assert val2 == 20.0


def test_sc_from_f2_inline_attrs_on_requirement():
    req = {"@type": "RequirementUsage", "@id": "rq1", "declaredName": "RQ_01"}
    els = {
        "rq1": req,
        "a1": {
            "@type": "AttributeUsage",
            "@id": "a1",
            "declaredName": 'scType = "threshold"',
            "owner": {"@id": "rq1"},
        },
        "a2": {
            "@type": "AttributeUsage",
            "@id": "a2",
            "declaredName": 'metric = "batteryLevel"',
            "owner": {"@id": "rq1"},
        },
        "a3": {
            "@type": "AttributeUsage",
            "@id": "a3",
            "declaredName": 'operator = ">="',
            "owner": {"@id": "rq1"},
        },
        "a4": {
            "@type": "AttributeUsage",
            "@id": "a4",
            "declaredName": "value = 20.0",
            "owner": {"@id": "rq1"},
        },
        "a5": {
            "@type": "AttributeUsage",
            "@id": "a5",
            "declaredName": 'unit = "percent"',
            "owner": {"@id": "rq1"},
        },
        "a6": {
            "@type": "AttributeUsage",
            "@id": "a6",
            "declaredName": 'scope = "all_entities"',
            "owner": {"@id": "rq1"},
        },
    }
    sc = success_criteria_from_syson_elements(req, els)
    assert sc is not None
    assert sc["metric"] == "batteryLevel"
    assert sc["value"] == 20.0
    assert sc["operator"] == ">="
    assert sc["unit"] == "percent"



def test_demo_sysml_sc_from_item_not_doc():
    text = DEMO.read_text(encoding="utf-8")
    tagged = requirements_for_verification(text)
    assert len(tagged) >= 4
    by_name = {r.name: r for r in tagged}
    for name in ("RQ_BAT_001", "RQ_01", "RQ_ALT_BAND_001", "RQ_ALT_VAR_001", "RQ_SEP_001"):
        assert name in by_name
        r = by_name[name]
        assert "_go_to_verification" in r.doc_raw
        assert "```" not in r.doc_raw
        assert r.success_criteria is not None

    assert by_name["RQ_BAT_001"].success_criteria["type"] == "threshold"
    assert by_name["RQ_BAT_001"].success_criteria["metric"] == "batteryLevel"
    assert by_name["RQ_ALT_BAND_001"].success_criteria["type"] == "range"
    assert by_name["RQ_ALT_BAND_001"].success_criteria["min_value"] == 20.0
    assert by_name["RQ_ALT_BAND_001"].success_criteria["max_value"] == 30.0
    assert by_name["RQ_ALT_VAR_001"].success_criteria["type"] == "statistical"
    assert by_name["RQ_ALT_VAR_001"].success_criteria["aggregation"] == "range"
    assert by_name["RQ_ALT_VAR_001"].success_criteria["value"] == 1.0
    assert by_name["RQ_SEP_001"].success_criteria["metric"] == "min_separation_m"


def test_textual_success_criteria_range_and_statistical():
    range_body = """
        doc /* _go_to_verification */
        item SuccessCriteria {
            attribute scType = "range";
            attribute metric = "altitudeAGL";
            attribute min_value = 20.0;
            attribute max_value = 30.0;
            attribute unit = "meters";
            attribute scope = "all_entities";
        }
    """
    sc_r = success_criteria_from_requirement_textual(range_body)
    assert sc_r is not None
    assert sc_r["type"] == "range"
    assert sc_r["min_value"] == 20.0
    assert sc_r["max_value"] == 30.0

    stat_body = """
        doc /* _go_to_verification */
        item SuccessCriteria {
            attribute scType = "statistical";
            attribute metric = "altitudeAGL";
            attribute aggregation = "range";
            attribute operator = "<=";
            attribute value = 1.0;
            attribute unit = "meters";
        }
    """
    sc_s = success_criteria_from_requirement_textual(stat_body)
    assert sc_s is not None
    assert sc_s["type"] == "statistical"
    assert sc_s["aggregation"] == "range"
    assert sc_s["value"] == 1.0


def test_textual_success_criteria_item_parser():
    body = """
        doc /* _go_to_verification */
        item SuccessCriteria {
            attribute scType = "threshold";
            attribute metric = "batteryLevel";
            attribute operator = ">=";
            attribute value = 20.0;
            attribute unit = "percent";
            attribute scope = "all_entities";
        }
    """
    sc = success_criteria_from_requirement_textual(body)
    assert sc is not None
    assert sc["type"] == "threshold"
    assert sc["metric"] == "batteryLevel"
    assert sc["operator"] == ">="
    assert sc["value"] == 20.0


def test_parse_sysml_export_finds_rq01():
    text = DEMO.read_text(encoding="utf-8")
    names = {r.name for r in parse_sysml_export(text) if r.tagged_for_verification}
    assert "RQ_01" in names
    assert "RQ_BAT_001" in names
    assert "RQ_ALT_BAND_001" in names
    assert "RQ_ALT_VAR_001" in names
    assert "RQ_SEP_001" in names
