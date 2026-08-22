"""Bloco VerificationResult no SysON — evidência ligada ao requirement."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


VR_ITEM_NAME = "VerificationResult"

# Atributos expostos no SysON (resto fica só no Documentation legível).
_SYSML_ATTRIBUTES = ("status", "sessionId", "failedAt", "extremeValue", "unit")


def _esc(s: Any) -> str:
    text = str(s if s is not None else "").replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:400]


def _iso(ts: float | None) -> str:
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (TypeError, ValueError, OSError):
        return ""


def status_from_ok(ok: bool | None) -> str:
    if ok is True:
        return "PASS"
    if ok is False:
        return "FAIL"
    return "INCONCLUSIVE"


def is_verification_result_name(name: str) -> bool:
    n = (name or "").strip()
    return n == VR_ITEM_NAME or n.startswith(VR_ITEM_NAME + "_")


def verification_result_item_name(fields: dict[str, Any]) -> str:
    """Nome curto no explorador — o requisito pai já dá o contexto (RQ_BAT_001, …)."""
    status = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("status") or "NA")) or "NA"
    return f"{VR_ITEM_NAME}_{status}"


def _human_extreme(fields: dict[str, Any]) -> str:
    ev = fields.get("extremeValue")
    if ev is None:
        return ""
    unit = str(fields.get("unit") or "").strip()
    u = f" {unit}" if unit else ""
    kind = str(fields.get("extremeKind") or "value")
    if kind == "min":
        return f"Minimum during run: {ev:g}{u}"
    if kind == "max":
        return f"Maximum during run: {ev:g}{u}"
    if kind == "first_fail":
        return f"Value at first violation: {ev:g}{u}"
    return f"Observed extreme: {ev:g}{u}"


def verification_result_doc_body(fields: dict[str, Any]) -> str:
    """Documentation do item — texto para leitura humana (bater o olho)."""
    status = str(fields.get("status") or "?")
    metric = str(fields.get("metric") or "").strip()
    expected = str(fields.get("expected") or "").strip()

    lines: list[str] = [f"=== {status} ===", ""]

    if metric and expected:
        lines.append(f"Criterion: {metric}")
        lines.append(f"Expected: {expected}")
    elif expected:
        lines.append(f"Expected: {expected}")
    elif metric:
        lines.append(f"Metric: {metric}")

    lines.append("")

    if status == "FAIL":
        if fields.get("failedAt"):
            lines.append(f"When: first violation at {fields['failedAt']}")
        extreme = _human_extreme(fields)
        if extreme:
            lines.append(extreme)
    elif status == "PASS":
        extreme = _human_extreme(fields)
        if extreme:
            lines.append(extreme)
        else:
            lines.append("All samples met the criterion during the run.")

    reason = str(fields.get("reason") or "").strip()
    if reason and reason.upper() not in (status, "PASS", "FAIL", "INCONCLUSIVE"):
        lines.append("")
        lines.append(f"Detail: {reason}")

    if fields.get("sessionId"):
        lines.append("")
        lines.append(f"ReqValLive session: {fields['sessionId']}")

    if fields.get("measuredAt"):
        lines.append(f"Measurement ended: {fields['measuredAt']}")

    return "\n".join(lines).replace("*/", "* /")


def build_verification_result_fields(
    req_update: dict[str, Any],
    *,
    finding: dict[str, Any] | None = None,
    session_id: str = "",
    measured_at: float | None = None,
) -> dict[str, Any]:
    """Campos estruturados do item VerificationResult (independente do tipo de SC)."""
    finding = finding or {}
    ok = req_update.get("ok")
    if ok is None:
        ok = finding.get("ok")
    status = status_from_ok(ok if isinstance(ok, bool) else None)
    metric = str(req_update.get("metric") or finding.get("metric") or "")
    expected = str(req_update.get("expected") or finding.get("expected") or "")
    why = str(req_update.get("why") or finding.get("why") or "")

    reason = str(req_update.get("syson_reason") or why or status)
    evidence = str(req_update.get("syson_evidence_summary") or "")

    failed_at = ""
    extreme_value: float | None = None
    extreme_kind = ""
    unit = ""

    entities = finding.get("entities") or []
    if status == "FAIL" and entities:
        best = None
        for e in entities:
            ts = e.get("first_fail_ts")
            if ts is None:
                continue
            if best is None or float(ts) < float(best.get("first_fail_ts") or 1e99):
                best = e
        if best is None:
            best = entities[0]
        failed_at = _iso(best.get("first_fail_ts"))
        if best.get("id"):
            reason = f"{best['id']}: {why}" if why else str(best["id"])
        if best.get("min") is not None:
            extreme_value = float(best["min"])
            extreme_kind = "min"
        elif best.get("first_fail") is not None:
            extreme_value = float(best["first_fail"])
            extreme_kind = "first_fail"
        if best.get("max") is not None and extreme_kind == "":
            extreme_value = float(best["max"])
            extreme_kind = "max"
    elif status == "PASS" and entities:
        mins = [float(e["min"]) for e in entities if e.get("min") is not None]
        maxs = [float(e["max"]) for e in entities if e.get("max") is not None]
        if mins:
            extreme_value = min(mins)
            extreme_kind = "min"
        elif maxs:
            extreme_value = max(maxs)
            extreme_kind = "max"

    sc = req_update.get("success_criteria") or finding.get("success_criteria") or {}
    sc_type = ""
    if isinstance(sc, dict):
        unit = str(sc.get("unit") or "")
        sc_type = str(sc.get("type") or "")
    if not sc_type:
        sc_type = str(req_update.get("sc_type") or finding.get("sc_type") or "")

    if not evidence:
        bits = []
        if failed_at:
            bits.append(f"first violation at {failed_at}")
        if extreme_value is not None and extreme_kind:
            bits.append(f"{extreme_kind}={extreme_value:g}{(' ' + unit) if unit else ''}")
        if expected:
            bits.append(f"expected {expected}")
        evidence = "; ".join(bits) if bits else reason

    return {
        "status": status,
        "scType": sc_type,
        "metric": metric,
        "expected": expected,
        "reason": reason,
        "evidenceSummary": evidence,
        "failedAt": failed_at,
        "extremeValue": extreme_value,
        "extremeKind": extreme_kind,
        "unit": unit,
        "sessionId": session_id,
        "measuredAt": _iso(measured_at),
        "itemName": "",
    }


def _with_item_name(fields: dict[str, Any]) -> dict[str, Any]:
    out = dict(fields)
    out["itemName"] = verification_result_item_name(out)
    return out


def verification_result_textual(fields: dict[str, Any]) -> str:
    """SysML v2 textual para insertTextualSysMLv2 sob o requirement."""
    fields = _with_item_name(fields)
    item_name = fields["itemName"]
    doc = verification_result_doc_body(fields)
    lines = [
        f"item {item_name} {{",
        "    doc /*",
        *[f"    {ln}" if ln else "    " for ln in doc.splitlines()],
        "    */",
    ]
    for key in _SYSML_ATTRIBUTES:
        val = fields.get(key)
        if val is None or val == "":
            continue
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            lines.append(f"    attribute {key} = {val};")
        else:
            lines.append(f'    attribute {key} = "{_esc(val)}";')
    lines.append("}")
    return "\n".join(lines) + "\n"


def attach_verification_results_to_update(
    update: dict[str, Any],
    *,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Acrescenta syson_verification_result a cada requisito do pacote UPDATE."""
    findings = findings or []
    by_finding = {f.get("req_id"): f for f in findings}
    measured_at = (update.get("measurement") or {}).get("ended_at")
    session_id = str(update.get("session_id") or "")
    out = dict(update)
    reqs = []
    for req in update.get("requirements") or []:
        r = dict(req)
        fields = _with_item_name(
            build_verification_result_fields(
                r,
                finding=by_finding.get(r.get("req_id")),
                session_id=session_id,
                measured_at=measured_at,
            )
        )
        r["syson_verification_result"] = fields
        r["syson_verification_textual"] = verification_result_textual(fields)
        reqs.append(r)
    out["requirements"] = reqs
    return out
