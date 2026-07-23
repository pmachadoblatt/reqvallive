"""Parser de export CATIA SysML v2 (_go_to_verification)."""

from __future__ import annotations

from pathlib import Path

from reqvallive.sysml.import_catia import (
    GO_TO_VERIFICATION,
    parse_sysml_export,
    requirements_for_verification,
    summary_dict,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_parse_example_sysml_tags_and_sc():
    text = (EXAMPLES / "catia_export_go_to_verification.sysml").read_text(encoding="utf-8")
    all_reqs = parse_sysml_export(text)
    assert len(all_reqs) == 2
    tagged = requirements_for_verification(text)
    assert len(tagged) == 1
    req = tagged[0]
    assert req.name == "RQ_BAT_001"
    assert req.tagged_for_verification is True
    assert req.success_criteria is not None
    assert req.success_criteria["metric"] == "batteryLevel"
    assert req.success_criteria["value"] == 20.0
    assert GO_TO_VERIFICATION in req.doc_raw
    assert "batteryLevel" in req.text

    summary = summary_dict(all_reqs)
    assert summary["tagged_for_verification"] == 1
    assert summary["ready_with_sc"] == 1


def test_ignore_untagged():
    text = """
    package P {
      requirement OnlyDocs {
        doc /* sem tag de verificação */
      }
    }
    """
    assert requirements_for_verification(text) == []


def test_kv_style_sc_without_json():
    text = """
    package P {
      requirement RQ_ALT {
        doc /*
        _go_to_verification
        Altitude não deve variar mais de 1 meter.
        type: statistical
        metric: altitudeAGL
        aggregation: range
        operator: <=
        value: 1
        unit: meters
        */
      }
    }
    """
    tagged = requirements_for_verification(text)
    assert len(tagged) == 1
    sc = tagged[0].success_criteria
    assert sc is not None
    assert sc["type"] == "statistical"
    assert sc["aggregation"] == "range"
    assert sc["value"] == 1.0
