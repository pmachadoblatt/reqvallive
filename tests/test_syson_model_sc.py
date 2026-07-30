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
    assert len(tagged) >= 2
    for r in tagged:
        assert "_go_to_verification" in r.doc_raw
        # doc mínimo: sem JSON de SC
        assert "batteryLevel" not in r.doc_raw or "```" not in r.doc_raw
        assert r.success_criteria is not None
        assert r.success_criteria["metric"] == "batteryLevel"
        assert r.success_criteria["value"] == 20.0


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
