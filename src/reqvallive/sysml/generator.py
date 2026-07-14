"""Geração de SysML V2 textual a partir de um RequirementRecord."""

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
    req_name = _safe_id(req.req_id)
    metric = metric_name(req)
    attr = _camel_metric(metric)
    satisfy_name = f"satisfy_{req_name}"
    verification_name = f"Verify_{req_name}"
    unit = getattr(req.success_criteria, "unit", None) or ""
    unit_comment = f" // {unit}" if unit else ""
    hint = metric_source_hint(metric)
    sc = req.success_criteria

    if isinstance(sc, ThresholdCriteria):
        op = sc.operator.value if hasattr(sc.operator, "value") else str(sc.operator)
        threshold_attrs = f"""
        attribute thresholdValue : Real = {sc.value};{unit_comment}
        attribute actualValue : Real;{unit_comment}
        attribute metricName : String = "{metric}";
        require constraint {{
            actualValue {op} thresholdValue
        }}"""
        satisfy_bind = f"""
        satisfy requirement {satisfy_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> thresholdValue = {sc.value};
        }}"""
    elif isinstance(sc, RangeCriteria):
        threshold_attrs = f"""
        attribute minValue : Real = {sc.min_value};{unit_comment}
        attribute maxValue : Real = {sc.max_value};{unit_comment}
        attribute actualValue : Real;{unit_comment}
        attribute metricName : String = "{metric}";
        require constraint {{
            actualValue >= minValue and actualValue <= maxValue
        }}"""
        satisfy_bind = f"""
        satisfy requirement {satisfy_name} : {req_name} {{
            :>> actualValue = {attr};
            :>> minValue = {sc.min_value};
            :>> maxValue = {sc.max_value};
        }}"""
    else:
        constraint = constraint_text(req).replace("metricValue", "actualValue")
        threshold_attrs = f"""
        attribute actualValue : Real;
        attribute metricName : String = "{metric}";
        require constraint {{
            {constraint}
        }}"""
        satisfy_bind = f"""
        satisfy requirement {satisfy_name} : {req_name} {{
            :>> actualValue = {attr};
        }}"""

    doc_text = req.text.replace("*/", "* /")

    return f"""package ReqValLive_{req_name} {{
    private import ScalarValues::*;

    doc /*
        Gerado automaticamente pelo ReqValLive.
        req_id: {req.req_id}
        title: {req.title}
        MQTT topic: {mqtt_topic}
        Métrica MQTT: {hint}
        Colar no Textual Editor do CATIA Magic (referência textual).
    */

    requirement def {req_name} {{
        doc /* {doc_text} */
        subject s : SystemUnderTest;
{threshold_attrs}
    }}

    part def SystemUnderTest {{
        attribute {attr} : Real := 0.0;{unit_comment}
        attribute mqttTopic : String = "{mqtt_topic}";
{satisfy_bind}
    }}

    verification def {verification_name} {{
        subject systemUnderTest : SystemUnderTest;
        objective {{
            doc /* Verificar {req.req_id}: {req.title} */
            verify {req_name};
        }}
    }}

    part missionValidation {{
        part systemUnderTest : SystemUnderTest;
        verification case testCase : {verification_name} {{
            subject systemUnderTest = systemUnderTest;
        }}
    }}

    view SolutionArchitecture : DS_Views::SymbolicViews::gv {{
        // Vista de referência: part + requirement + satisfy + verification
    }}
}}
"""
