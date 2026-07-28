"""Unitários do export CSV Sync + patch SysML."""

from __future__ import annotations

from reqvallive.reports.catia_export import (
    build_csv_sync,
    patch_sysml_docs,
)


def test_csv_sync_uses_llm_doc_when_present():
    update = {
        "requirements": [
            {
                "req_id": "RQ_BAT_001",
                "title": "Battery",
                "verification_tag": "_verification_FAIL",
                "catia_doc_append": "_verification_FAIL\nplain",
                "catia_doc_llm": "_verification_FAIL\nllm-enriched",
            }
        ]
    }
    csv_text = build_csv_sync(update).lstrip("\ufeff")
    assert "llm-enriched" in csv_text
    assert "plain" not in csv_text.split("\n")[1]


def test_patch_sysml_replaces_doc_keeps_others():
    source = """package Model {
    requirement RQ_BAT_001 {
        doc /*
        _go_to_verification
        old
        */
    }
    requirement RQ_OTHER {
        doc /*
        keep me
        */
    }
}
"""
    update = {
        "requirements": [
            {
                "req_id": "RQ_BAT_001",
                "catia_doc_append": "_verification_PASS\n_go_to_verification\nnew",
            }
        ]
    }
    out = patch_sysml_docs(source, update)
    assert "_verification_PASS" in out
    assert "old" not in out.split("RQ_OTHER")[0]
    assert "keep me" in out
    assert "NAMESPACE RAIZ SEPARADO" in out or "namespace" in out.lower()
