"""Geração de SysML V2 textual a partir de um RequirementRecord."""

from __future__ import annotations

import re

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import RangeCriteria, ThresholdCriteria

from reqvallive.eval.live import constraint_text, metric_name


def _safe_id(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", text)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"R_{cleaned}"
    return cleaned or "Requirement"


def generate_sysml(req: RequirementRecord, mqtt_topic: str) -> str:
    req_name = _safe_id(req.req_id)
    metric = metric_name(req)
    attr = _camel_metric(metric)
    constraint = _sysml_constraint(req, attr)
    unit = getattr(req.success_criteria, "unit", None) or ""
    unit_comment = f" // {unit}" if unit else ""

    return f"""package ReqValLive_{req_name} {{
    private import ScalarValues::*;

    doc /*
        Gerado automaticamente pelo ReqValLive.
        req_id: {req.req_id}
        MQTT topic: {mqtt_topic}
        Colar no Textual Editor do CATIA Magic (referência textual).
    */

    requirement def {req_name} {{
        doc /* {req.text} */
        attribute currentValue : Real;
        attribute metricName : String = "{metric}";
        require constraint {{
            {constraint}
        }}
    }}

    part def MissionValidator {{
        attribute {attr} : Real := 100.0;{unit_comment}
        attribute mqttTopic : String = "{mqtt_topic}";

        satisfy requirement batteryReq : {req_name} {{
            :>> currentValue = {attr};
        }}
    }}

    part missionValidation {{
        part validator : MissionValidator;
    }}
}}
"""


def _camel_metric(metric: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", metric)
    parts = [p for p in parts if p]
    if not parts:
        return "metricValue"
    head, *tail = parts
    return head.lower() + "".join(p.capitalize() for p in tail)


def _sysml_constraint(req: RequirementRecord, attr: str) -> str:
    sc = req.success_criteria
    if isinstance(sc, ThresholdCriteria):
        op = sc.operator.value if hasattr(sc.operator, "value") else str(sc.operator)
        return f"currentValue {op} {sc.value}"
    if isinstance(sc, RangeCriteria):
        return f"currentValue >= {sc.min_value} and currentValue <= {sc.max_value}"
    # fallback textual
    return constraint_text(req).replace("metricValue", "currentValue")
