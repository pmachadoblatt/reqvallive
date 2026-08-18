"""Avaliação ao vivo de threshold/range/statistical/rate/dwell."""

from __future__ import annotations

from dataclasses import dataclass

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import (
    Aggregation,
    DwellCriteria,
    Operator,
    RangeCriteria,
    RateCriteria,
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
    pending: bool = False
    dwell_since: float | None = None


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


def is_rate(req: RequirementRecord) -> bool:
    return isinstance(req.success_criteria, RateCriteria)


def is_dwell(req: RequirementRecord) -> bool:
    return isinstance(req.success_criteria, DwellCriteria)


def is_mvp_supported(req: RequirementRecord) -> bool:
    """Live: threshold/range/statistical window + Jefferson rate e dwell."""
    sc = req.success_criteria
    from reqvallive.metrics.registry import is_live_supported

    if isinstance(sc, (ThresholdCriteria, RangeCriteria, RateCriteria, DwellCriteria)):
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


def rate_unit_scale(unit: str | None) -> float:
    """Converte dV/dt em 1/s para a unidade do critério (×60 se for por minuto)."""
    u = (unit or "").lower().replace(" ", "")
    if "/min" in u or "permin" in u or "per_min" in u:
        return 60.0
    return 1.0


def observed_rate(
    prev_value: float,
    value: float,
    dt_s: float,
    unit: str | None,
    abs_rate: bool,
) -> float:
    if dt_s <= 0:
        raise ValueError("dt_s deve ser positivo")
    signed = ((value - prev_value) / dt_s) * rate_unit_scale(unit)
    return abs(signed) if abs_rate else signed


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
    """Avalia um valor já resolvido (amostra, agregado, taxa)."""
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

    if isinstance(sc, RateCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        passed, detail = _eval_operator(op, value, float(sc.value), 0.0)
        mag = "|" if sc.abs_rate else ""
        return LiveVerdict(
            ok=passed,
            supported=True,
            detail=f"{mag}d({sc.metric})/dt{mag} {detail} {sc.unit}",
            value=value,
        )

    if isinstance(sc, DwellCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        holds, detail = _eval_operator(op, value, float(sc.value), sc.tolerance or 0.0)
        return LiveVerdict(
            ok=not holds,
            supported=True,
            detail=f"condição ({detail}) {'activa' if holds else 'inactiva'}",
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
    *,
    prev_value: float | None = None,
    prev_ts: float | None = None,
    now: float | None = None,
    dwell_since: float | None = None,
) -> LiveVerdict:
    """Avalia uma amostra; rate/dwell usam histórico temporal opcional."""
    if is_window_statistical(req):
        sc = req.success_criteria
        assert isinstance(sc, StatisticalCriteria)
        lo = sample if sample_min is None else sample_min
        hi = sample if sample_max is None else sample_max
        observed = window_observed(sc.aggregation, lo, hi)
        return evaluate_value(req, observed)

    if is_rate(req):
        sc = req.success_criteria
        assert isinstance(sc, RateCriteria)
        if prev_value is None or prev_ts is None or now is None:
            return LiveVerdict(
                ok=True,
                supported=True,
                detail="à espera de segunda amostra para taxa",
                value=None,
                pending=True,
            )
        dt = now - prev_ts
        if dt < float(sc.min_dt_s):
            return LiveVerdict(
                ok=True,
                supported=True,
                detail=f"Δt={dt:g}s < min_dt {sc.min_dt_s:g}s",
                value=None,
                pending=True,
            )
        observed = observed_rate(prev_value, sample, dt, sc.unit, sc.abs_rate)
        return evaluate_value(req, observed)

    if is_dwell(req):
        sc = req.success_criteria
        assert isinstance(sc, DwellCriteria)
        ts = now if now is not None else 0.0
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        holds, cond_detail = _eval_operator(op, sample, float(sc.value), sc.tolerance or 0.0)
        if not holds:
            return LiveVerdict(
                ok=True,
                supported=True,
                detail=f"condição inactiva ({cond_detail})",
                value=sample,
                dwell_since=None,
            )
        since = dwell_since if dwell_since is not None else ts
        elapsed_ms = max(0.0, (ts - since) * 1000.0)
        limit = float(sc.max_duration_ms)
        passed = elapsed_ms < limit
        return LiveVerdict(
            ok=passed,
            supported=True,
            detail=(
                f"condição activa {elapsed_ms:g} ms "
                f"(máx. {limit:g} ms; {cond_detail})"
            ),
            value=sample,
            dwell_since=since,
        )

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
    if isinstance(sc, RateCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        mag = "|" if sc.abs_rate else ""
        return f"{mag}d(metricValue)/dt{mag} {op.value} {sc.value} {sc.unit}"
    if isinstance(sc, DwellCriteria):
        op = sc.operator if isinstance(sc.operator, Operator) else Operator(sc.operator)
        return (
            f"metricValue {op.value} {sc.value} por no máximo "
            f"{sc.max_duration_ms:g} ms"
        )
    return "true /* critério não suportado no MVP */"
