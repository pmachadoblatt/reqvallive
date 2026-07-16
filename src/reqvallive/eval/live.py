"""Avaliação ao vivo de threshold/range/statistical (window aggregations)."""

from __future__ import annotations

from dataclasses import dataclass

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import (
    Aggregation,
    Operator,
    RangeCriteria,
    StatisticalCriteria,
    ThresholdCriteria,
)

# Agregações sobre a janela de medição (sem inventar métricas MQTT novas).
LIVE_WINDOW_AGGREGATIONS = frozenset(
    {
        Aggregation.RANGE,
        Aggregation.MAX,
        Aggregation.MIN,
        "range",
        "max",
        "min",
    }
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


def _agg_value(aggregation: Aggregation | str) -> str:
    if isinstance(aggregation, Aggregation):
        return aggregation.value
    return str(aggregation).lower()


def is_window_statistical(req: RequirementRecord) -> bool:
    sc = req.success_criteria
    if not isinstance(sc, StatisticalCriteria):
        return False
    return _agg_value(sc.aggregation) in {"range", "max", "min"}


def is_mvp_supported(req: RequirementRecord) -> bool:
    """Live MVP: threshold/range + statistical window (range/max/min) sobre métrica MQTT."""
    sc = req.success_criteria
    from reqvallive.metrics.registry import is_live_supported

    if isinstance(sc, (ThresholdCriteria, RangeCriteria)):
        return is_live_supported(sc.metric)
    if isinstance(sc, StatisticalCriteria) and is_window_statistical(req):
        return is_live_supported(sc.metric)
    return False


def window_observed(
    aggregation: Aggregation | str,
    sample_min: float,
    sample_max: float,
) -> float:
    """Valor agregado na janela a partir dos extremos da série da métrica MQTT."""
    key = _agg_value(aggregation)
    if key == "range":
        return sample_max - sample_min
    if key == "max":
        return sample_max
    if key == "min":
        return sample_min
    raise ValueError(f"Agregação live não suportada: {aggregation}")


def _eval_operator(
    op: Operator,
    observed: float,
    expected: float,
    tolerance: float = 0.0,
) -> tuple[bool, str]:
    if op in (Operator.GTE, Operator.GT):
        cmp_obs = observed + tolerance
    elif op in (Operator.LTE, Operator.LT):
        cmp_obs = observed - tolerance
    elif op == Operator.EQ:
        passed = abs(observed - expected) <= tolerance
        return passed, f"{observed:g} == {expected:g} (±{tolerance:g})"
    elif op == Operator.NEQ:
        passed = abs(observed - expected) > tolerance
        return passed, f"{observed:g} != {expected:g} (±{tolerance:g})"
    else:
        cmp_obs = observed
    passed = op.evaluate(cmp_obs, float(expected))
    return passed, f"{observed:g} {op.value} {expected:g}"


def evaluate_value(req: RequirementRecord, value: float) -> LiveVerdict:
    """Avalia um valor já resolvido (amostra instantânea ou agregado de janela)."""
    sc = req.success_criteria

    if isinstance(sc, ThresholdCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        tolerance = sc.tolerance or 0.0
        passed, detail = _eval_operator(op, value, float(sc.value), tolerance)
        return LiveVerdict(ok=passed, supported=True, detail=detail, value=value)

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

    if isinstance(sc, StatisticalCriteria) and is_window_statistical(req):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        agg = _agg_value(sc.aggregation)
        passed, detail = _eval_operator(op, value, float(sc.value), 0.0)
        return LiveVerdict(
            ok=passed,
            supported=True,
            detail=f"{agg}({sc.metric})={detail}",
            value=value,
        )

    return LiveVerdict(
        ok=False,
        supported=False,
        detail=f"Critério '{type(sc).__name__}' não suportado no MVP live",
        value=value,
    )


def evaluate_sample(
    req: RequirementRecord,
    sample: float,
    sample_min: float | None = None,
    sample_max: float | None = None,
) -> LiveVerdict:
    """Avalia uma amostra; para statistical window usa min/max da série."""
    if is_window_statistical(req):
        sc = req.success_criteria
        assert isinstance(sc, StatisticalCriteria)
        lo = sample if sample_min is None else sample_min
        hi = sample if sample_max is None else sample_max
        observed = window_observed(sc.aggregation, lo, hi)
        return evaluate_value(req, observed)
    return evaluate_value(req, sample)


def constraint_text(req: RequirementRecord) -> str:
    sc = req.success_criteria
    if isinstance(sc, ThresholdCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        return f"metricValue {op.value} {sc.value}"
    if isinstance(sc, RangeCriteria):
        return f"metricValue >= {sc.min_value} and metricValue <= {sc.max_value}"
    if isinstance(sc, StatisticalCriteria) and is_window_statistical(req):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        agg = _agg_value(sc.aggregation)
        return f"{agg}(metricValue) {op.value} {sc.value}"
    return "true /* critério não suportado no MVP */"
