"""Geração de SysML V2 textual (single ou multi-requisito)."""

from __future__ import annotations

import re

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import RangeCriteria, ThresholdCriteria

from reqvallive.eval.live import constraint_text, metric_name
from reqvallive.metrics.registry import metric_source_hint


def _safe_id(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", text)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"R_{cleaned}"
    return cleaned or "Requirement"


def _camel_metric(metric: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", metric)
    parts = [p for p in parts if p]
    if not parts:
        return "metricValue"
    head, *tail = parts
    return head.lower() + "".join(p.capitalize() for p in tail)


def generate_sysml(req: RequirementRecord, mqtt_topic: str) -> str:
    return generate_sysml_multi([req], mqtt_topic)


def generate_sysml_multi(requirements: list[RequirementRecord], mqtt_topic: str) -> str:
    if not requirements:
        raise ValueError("Lista de requisitos vazia")

    pkg = _safe_id(requirements[0].req_id)
    blocks: list[str] = []
    satisfy_blocks: list[str] = []
    verify_lines: list[str] = []

    for req in requirements:
        req_name = _safe_id(req.req_id)
        metric = metric_name(req)
        attr = _camel_metric(metric)
        unit = getattr(req.success_criteria, "unit", None) or ""
        unit_comment = f" // {unit}" if unit else ""
        sc = req.success_criteria
        doc_text = req.text.replace("*/", "* /")

        if isinstance(sc, ThresholdCriteria):
            op = sc.operator.value if hasattr(sc.operator, "value") else str(sc.operator)
            req_body = f"""
        attribute thresholdValue : Real = {sc.value};{unit_comment}
        attribute actualValue : Real;{unit_comment}
        attribute metricName : String = "{metric}";
        require constraint {{
            actualValue {op} thresholdValue
        }}"""
            satisfy = f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> thresholdValue = {sc.value};
        }}"""
        elif isinstance(sc, RangeCriteria):
            req_body = f"""
        attribute minValue : Real = {sc.min_value};{unit_comment}
        attribute maxValue : Real = {sc.max_value};{unit_comment}
        attribute actualValue : Real;{unit_comment}
        attribute metricName : String = "{metric}";
        require constraint {{
            actualValue >= minValue and actualValue <= maxValue
        }}"""
            satisfy = f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> minValue = {sc.min_value};
            :>> maxValue = {sc.max_value};
        }}"""
        else:
            constraint = constraint_text(req).replace("metricValue", "actualValue")
            req_body = f"""
        attribute actualValue : Real;
        attribute metricName : String = "{metric}";
        require constraint {{
            {constraint}
        }}"""
            satisfy = f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
        }}"""

        blocks.append(
            f"""
    requirement def {req_name} {{
        doc /* {doc_text} */
        subject s : SystemUnderTest;
{req_body}
    }}"""
        )
        satisfy_blocks.append(satisfy)
        verify_lines.append(f"            verify {req_name};")

        # attribute on part
        satisfy_blocks.insert(
            0 if len(satisfy_blocks) == 1 else len(satisfy_blocks) - 1,
            f"\n        attribute {attr} : Real := 0.0;{unit_comment}"
            f"\n        // {metric_source_hint(metric)}",
        )

    # Fix attribute ordering: collect unique attrs first
    attr_lines: list[str] = []
    seen_attrs: set[str] = set()
    sat_only: list[str] = []
    for req in requirements:
        metric = metric_name(req)
        attr = _camel_metric(metric)
        if attr not in seen_attrs:
            seen_attrs.add(attr)
            unit = getattr(req.success_criteria, "unit", None) or ""
            unit_comment = f" // {unit}" if unit else ""
            attr_lines.append(
                f"        attribute {attr} : Real := 0.0;{unit_comment}\n"
                f"        // {metric_source_hint(metric)}"
            )
        # regenerate satisfy cleanly
    sat_only = []
    for req in requirements:
        req_name = _safe_id(req.req_id)
        metric = metric_name(req)
        attr = _camel_metric(metric)
        sc = req.success_criteria
        if isinstance(sc, ThresholdCriteria):
            sat_only.append(
                f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> thresholdValue = {sc.value};
        }}"""
            )
        elif isinstance(sc, RangeCriteria):
            sat_only.append(
                f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> minValue = {sc.min_value};
            :>> maxValue = {sc.max_value};
        }}"""
            )
        else:
            sat_only.append(
                f"""
        satisfy requirement satisfy_{req_name} : {req_name} {{
            :>> actualValue = {attr};
        }}"""
            )

    hints = ", ".join(metric_name(r) for r in requirements)

    return f"""package ReqValLive_{pkg} {{
    private import ScalarValues::*;

    doc /*
        Gerado pelo ReqValLive (+ LLM opcional).
        MQTT topic: {mqtt_topic}
        Métricas: {hints}
        Suporta múltiplos drones (instances) no runtime da ferramenta.
        Colar no Textual Editor do CATIA Magic.
    */
{''.join(blocks)}

    part def SystemUnderTest {{
        attribute mqttTopic : String = "{mqtt_topic}";
        attribute droneName : String;
{chr(10).join(attr_lines)}
{''.join(sat_only)}
    }}

    verification def VerifyMission {{
        subject systemUnderTest : SystemUnderTest;
        objective {{
            doc /* Verificar requisitos da missão */
{chr(10).join(verify_lines)}
        }}
    }}

    part missionValidation {{
        part droneA : SystemUnderTest;
        part droneB : SystemUnderTest;
        part droneC : SystemUnderTest;
        verification case testCase : VerifyMission;
    }}

    view SolutionArchitecture : DS_Views::SymbolicViews::gv;
}}
"""
