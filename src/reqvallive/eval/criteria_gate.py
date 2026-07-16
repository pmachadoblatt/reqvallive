"""Gate de aceite/recusa de Success Criteria (antes da medição MQTT).

Alinhado a SIS-08 Methods (Cerqueira) / MSFC-HDBK-3173:
- Success Criteria são critérios detalhados e específicos, aprováveis *antes*
  da actividade de V&V.
- Checklist (ao definir SC): Performance, Environment Test Limits, Tolerances,
  Margins, Specifications, Restrictions, Checkpoints, Effectiveness/localization.
- Coerência obrigatória Method × Success (critério de nota do assignment).
- Requisitos devem ser verificáveis como escritos.

No ReqValLive, ACCEPT significa «aprovado para medição live MQTT»;
REJECT bloqueia /start (e, na UI, MQTT) com motivos e sugestões.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.success_criteria import (
    Aggregation,
    RangeCriteria,
    StatisticalCriteria,
    ThresholdCriteria,
)
from simreqvalidator.schema.vv_method import VVMethod

from reqvallive.metrics.registry import BATTERY_ALIASES, DISTANCE_METRICS


class GateStatus(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class ReasonSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class MsfcDimension(str, Enum):
    """As 8 considerações MSFC ao desenvolver Success Criteria (+ Method)."""

    PERFORMANCE = "performance_criteria"
    ENVIRONMENT = "environment_test_limits"
    TOLERANCES = "tolerances"
    MARGINS = "margins"
    SPECIFICATIONS = "specifications"
    RESTRICTIONS = "restrictions"
    CHECKPOINTS = "checkpoints"
    EFFECTIVENESS_LOCALIZATION = "effectiveness_and_localization"
    METHOD_COHERENCE = "method_x_success"
    LIVE_EXECUTABLE = "live_executable"


# Métricas reconhecidas no payload / agregações do lab (telemetria)
KNOWN_TELEMETRY_METRICS = frozenset(
    {
        *BATTERY_ALIASES,
        *DISTANCE_METRICS,
        "altitudeAGL",
        "altitude",
        "altitude_m",
        "distanceToHome",
        "speed_horizontal",
        "speed.horizontal",
        "satelliteCount",
        "remainingFlightTime",
        "timeNeededToGoHome",
        "timeNeededToLand",
        "batteryNeededToGoHome",
        "maxRadiusCanFlyAndGoHome",
        "seriousLowBatteryThreshold",
    }
)

# Agregações estatísticas executáveis na janela de medição MQTT (sobre a métrica telemetria)
LIVE_WINDOW_AGGREGATIONS = frozenset({"range", "max", "min"})

# Métodos que NÃO produzem evidência por amostragem MQTT contínua (Methods slides)
NON_LIVE_METHODS = frozenset(
    {
        VVMethod.INSPECTION,
        VVMethod.ANALYSIS,
        VVMethod.SIMILARITY,
        VVMethod.REVIEW_OF_DESIGN,
    }
)

# MVP: só Test é aceite para medição live (Demo fica backlog / aviso)
LIVE_OK_METHODS = frozenset({VVMethod.TEST})

_VAGUE_PATTERNS = (
    r"\badequado\b",
    r"\bbom desempenho\b",
    r"\bsuficiente\b",
    r"\baceit[aá]vel\b",
    r"\bratisfat[oó]rio\b",
    r"\bapropriado\b",
    r"\bde qualidade\b",
    r"\bas needed\b",
    r"\bas required\b",
    r"\bproperly\b",
    r"\badequate\b",
    r"\bsufficient\b",
    r"\bgood performance\b",
)

_TEMPORAL_WHOLE_MISSION = re.compile(
    r"(toda a (opera[cç][aã]o|miss[aã]o)|durante todo|all timesteps|"
    r"throughout the (mission|operation))",
    re.I,
)

_PERCENTILE = re.compile(r"percentil|percentile|p95|p99|\bmean\b|\bm[eé]dia\b", re.I)


@dataclass
class GateReason:
    code: str
    severity: ReasonSeverity
    message: str
    dimension: MsfcDimension
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "dimension": self.dimension.value,
            "suggestion": self.suggestion,
        }


@dataclass
class CriteriaGateResult:
    req_id: str
    status: GateStatus
    reasons: list[GateReason] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    method_coherence: str = "ok"  # ok | fail
    live_executable: bool = False
    vv_method: str | None = None
    metric: str | None = None
    criteria_type: str | None = None

    @property
    def errors(self) -> list[GateReason]:
        return [r for r in self.reasons if r.severity == ReasonSeverity.ERROR]

    @property
    def warnings(self) -> list[GateReason]:
        return [r for r in self.reasons if r.severity == ReasonSeverity.WARNING]

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "status": self.status.value,
            "reasons": [r.to_dict() for r in self.reasons],
            "suggestions": list(self.suggestions),
            "method_coherence": self.method_coherence,
            "live_executable": self.live_executable,
            "vv_method": self.vv_method,
            "metric": self.metric,
            "criteria_type": self.criteria_type,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


@dataclass
class SessionGateSummary:
    global_status: GateStatus
    results: list[CriteriaGateResult]
    evaluated_at: float
    accepted_count: int
    rejected_count: int
    warning_count: int
    theory_refs: list[str] = field(
        default_factory=lambda: [
            "SIS-08 Methods — Means of Compliance and Success Criteria (Cerqueira, 2025)",
            "MSFC-HDBK-3173 — Product Verification/Validation success criteria",
            "Assignment grading: Coherent Method × Success; verifiable as written",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_status": self.global_status.value,
            "results": [r.to_dict() for r in self.results],
            "evaluated_at": self.evaluated_at,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "warning_count": self.warning_count,
            "theory_refs": list(self.theory_refs),
            "can_start_measurement": self.global_status == GateStatus.ACCEPT,
        }


def _vv_value(req: RequirementRecord) -> str | None:
    m = req.vv_method
    if m is None:
        return None
    return m.value if isinstance(m, VVMethod) else str(m)


def _metric_needs_unit(metric: str) -> str | None:
    if metric in BATTERY_ALIASES or "battery" in metric.lower() or metric == "remainingCharge":
        return "percent"
    if metric in DISTANCE_METRICS or metric in (
        "distanceToHome",
        "altitudeAGL",
        "maxRadiusCanFlyAndGoHome",
    ):
        return "meters"
    if "speed" in metric.lower():
        return "m/s"
    if metric in ("remainingFlightTime", "timeNeededToGoHome", "timeNeededToLand"):
        return "seconds"
    return None


def _unit_ok(unit: str | None, expected_kind: str | None) -> bool:
    if not expected_kind:
        return True
    u = (unit or "").strip().lower()
    if not u:
        return False
    if expected_kind == "percent":
        return any(x in u for x in ("%", "percent", "pct"))
    if expected_kind == "meters":
        return any(x in u for x in ("m", "meter", "metre"))
    if expected_kind == "m/s":
        return any(x in u for x in ("m/s", "mps", "meter"))
    if expected_kind == "seconds":
        return any(x in u for x in ("s", "sec", "second", "min"))
    return True


def _text_not_measurable(text: str) -> bool:
    t = text or ""
    if any(re.search(p, t, re.I) for p in _VAGUE_PATTERNS):
        # ainda mensurável se tiver número + operador implícito no texto
        if re.search(r"\d+(\.\d+)?\s*%?", t) and re.search(
            r"[<>]=?|>=|<=|acima|abaixo|entre|mín|max|min", t, re.I
        ):
            return False
        return True
    return False


def _normalize_metric(metric: str) -> str:
    m = metric.strip()
    if m == "speed.horizontal":
        return "speed_horizontal"
    if m in ("altitude", "altitude_m", "alt"):
        return "altitudeAGL"
    return m


def _agg_name(aggregation: Aggregation | str | None) -> str:
    if aggregation is None:
        return ""
    if isinstance(aggregation, Aggregation):
        return aggregation.value
    return str(aggregation).lower().strip()


def _is_known_telemetry(metric: str) -> bool:
    return _normalize_metric(metric) in KNOWN_TELEMETRY_METRICS


def evaluate_requirement_criteria(req: RequirementRecord) -> CriteriaGateResult:
    """Avalia um requisito face ao gate de Success Criteria (teoria + live)."""
    reasons: list[GateReason] = []
    suggestions: list[str] = []
    method_coherence = "ok"
    live_executable = False
    metric: str | None = None
    ctype: str | None = None
    vv = _vv_value(req)

    # --- Specs / rastreabilidade (warnings) ---
    if not (req.conops_ref or "").strip() or (req.conops_ref or "").strip().upper() in (
        "CONOPS",
        "N/A",
        "-",
    ):
        reasons.append(
            GateReason(
                code="SC_CONOPS_MISSING",
                severity=ReasonSeverity.WARNING,
                message="Sem ligação clara a CONOPS/especificação (Specifications).",
                dimension=MsfcDimension.SPECIFICATIONS,
                suggestion="Preencha conops_ref com a secção do CONOPS (ex.: CONOPS-UTM §4.2).",
            )
        )
    if not (req.rationale or "").strip():
        reasons.append(
            GateReason(
                code="SC_RATIONALE_MISSING",
                severity=ReasonSeverity.WARNING,
                message="Rationale ausente — dificulta rastreio ao «porquê» do critério.",
                dimension=MsfcDimension.SPECIFICATIONS,
                suggestion="Acrescente rationale ligando o requisito à necessidade operacional.",
            )
        )

    if not (req.level or "").strip():
        reasons.append(
            GateReason(
                code="SC_LEVEL_MISSING",
                severity=ReasonSeverity.ERROR,
                message="Nível hierárquico (mission/system/subsystem/component) ausente.",
                dimension=MsfcDimension.EFFECTIVENESS_LOCALIZATION,
                suggestion="Indique level conforme a reorganização de níveis do assignment.",
            )
        )

    # --- Method ---
    if not vv:
        reasons.append(
            GateReason(
                code="VV_METHOD_MISSING",
                severity=ReasonSeverity.ERROR,
                message="vv_method ausente — não dá para verificar Method × Success.",
                dimension=MsfcDimension.METHOD_COHERENCE,
                suggestion="Defina vv_method (para medição MQTT live use «test»).",
            )
        )
        method_coherence = "fail"
    else:
        try:
            vv_enum = VVMethod(vv)
        except ValueError:
            vv_enum = None
            reasons.append(
                GateReason(
                    code="VV_METHOD_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message=f"vv_method «{vv}» não reconhecido nos métodos IADT/MSFC.",
                    dimension=MsfcDimension.METHOD_COHERENCE,
                    suggestion="Use inspection|analysis|demonstration|test|similarity|review_of_design.",
                )
            )
            method_coherence = "fail"
            vv_enum = None  # type: ignore

        if vv_enum is not None:
            if vv_enum in NON_LIVE_METHODS:
                reasons.append(
                    GateReason(
                        code="VV_METHOD_NOT_LIVE",
                        severity=ReasonSeverity.ERROR,
                        message=(
                            f"Método «{vv_enum.value}» não gera evidência por telemetria MQTT contínua "
                            "(Methods: Inspection/Analysis/Similarity/Review-of-design)."
                        ),
                        dimension=MsfcDimension.METHOD_COHERENCE,
                        suggestion=(
                            "Para esta ferramenta live use vv_method=test com limiar numérico; "
                            "ou retire o requisito da sessão de medição MQTT."
                        ),
                    )
                )
                method_coherence = "fail"
            elif vv_enum == VVMethod.DEMONSTRATION:
                reasons.append(
                    GateReason(
                        code="VV_METHOD_MISMATCH",
                        severity=ReasonSeverity.ERROR,
                        message=(
                            "Demonstration (Methods) é confirmação pass/fail sem data gathering denso; "
                            "o motor live faz amostragem contínua — MVP só aceita «test»."
                        ),
                        dimension=MsfcDimension.METHOD_COHERENCE,
                        suggestion="Altere vv_method para «test» se pretende limiares instrumentados via MQTT.",
                    )
                )
                method_coherence = "fail"
            elif vv_enum not in LIVE_OK_METHODS:
                reasons.append(
                    GateReason(
                        code="VV_METHOD_NOT_LIVE",
                        severity=ReasonSeverity.ERROR,
                        message=f"Método «{vv_enum.value}» fora do conjunto aceite para medição live (MVP: test).",
                        dimension=MsfcDimension.METHOD_COHERENCE,
                        suggestion="Use vv_method=test.",
                    )
                )
                method_coherence = "fail"

    # --- Success criteria / Performance ---
    sc = req.success_criteria
    if sc is None:
        reasons.append(
            GateReason(
                code="SC_MISSING",
                severity=ReasonSeverity.ERROR,
                message="success_criteria ausente — MSFC exige critérios detalhados e específicos.",
                dimension=MsfcDimension.PERFORMANCE,
                suggestion="Defina threshold ou range com metric, operador/limites, unit e scope.",
            )
        )
    elif isinstance(sc, ThresholdCriteria):
        ctype = "threshold"
        metric = _normalize_metric(str(sc.metric or ""))
        if not metric:
            reasons.append(
                GateReason(
                    code="SC_METRIC_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="Threshold sem metric (Performance criteria).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Indique a métrica MQTT (ex.: batteryLevel, min_separation_m).",
                )
            )
        try:
            op = sc.operator
            if op is None:
                raise ValueError("missing")
        except Exception:
            reasons.append(
                GateReason(
                    code="SC_OPERATOR_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="Threshold sem operador de comparação válido.",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Use um de: >=, <=, >, <, ==, !=.",
                )
            )
        if sc.value is None:
            reasons.append(
                GateReason(
                    code="SC_VALUE_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="Threshold sem value numérico.",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Defina o limiar (ex.: 20.0 para bateria ≥ 20%).",
                )
            )
        else:
            live_executable = True

        kind = _metric_needs_unit(metric) if metric else None
        if kind and not _unit_ok(sc.unit, kind):
            reasons.append(
                GateReason(
                    code="SC_UNIT_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message=f"Unidade ausente ou incoerente para «{metric}» (esperado: {kind}).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion=f"Preencha success_criteria.unit (ex.: {kind}).",
                )
            )

        # Tolerances / margins (warn; error se safety high sem tolerance definida como None)
        tol = sc.tolerance
        tags = {str(t).lower() for t in (req.tags or [])}
        is_safety = "safety" in tags or "segurança" in tags or (req.priority or "").lower() == "high"
        if tol is None or (is_safety and float(tol or 0) == 0.0 and "battery" in (metric or "").lower()):
            # aviso padrão; se high+safety e tolerancia 0 explícita ainda é warn (política MVP)
            if tol is None:
                reasons.append(
                    GateReason(
                        code="SC_TOLERANCE_MISSING",
                        severity=ReasonSeverity.WARNING,
                        message="Tolerância não definida (MSFC: Tolerances).",
                        dimension=MsfcDimension.TOLERANCES,
                        suggestion="Defina tolerance (pode ser 0.0 se o limiar for absoluto).",
                    )
                )
            elif is_safety:
                reasons.append(
                    GateReason(
                        code="SC_MARGIN_UNDEFINED",
                        severity=ReasonSeverity.WARNING,
                        message="Requisito de segurança/high com margem/tolerância nula — confirme se é intencional.",
                        dimension=MsfcDimension.MARGINS,
                        suggestion="Considere margin operacional (RTL, etc.) além do limiar nominal.",
                    )
                )

        scope = getattr(sc, "scope", None)
        if scope is None:
            reasons.append(
                GateReason(
                    code="SC_SCOPE_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="scope ausente (Restrictions / localization).",
                    dimension=MsfcDimension.RESTRICTIONS,
                    suggestion="Use all_entities, all_timesteps, etc.",
                )
            )
        else:
            scope_s = scope.value if hasattr(scope, "value") else str(scope)
            if metric in DISTANCE_METRICS and scope_s in ("per_entity",):
                reasons.append(
                    GateReason(
                        code="SC_RESTRICTION_CONFLICT",
                        severity=ReasonSeverity.ERROR,
                        message="min_separation_m é métrica global entre drones; scope per_entity é incoerente.",
                        dimension=MsfcDimension.RESTRICTIONS,
                        suggestion="Use scope=all_entities (ou equivalente global).",
                    )
                )
            if metric in DISTANCE_METRICS:
                # localization clara global
                pass
            elif scope_s in ("all_entities", "per_entity", "all_timesteps", "all_flights"):
                pass
            else:
                reasons.append(
                    GateReason(
                        code="SC_LOCALIZATION_UNCLEAR",
                        severity=ReasonSeverity.WARNING,
                        message=f"scope «{scope_s}» pouco claro para localização da evidência.",
                        dimension=MsfcDimension.EFFECTIVENESS_LOCALIZATION,
                        suggestion="Prefira all_entities (por drone) ou all_timesteps.",
                    )
                )

    elif isinstance(sc, RangeCriteria):
        ctype = "range"
        metric = _normalize_metric(str(sc.metric or ""))
        if not metric:
            reasons.append(
                GateReason(
                    code="SC_METRIC_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="Range sem metric.",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Indique a métrica (ex.: altitudeAGL).",
                )
            )
        try:
            lo, hi = float(sc.min_value), float(sc.max_value)
            if lo > hi:
                reasons.append(
                    GateReason(
                        code="SC_RANGE_INVALID",
                        severity=ReasonSeverity.ERROR,
                        message=f"Range inválido: min_value ({lo}) > max_value ({hi}).",
                        dimension=MsfcDimension.PERFORMANCE,
                        suggestion="Corrija os limites do intervalo.",
                    )
                )
            else:
                live_executable = True
        except (TypeError, ValueError):
            reasons.append(
                GateReason(
                    code="SC_RANGE_INVALID",
                    severity=ReasonSeverity.ERROR,
                    message="Range incompleto (min_value/max_value).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Preencha min_value e max_value numéricos.",
                )
            )
        kind = _metric_needs_unit(metric) if metric else None
        if kind and not _unit_ok(sc.unit, kind):
            reasons.append(
                GateReason(
                    code="SC_UNIT_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message=f"Unidade ausente ou incoerente para «{metric}» (esperado: {kind}).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion=f"Preencha unit (ex.: {kind}).",
                )
            )
        if getattr(sc, "scope", None) is None:
            reasons.append(
                GateReason(
                    code="SC_SCOPE_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="scope ausente no range.",
                    dimension=MsfcDimension.RESTRICTIONS,
                    suggestion="Defina scope (ex.: all_entities).",
                )
            )

    elif isinstance(sc, StatisticalCriteria):
        ctype = "statistical"
        metric = _normalize_metric(str(sc.metric or ""))
        agg = _agg_name(sc.aggregation)
        if not metric:
            reasons.append(
                GateReason(
                    code="SC_METRIC_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message="Statistical sem metric (Performance criteria).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion="Indique a métrica MQTT (ex.: altitudeAGL, batteryLevel).",
                )
            )
        if agg not in LIVE_WINDOW_AGGREGATIONS:
            reasons.append(
                GateReason(
                    code="SC_AGGREGATION_UNSUPPORTED",
                    severity=ReasonSeverity.ERROR,
                    message=(
                        f"Agregação «{agg or '?'}» fora do live MQTT "
                        f"(aceites: {', '.join(sorted(LIVE_WINDOW_AGGREGATIONS))}). "
                        "mean/std/percentile: backlog."
                    ),
                    dimension=MsfcDimension.LIVE_EXECUTABLE,
                    suggestion=(
                        "Para variação («não variar mais de X»), use aggregation=range "
                        "com operator <= e value=X sobre a métrica telemetria."
                    ),
                )
            )
            live_executable = False
        else:
            try:
                op = sc.operator
                if op is None:
                    raise ValueError("missing")
            except Exception:
                reasons.append(
                    GateReason(
                        code="SC_OPERATOR_MISSING",
                        severity=ReasonSeverity.ERROR,
                        message="Statistical sem operador de comparação válido.",
                        dimension=MsfcDimension.PERFORMANCE,
                        suggestion="Use um de: >=, <=, >, <, ==, !=.",
                    )
                )
            if sc.value is None:
                reasons.append(
                    GateReason(
                        code="SC_VALUE_MISSING",
                        severity=ReasonSeverity.ERROR,
                        message="Statistical sem value numérico.",
                        dimension=MsfcDimension.PERFORMANCE,
                        suggestion="Defina o limiar do agregado (ex.: range <= 1.0).",
                    )
                )
            elif agg in LIVE_WINDOW_AGGREGATIONS:
                live_executable = True

        kind = _metric_needs_unit(metric) if metric else None
        if kind and not _unit_ok(sc.unit, kind):
            reasons.append(
                GateReason(
                    code="SC_UNIT_MISSING",
                    severity=ReasonSeverity.ERROR,
                    message=f"Unidade ausente ou incoerente para «{metric}» (esperado: {kind}).",
                    dimension=MsfcDimension.PERFORMANCE,
                    suggestion=f"Preencha success_criteria.unit (ex.: {kind}).",
                )
            )

    else:
        ctype = type(sc).__name__
        reasons.append(
            GateReason(
                code="SC_TYPE_UNSUPPORTED",
                severity=ReasonSeverity.ERROR,
                message=(
                    f"Tipo de critério «{ctype}» fora do MVP live "
                    "(threshold/range/statistical com range|max|min). "
                    "Boolean/temporal/mean: backlog."
                ),
                dimension=MsfcDimension.PERFORMANCE,
                suggestion=(
                    "Reformule como threshold/range, ou statistical aggregation=range "
                    "para variação peak-to-peak."
                ),
            )
        )
        reasons.append(
            GateReason(
                code="LIVE_BOOLEAN_TEMPORAL",
                severity=ReasonSeverity.ERROR,
                message="Critério não executável pelo motor live actual.",
                dimension=MsfcDimension.LIVE_EXECUTABLE,
            )
        )
        live_executable = False

    # Texto verificável (Methods: SE should ensure all requirements are verifiable as written)
    if _text_not_measurable(req.text or ""):
        reasons.append(
            GateReason(
                code="SC_TEXT_NOT_MEASURABLE",
                severity=ReasonSeverity.ERROR,
                message=(
                    "Texto do requisito ambíguo / não mensurável "
                    "(Methods: requirements must be verifiable as written)."
                ),
                dimension=MsfcDimension.PERFORMANCE,
                suggestion=(
                    "Reescreva com métrica, operador e limiar "
                    "(ex.: «batteryLevel >= 20 percent em cada drone»)."
                ),
            )
        )
        suggestions.append(
            "Sugestão de reescrita: «O sistema deve manter <métrica> <operador> <valor> <unidade> "
            "durante <escopo>, medido via telemetria MQTT.»"
        )

    # Checkpoints / environment warnings
    if _TEMPORAL_WHOLE_MISSION.search(req.text or ""):
        reasons.append(
            GateReason(
                code="SC_CHECKPOINT_UNDEFINED",
                severity=ReasonSeverity.WARNING,
                message=(
                    "Texto exige cobertura temporal alargada sem duração mínima / checkpoint operacional "
                    "(MSFC: Checkpoints)."
                ),
                dimension=MsfcDimension.CHECKPOINTS,
                suggestion="Indique duração mínima de amostragem ou checkpoints da missão no MD/rationale.",
            )
        )

    reasons.append(
        GateReason(
            code="SC_ENV_UNDEFINED",
            severity=ReasonSeverity.WARNING,
            message=(
                "Environment Test Limits pouco especificados (altitude, nº mín. drones, indoor/outdoor…)."
            ),
            dimension=MsfcDimension.ENVIRONMENT,
            suggestion="Descreva no MD as condições sob as quais o critério é válido.",
        )
    )

    if metric and _PERCENTILE.search(req.text or ""):
        # Texto pede média/percentil — só aceite se o SC já for window-agg suportada
        # e o texto não for o único indício (ainda rejeitamos mean/percentile no motor).
        sc_agg = (
            _agg_name(sc.aggregation)
            if isinstance(sc, StatisticalCriteria)
            else ""
        )
        if sc_agg not in LIVE_WINDOW_AGGREGATIONS:
            reasons.append(
                GateReason(
                    code="SC_AGGREGATION_UNSUPPORTED",
                    severity=ReasonSeverity.ERROR,
                    message="Agregação estatística temporal (média/percentil) ainda não suportada no motor live.",
                    dimension=MsfcDimension.LIVE_EXECUTABLE,
                    suggestion=(
                        "Use limiar por amostra (threshold/range) ou variation peak-to-peak "
                        "(statistical aggregation=range)."
                    ),
                )
            )
            live_executable = False

    # Telemetria / live
    if metric:
        if not _is_known_telemetry(metric):
            reasons.append(
                GateReason(
                    code="SC_METRIC_NOT_IN_TELEMETRY",
                    severity=ReasonSeverity.ERROR,
                    message=f"Métrica «{metric}» não mapeável à telemetria MQTT do lab.",
                    dimension=MsfcDimension.EFFECTIVENESS_LOCALIZATION,
                    suggestion="Use campos do payload (batteryLevel, altitudeAGL, min_separation_m, …).",
                )
            )
            live_executable = False
        elif metric in DISTANCE_METRICS:
            reasons.append(
                GateReason(
                    code="LIVE_NEEDS_MULTI_DRONE",
                    severity=ReasonSeverity.WARNING,
                    message="min_separation_m exige ≥2 drones com GPS publicados no tópico.",
                    dimension=MsfcDimension.LIVE_EXECUTABLE,
                    suggestion="Garanta pelo menos duas entidades a publicar location durante a medição.",
                )
            )

    _LIVE_NUMERIC_TYPES = ("threshold", "range", "statistical")
    if vv == VVMethod.TEST.value and ctype not in _LIVE_NUMERIC_TYPES:
        reasons.append(
            GateReason(
                code="VV_TEST_WITHOUT_NUMERIC",
                severity=ReasonSeverity.ERROR,
                message="Método Test sem limiar numérico claro (Methods: Test obtém dados detalhados).",
                dimension=MsfcDimension.METHOD_COHERENCE,
                suggestion="Associe threshold/range ou statistical (range|max|min) com value.",
            )
        )
        method_coherence = "fail"

    for r in reasons:
        if (
            r.suggestion
            and r.suggestion not in suggestions
            and r.severity == ReasonSeverity.ERROR
        ):
            suggestions.append(r.suggestion)

    errors = [r for r in reasons if r.severity == ReasonSeverity.ERROR]
    numeric_ready = (
        ctype in _LIVE_NUMERIC_TYPES
        and bool(metric)
        and _is_known_telemetry(metric or "")
        and live_executable
    )

    if (
        not errors
        and method_coherence == "ok"
        and vv == VVMethod.TEST.value
        and numeric_ready
    ):
        status = GateStatus.ACCEPT
    else:
        status = GateStatus.REJECT

    return CriteriaGateResult(
        req_id=req.req_id,
        status=status,
        reasons=reasons,
        suggestions=suggestions,
        method_coherence=method_coherence,
        live_executable=(status == GateStatus.ACCEPT),
        vv_method=vv,
        metric=metric,
        criteria_type=ctype,
    )


def evaluate_session_criteria(requirements: list[RequirementRecord]) -> SessionGateSummary:
    results = [evaluate_requirement_criteria(r) for r in requirements]
    rejected = sum(1 for r in results if r.status == GateStatus.REJECT)
    accepted = sum(1 for r in results if r.status == GateStatus.ACCEPT)
    warns = sum(len(r.warnings) for r in results)
    global_status = GateStatus.ACCEPT if rejected == 0 and accepted > 0 else GateStatus.REJECT
    if not requirements:
        global_status = GateStatus.REJECT
    return SessionGateSummary(
        global_status=global_status,
        results=results,
        evaluated_at=time.time(),
        accepted_count=accepted,
        rejected_count=rejected,
        warning_count=warns,
    )


def success_criteria_model_doc() -> dict[str, Any]:
    """Modelo pedagógico para a UI (MSFC + Methods)."""
    return {
        "title": "Modelo de Success Criteria (MSFC-HDBK-3173 / SIS-08 Methods)",
        "msfc_dimensions": [
            {
                "id": "performance_criteria",
                "name": "Performance criteria",
                "ask": "O que medir e qual o limiar? (métrica + operador + valor / faixa)",
            },
            {
                "id": "environment_test_limits",
                "name": "Environment Test Limits",
                "ask": "Em que condições ambientais/operacionais o critério é válido?",
            },
            {
                "id": "tolerances",
                "name": "Tolerances",
                "ask": "Que folga é aceitável na observação?",
            },
            {
                "id": "margins",
                "name": "Margins",
                "ask": "Há margem de segurança além do limiar nominal?",
            },
            {
                "id": "specifications",
                "name": "Specifications",
                "ask": "A que CONOPS / especificação / requisito-fonte remete?",
            },
            {
                "id": "restrictions",
                "name": "Restrictions",
                "ask": "Escopo, entidades, pré-condições, restrições de execução?",
            },
            {
                "id": "checkpoints",
                "name": "Checkpoints",
                "ask": "Pontos de verificação no tempo ou no cenário?",
            },
            {
                "id": "effectiveness_and_localization",
                "name": "Effectiveness and localization",
                "ask": "Nível (missão/sistema/…) e alvo (por drone vs global)?",
            },
        ],
        "method_coherence": {
            "test": "Dados numéricos sob condições controladas (thresholds, ranges, amostras) — adequado a MQTT live",
            "demonstration": "Pass/fail observacional, sem data gathering denso — fora do MVP live",
            "inspection": "Atributos físicos / registos visuais — não é telemetria contínua",
            "analysis": "Modelos, cálculo, similaridade — não exige MQTT live",
        },
        "lifecycle": [
            "1. Definir Success Criteria (8 dimensões MSFC)",
            "2. Submeter para aprovação (maturidade suficiente) — no ReqValLive: gate ACCEPT/REJECT",
            "3. Manter sob controlo — critério aprovado fica associado à sessão/relatório",
            "4. Só então executar a actividade de V&V (medir MQTT → ok/nok)",
        ],
        "markdown_example": (
            "# Requisitos de missão (modelo)\n\n"
            "## RQ-BAT-001 — Bateria mínima (system / test)\n"
            "O sistema deve manter **batteryLevel >= 20 percent** em **cada drone** "
            "durante a operação (scope: all_entities).\n\n"
            "- **Success Criteria (Performance):** threshold metric=batteryLevel "
            "operator=>= value=20 unit=percent tolerance=0\n"
            "- **Environment:** voo outdoor; telemetria MQTT activa\n"
            "- **Restrictions / localization:** all_entities (por aeronave)\n"
            "- **Specifications:** conops_ref CONOPS-UTM §4.2; vv_method=test\n"
            "- **Checkpoints:** amostragem contínua enquanto measuring=true\n\n"
            "## RQ-SEP-001 — Separação mínima (system / test)\n"
            "Separação Haversine entre quaisquer dois drones: "
            "**min_separation_m >= 20 meters** (métrica global).\n\n"
            "- **Success Criteria:** threshold metric=min_separation_m "
            "operator=>= value=20 unit=meters scope=all_entities\n"
            "- **Pré-condição:** ≥2 drones com GPS\n\n"
            "## RQ-ALT-VAR-001 — Variação de altitude (system / test)\n"
            "altitudeAGL **não deve variar mais de 1 meter** na janela de medição.\n\n"
            "- **Success Criteria:** statistical metric=altitudeAGL aggregation=range "
            "operator=<= value=1 unit=meters\n"
            "- **Nota:** não inventar métrica `altitude_variation` — o agregado é sobre o campo MQTT\n"
        ),
        "live_statistical_window": {
            "aggregations": ["range", "max", "min"],
            "meaning": {
                "range": "max(série) − min(série) na janela measuring=true",
                "max": "máximo da série na janela",
                "min": "mínimo da série na janela",
            },
            "not_supported_yet": ["mean", "std", "percentile", "median"],
        },
        "json_example": {
            "req_id": "RQ-BAT-001",
            "title": "Nível mínimo de bateria",
            "text": "O sistema deve manter batteryLevel >= 20 percent em cada drone durante a operação",
            "rationale": "Evitar RTL forçado por descarga crítica",
            "level": "system",
            "vv_method": "test",
            "conops_ref": "CONOPS-UTM §4.2",
            "priority": "high",
            "success_criteria": {
                "type": "threshold",
                "metric": "batteryLevel",
                "operator": ">=",
                "value": 20.0,
                "unit": "percent",
                "scope": "all_entities",
                "tolerance": 0.0,
            },
            "tags": ["battery", "safety"],
        },
    }
