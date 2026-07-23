"""Geração do artefato de UPDATE para o CATIA após a medição."""

from __future__ import annotations

import time
from typing import Any

from reqvallive.eval.live import metric_name
from reqvallive.models.session import MeasurementSession


def build_verification_update(session: MeasurementSession) -> dict[str, Any]:
    """Monta o pacote de verificação a partir da evidência live (sem LLM)."""
    findings = session.findings()
    gate = session.validation_status() if hasattr(session, "validation_status") else {}
    overall = session.overall_ok()
    if overall is True:
        overall_tag = "_verification_PASS"
    elif overall is False:
        overall_tag = "_verification_FAIL"
    else:
        overall_tag = "_verification_INCONCLUSIVE"

    req_updates = []
    for req in session.active_requirements():
        rid = req.req_id
        finding = next((f for f in findings if f.get("req_id") == rid), None)
        ok = finding.get("ok") if finding else None
        if ok is True:
            tag = "_verification_PASS"
        elif ok is False:
            tag = "_verification_FAIL"
        else:
            tag = "_verification_INCONCLUSIVE"

        entities = finding.get("entities") if finding else []
        evidence_lines = []
        for e in entities or []:
            evidence_lines.append(
                f"- {e.get('id')}: last={e.get('last')} min={e.get('min')} max={e.get('max')} "
                f"1st_fail={e.get('first_fail')} falhas={e.get('fail_count')}/{e.get('sample_count')}"
            )
        if finding and finding.get("scope") == "global":
            evidence_lines.append(
                f"- global actual={finding.get('actual')} detail={finding.get('detail')}"
            )

        doc_block = (
            f"{tag}\n"
            f"_go_to_verification\n"
            f"session: {session.id}\n"
            f"measured_at_end: {session.ended_at}\n"
            f"metric: {metric_name(req)}\n"
            f"expected: {finding.get('expected') if finding else ''}\n"
            f"why: {finding.get('why') if finding else ''}\n"
            "evidence:\n"
            + ("\n".join(evidence_lines) if evidence_lines else "- (sem amostras)")
        )

        req_updates.append(
            {
                "req_id": rid,
                "title": req.title,
                "verification_tag": tag,
                "ok": ok,
                "metric": metric_name(req),
                "expected": finding.get("expected") if finding else None,
                "why": finding.get("why") if finding else None,
                "catia_doc_append": doc_block,
                "sysml_doc_snippet": (
                    f"requirement {rid} {{\n"
                    f"  doc /*\n{doc_block}\n  */\n"
                    f"}}"
                ),
            }
        )

    return {
        "generated_at": time.time(),
        "session_id": session.id,
        "overall_ok": overall,
        "overall_tag": overall_tag,
        "measurement": {
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "mqtt_broker": session.mqtt_broker,
            "mqtt_topic": session.mqtt_topic,
            "drone_count": len(session.drones),
            "message_count": session.message_count,
        },
        "gate_before_measure": gate,
        "approved_sc_snapshot": session.approved_sc_snapshot,
        "gse_config": session.gse_config,
        "requirements": req_updates,
        "instructions_pt": (
            "1) Abra o requisito correspondente no CATIA Magic.\n"
            "2) No campo Documentation / doc, acrescente o bloco catia_doc_append "
            "(ou substitua o trecho de verificação anterior).\n"
            "3) Mantenha a tag _go_to_verification se quiser re-medir depois.\n"
            "4) Opcional: use sysml_doc_snippet no export textual."
        ),
        "llm_enrichment": None,
    }
