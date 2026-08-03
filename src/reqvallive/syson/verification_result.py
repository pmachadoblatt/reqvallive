"""Bloco VerificationResult no SysON — evidência ligada ao requirement."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


VR_ITEM_NAME = "VerificationResult"


def _esc(s: Any) -> str:
    text = str(s if s is not None else "").replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:400]


def _iso(ts: float | None) -> str:
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
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
    """Nome visível no explorador SysON — PASS/FAIL no 2º segmento (sem abrir o item)."""
    status = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("status") or "NA")) or "NA"
    parts = [VR_ITEM_NAME, status]
    sc_type = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("scType") or ""))[:12]
    if sc_type:
        parts.append(sc_type)
    ek = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("extremeKind") or ""))
    ev = fields.get("extremeValue")
    if ek and ev is not None:
        try:
            num = f"{float(ev):g}".replace(".", "p").replace("-", "m")
        except (TypeError, ValueError):
            num = "x"
        parts.append(f"{ek}{num}")
    metric = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("metric") or ""))[:24]
    if metric:
        parts.append(metric)
    sid = re.sub(r"[^A-Za-z0-9]", "", str(fields.get("sessionId") or ""))[:8]
    if sid:
        parts.append(sid)
    return "_".join(parts)[:80]


def verification_result_doc_body(fields: dict[str, Any]) -> str:
    """Texto no Documentation do item — legível ao seleccionar no SysON."""
    lines = [
        f"status: {fields.get('status') or ''}",
        f"scType: {fields.get('scType') or ''}",
        f"metric: {fields.get('metric') or ''}",
        f"expected: {fields.get('expected') or ''}",
    ]
    if fields.get("failedAt"):
        lines.append(f"failedAt: {fields['failedAt']}")
    if fields.get("extremeValue") is not None and fields.get("extremeKind"):
        unit = f" {fields['unit']}" if fields.get("unit") else ""
        lines.append(
            f"extreme: {fields['extremeKind']}={fields['extremeValue']}{unit}"
        )
    if fields.get("reason"):
        lines.append(f"reason: {fields['reason']}")
    if fields.get("evidenceSummary"):
        lines.append(f"evidence: {fields['evidenceSummary']}")
    if fields.get("sessionId"):
        lines.append(f"sessionId: {fields['sessionId']}")
    if fields.get("measuredAt"):
        lines.append(f"measuredAt: {fields['measuredAt']}")
    # doc /* */ não gosta de */
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

    # LLM pode já ter preenchido reason / evidenceSummary
    reason = str(req_update.get("syson_reason") or why or status)
    evidence = str(req_update.get("syson_evidence_summary") or "")

    failed_at = ""
    extreme_value: float | None = None
    extreme_kind = ""
    unit = ""

    entities = finding.get("entities") or []
    if status == "FAIL" and entities:
        # Escolhe a 1ª falha mais cedo; extreme = min (threshold baixo) ou valor da 1ª falha
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
        # Em PASS: regista extremo observado (útil p/ bateria = min)
        mins = [float(e["min"]) for e in entities if e.get("min") is not None]
        maxs = [float(e["max"]) for e in entities if e.get("max") is not None]
        if mins:
            extreme_value = min(mins)
            extreme_kind = "min"
        elif maxs:
            extreme_value = max(maxs)
            extreme_kind = "max"

    # unit / scType a partir do SC
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
            bits.append(f"falhou em {failed_at}")
        if extreme_value is not None and extreme_kind:
            bits.append(f"{extreme_kind}={extreme_value:g}{(' ' + unit) if unit else ''}")
        if expected:
            bits.append(f"esperado {expected}")
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
        "itemName": "",  # preenchido abaixo
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
    order = [
        "status",
        "scType",
        "metric",
        "expected",
        "reason",
        "evidenceSummary",
        "failedAt",
        "extremeValue",
        "extremeKind",
        "unit",
        "sessionId",
        "measuredAt",
    ]
    for key in order:
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
