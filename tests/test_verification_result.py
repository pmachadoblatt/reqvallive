"""VerificationResult textual builder."""

from reqvallive.syson.verification_result import (
    build_verification_result_fields,
    is_verification_result_name,
    verification_result_item_name,
    verification_result_textual,
)


def test_verification_result_textual_fail_battery():
    fields = build_verification_result_fields(
        {
            "ok": False,
            "metric": "batteryLevel",
            "expected": ">= 20.0",
            "why": "violação",
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
    assert fields["scType"] == "threshold"
    assert fields["extremeKind"] == "min"
    assert fields["extremeValue"] == 15.2
    assert fields["failedAt"]
    name = verification_result_item_name(fields)
    assert name.startswith("VerificationResult_FAIL_threshold_min15p2")
    assert "abc123" in name
    text = verification_result_textual(fields)
    assert f"item {name}" in text or "item VerificationResult_FAIL" in text
    assert "doc /*" in text
    assert "status: FAIL" in text
    assert "scType: threshold" in text
    assert 'status = "FAIL"' in text
    assert "extremeValue = 15.2" in text


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
    assert is_verification_result_name("VerificationResult_PASS_threshold_min55")
    assert not is_verification_result_name("SuccessCriteria")
    name = verification_result_item_name(fields)
    assert "PASS" in name
    assert "threshold" in name
