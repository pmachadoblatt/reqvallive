"""VerificationResult textual builder."""

from reqvallive.syson.verification_result import (
    build_verification_result_fields,
    is_verification_result_name,
    verification_result_doc_body,
    verification_result_item_name,
    verification_result_textual,
)


def test_verification_result_textual_fail_battery():
    fields = build_verification_result_fields(
        {
            "ok": False,
            "metric": "batteryLevel",
            "expected": ">= 20.0",
            "why": "below threshold",
            "success_criteria": {
                "type": "threshold",
                "metric": "batteryLevel",
                "unit": "percent",
            },
        },
        finding={
            "ok": False,
            "entities": [
                {
                    "id": "drone1",
                    "min": 15.2,
                    "first_fail": 15.2,
                    "first_fail_ts": 1720000000.0,
                }
            ],
        },
        session_id="abc123",
        measured_at=1720000100.0,
    )
    assert fields["status"] == "FAIL"
    assert fields["extremeValue"] == 15.2
    assert fields["failedAt"]
    name = verification_result_item_name(fields)
    assert name == "VerificationResult_FAIL"
    text = verification_result_textual(fields)
    assert f"item {name}" in text
    assert "doc /*" in text
    assert "=== FAIL ===" in verification_result_doc_body(fields)
    assert "Criterion: batteryLevel" in verification_result_doc_body(fields)
    assert 'status = "FAIL"' in text
    assert "extremeValue = 15.2" in text
    assert "scType" not in text
    assert 'attribute sessionId = "abc123"' in text


def test_verification_result_pass_has_min():
    fields = build_verification_result_fields(
        {
            "ok": True,
            "metric": "batteryLevel",
            "expected": ">= 20",
            "success_criteria": {"type": "threshold", "unit": "percent"},
        },
        finding={
            "ok": True,
            "entities": [{"id": "d1", "min": 55.0, "max": 80.0}],
        },
    )
    assert fields["status"] == "PASS"
    assert fields["extremeValue"] == 55.0
    assert is_verification_result_name("VerificationResult")
    assert is_verification_result_name("VerificationResult_PASS")
    assert is_verification_result_name("VerificationResult_FAIL_threshold_min55")
    assert not is_verification_result_name("SuccessCriteria")
    name = verification_result_item_name(fields)
    assert name == "VerificationResult_PASS"
    assert "=== PASS ===" in verification_result_doc_body(fields)
