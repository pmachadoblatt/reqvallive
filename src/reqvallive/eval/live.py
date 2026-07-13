"""Avaliação ao vivo de threshold/range contra um valor amostrado."""

from __future__ import annotations

from dataclasses import dataclass

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import (
    Operator,
    RangeCriteria,
    ThresholdCriteria,
)


@dataclass
class LiveVerdict:
    ok: bool
    supported: bool
    detail: str
    value: float | None = None


def criteria_type(req: RequirementRecord) -> str:
    return getattr(req.success_criteria, "type", type(req.success_criteria).__name__)


def metric_name(req: RequirementRecord) -> str:
    return str(req.success_criteria.metric)


def is_mvp_supported(req: RequirementRecord) -> bool:
    sc = req.success_criteria
    if not isinstance(sc, (ThresholdCriteria, RangeCriteria)):
        return False
    from reqvallive.metrics.registry import is_live_supported

    return is_live_supported(sc.metric)


def evaluate_value(req: RequirementRecord, value: float) -> LiveVerdict:
    sc = req.success_criteria

    if isinstance(sc, ThresholdCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        tolerance = sc.tolerance or 0.0
        observed = value
        if op in (Operator.GTE, Operator.GT):
            observed = value + tolerance
        elif op in (Operator.LTE, Operator.LT):
            observed = value - tolerance
        elif op == Operator.EQ:
            passed = abs(value - sc.value) <= tolerance
            return LiveVerdict(
                ok=passed,
                supported=True,
                detail=f"{value} == {sc.value} (±{tolerance})",
                value=value,
            )
        elif op == Operator.NEQ:
            passed = abs(value - sc.value) > tolerance
            return LiveVerdict(
                ok=passed,
                supported=True,
                detail=f"{value} != {sc.value} (±{tolerance})",
                value=value,
            )
        passed = op.evaluate(observed, float(sc.value))
        return LiveVerdict(
            ok=passed,
            supported=True,
            detail=f"{value} {op.value} {sc.value}",
            value=value,
        )

    if isinstance(sc, RangeCriteria):
        lo = float(sc.min_value)
        hi = float(sc.max_value)
        if sc.inclusive_min is False:
            low_ok = value > lo
        else:
            low_ok = value >= lo
        if sc.inclusive_max is False:
            high_ok = value < hi
        else:
            high_ok = value <= hi
        passed = low_ok and high_ok
        return LiveVerdict(
            ok=passed,
            supported=True,
            detail=f"{lo} .. {hi} contém {value}",
            value=value,
        )

    return LiveVerdict(
        ok=False,
        supported=False,
        detail=f"Critério '{type(sc).__name__}' não suportado no MVP live",
        value=value,
    )


def constraint_text(req: RequirementRecord) -> str:
    sc = req.success_criteria
    if isinstance(sc, ThresholdCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        return f"metricValue {op.value} {sc.value}"
    if isinstance(sc, RangeCriteria):
        return f"metricValue >= {sc.min_value} and metricValue <= {sc.max_value}"
    return "true /* critério não suportado no MVP */"
