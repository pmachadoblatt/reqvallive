"""Estado de sessão — multi-requisito e multi-drone."""

from __future__ import annotations

import copy
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.validator import SchemaValidator

from reqvallive.eval.criteria_gate import (
    GateStatus,
    SessionGateSummary,
    evaluate_session_criteria,
)
from reqvallive.eval.live import (
    constraint_text,
    evaluate_sample,
    evaluate_value,
    is_mvp_supported,
    is_window_statistical,
    metric_name,
)
from reqvallive.metrics.registry import (
    BATTERY_ALIASES,
    DISTANCE_METRICS,
    drone_id,
    extract_battery,
    extract_metric_from_payload,
    extract_position,
    metric_source_hint,
    min_separation_from_positions,
    separation_pairs,
)
from reqvallive.reports.markdown_export import build_model_markdown
from reqvallive.sysml.generator import generate_sysml_multi

_validator = SchemaValidator()


@dataclass
class DroneState:
    id: str
    battery: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    last_seen: float = 0.0
    last_payload: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    # Veredicto latched (all_timesteps): False permanece até ao fim
    ok_by_req: dict[str, bool | None] = field(default_factory=dict)
    detail_by_req: dict[str, str] = field(default_factory=dict)
    # Último valor visto (continua a actualizar mesmo após FAIL)
    last_actual_by_req: dict[str, float] = field(default_factory=dict)
    last_detail_by_req: dict[str, str] = field(default_factory=dict)
    # Extremos e contagens durante a medição
    min_actual_by_req: dict[str, float] = field(default_factory=dict)
    max_actual_by_req: dict[str, float] = field(default_factory=dict)
    sample_count_by_req: dict[str, int] = field(default_factory=dict)
    fail_count_by_req: dict[str, int] = field(default_factory=dict)
    # Evidência da primeira violação
    fail_actual_by_req: dict[str, float] = field(default_factory=dict)
    fail_detail_by_req: dict[str, str] = field(default_factory=dict)
    fail_ts_by_req: dict[str, float] = field(default_factory=dict)
    # compat: actual_by_req = evidência para relatório (1ª falha se FAIL, senão último)
    actual_by_req: dict[str, float] = field(default_factory=dict)


@dataclass
class MeasurementSession:
    id: str
    requirements: list[RequirementRecord]
    mqtt_broker: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_topic: str
    sysml_text: str
    model_markdown: str
    source_markdown: str = ""
    llm_notes: str = ""
    created_at: float = field(default_factory=time.time)
    connected: bool = False
    measuring: bool = False
    measurement_ended: bool = False
    started_at: float | None = None
    ended_at: float | None = None
    criteria_gate: SessionGateSummary | None = None
    # Cópia imutável do SC aprovado no instante do /start (auditoria da corrida)
    approved_sc_snapshot: dict[str, Any] | None = None
    _approved_requirements: list[RequirementRecord] | None = None
    mqtt_status: str = "disconnected"  # disconnected|connecting|listening|no_messages|error
    last_error: str | None = None
    drones: dict[str, DroneState] = field(default_factory=dict)
    message_log: list[dict[str, Any]] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)
    global_metrics: dict[str, float] = field(default_factory=dict)
    global_ok_by_req: dict[str, bool | None] = field(default_factory=dict)
    global_detail_by_req: dict[str, str] = field(default_factory=dict)
    global_actual_by_req: dict[str, float] = field(default_factory=dict)
    global_fail_actual_by_req: dict[str, float] = field(default_factory=dict)
    global_fail_detail_by_req: dict[str, str] = field(default_factory=dict)
    global_fail_ts_by_req: dict[str, float] = field(default_factory=dict)
    global_last_actual_by_req: dict[str, float] = field(default_factory=dict)
    global_fail_count_by_req: dict[str, int] = field(default_factory=dict)
    global_sample_count_by_req: dict[str, int] = field(default_factory=dict)
    # extremos observados durante measuring (para o relatório)
    metric_extrema: dict[str, dict[str, float]] = field(default_factory=dict)
    message_count: int = 0
    last_message_at: float | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def active_requirements(self) -> list[RequirementRecord]:
        """Requisitos da corrida: snapshot aprovado após /start; senão a lista de trabalho."""
        if self._approved_requirements is not None:
            return self._approved_requirements
        return self.requirements

    def tracked_metrics(self) -> list[str]:
        """Métricas pedidas pelos requisitos activos (única fonte para UI/relatório)."""
        seen: list[str] = []
        for req in self.active_requirements():
            m = metric_name(req)
            if m and m not in seen:
                seen.append(m)
        return seen

    def refresh_criteria_gate(self) -> SessionGateSummary:
        with self._lock:
            # Gate reavalia a lista de trabalho; o snapshot da corrida não muda.
            summary = evaluate_session_criteria(self.requirements)
            self.criteria_gate = summary
            return summary

    def gate_allows_measurement(self) -> bool:
        with self._lock:
            if self.criteria_gate is None:
                self.refresh_criteria_gate()
            assert self.criteria_gate is not None
            return self.criteria_gate.global_status == GateStatus.ACCEPT

    def freeze_approved_sc(self) -> dict[str, Any]:
        """Congela SC + gate no instante do start (deep copy via JSON do schema)."""
        dumped = [r.model_dump(mode="json") for r in self.requirements]
        self._approved_requirements = [RequirementRecord.model_validate(d) for d in dumped]
        gate = self.criteria_gate.to_dict() if self.criteria_gate else None
        self.approved_sc_snapshot = {
            "frozen_at": time.time(),
            "session_id": self.id,
            "gate_status": (gate or {}).get("global_status"),
            "gate": gate,
            "requirements": dumped,
            "mqtt": {
                "broker": self.mqtt_broker,
                "port": self.mqtt_port,
                "topic": self.mqtt_topic,
            },
        }
        return self.approved_sc_snapshot

    def start_measurement(self) -> None:
        with self._lock:
            self.freeze_approved_sc()
            self.measuring = True
            self.measurement_ended = False
            self.started_at = time.time()
            self.ended_at = None
            # limpa veredictos anteriores para uma nova corrida
            self.global_ok_by_req.clear()
            self.global_detail_by_req.clear()
            self.global_actual_by_req.clear()
            self.global_fail_actual_by_req.clear()
            self.global_fail_detail_by_req.clear()
            self.global_fail_ts_by_req.clear()
            self.global_last_actual_by_req.clear()
            self.global_fail_count_by_req.clear()
            self.global_sample_count_by_req.clear()
            self.metric_extrema.clear()
            self.samples.clear()
            for d in self.drones.values():
                d.ok_by_req.clear()
                d.detail_by_req.clear()
                d.actual_by_req.clear()
                d.last_actual_by_req.clear()
                d.last_detail_by_req.clear()
                d.min_actual_by_req.clear()
                d.max_actual_by_req.clear()
                d.sample_count_by_req.clear()
                d.fail_count_by_req.clear()
                d.fail_actual_by_req.clear()
                d.fail_detail_by_req.clear()
                d.fail_ts_by_req.clear()

    def stop_measurement(self) -> None:
        with self._lock:
            self.measuring = False
            self.measurement_ended = True
            self.ended_at = time.time()
            # Mantém approved_sc_snapshot — é a prova do que valeu nesta corrida

    def primary_requirement(self) -> RequirementRecord:
        reqs = self.active_requirements()
        return reqs[0]

    @staticmethod
    def _latch_ok(previous: bool | None, sample_ok: bool | None) -> bool | None:
        """all_timesteps: uma falha em qualquer amostra permanece FAIL até ao fim."""
        if sample_ok is None:
            return previous
        if previous is False:
            return False
        return sample_ok

    def _note_extrema(self, metric: str, value: float) -> None:
        ext = self.metric_extrema.get(metric)
        if ext is None:
            self.metric_extrema[metric] = {"min": value, "max": value}
        else:
            ext["min"] = min(ext["min"], value)
            ext["max"] = max(ext["max"], value)

    def ingest_payload(self, payload: dict[str, Any]) -> None:
        with self._lock:
            # Medição já encerrada: não alterar resultados (só heartbeat MQTT)
            if self.measurement_ended:
                if self.mqtt_status in ("connecting", "no_messages", "listening"):
                    self.mqtt_status = "listening"
                self.last_message_at = time.time()
                return

            self.message_count += 1
            self.last_message_at = time.time()
            if self.mqtt_status in ("connecting", "no_messages", "listening"):
                self.mqtt_status = "listening"

            did = drone_id(payload)
            drone = self.drones.get(did) or DroneState(id=did)
            drone.last_seen = time.time()
            drone.last_payload = payload

            needed = set(self.tracked_metrics())
            needs_battery = bool(needed & BATTERY_ALIASES)

            bat = extract_battery(payload)
            if bat is not None and needs_battery:
                drone.battery = bat
                drone.metrics["batteryLevel"] = bat

            pos = extract_position(payload)
            if pos:
                drone.latitude, drone.longitude, drone.altitude = pos[0], pos[1], pos[2]

            # métricas por requisito (excepto distância global)
            for req in self.active_requirements():
                metric = metric_name(req)
                if metric in DISTANCE_METRICS:
                    continue
                val = extract_metric_from_payload(metric, payload)
                if val is None:
                    continue
                drone.metrics[metric] = val
                if self.measuring:
                    self._note_extrema(metric, float(val))
                if self.measuring and is_mvp_supported(req):
                    rid = req.req_id
                    raw = float(val)
                    # Extremos da série da métrica MQTT (sempre sobre o valor bruto)
                    if rid not in drone.min_actual_by_req:
                        drone.min_actual_by_req[rid] = raw
                        drone.max_actual_by_req[rid] = raw
                    else:
                        drone.min_actual_by_req[rid] = min(drone.min_actual_by_req[rid], raw)
                        drone.max_actual_by_req[rid] = max(drone.max_actual_by_req[rid], raw)

                    verdict = evaluate_sample(
                        req,
                        raw,
                        sample_min=drone.min_actual_by_req[rid],
                        sample_max=drone.max_actual_by_req[rid],
                    )
                    sample_ok = verdict.ok if verdict.supported else None
                    prev = drone.ok_by_req.get(rid)
                    latched = self._latch_ok(prev, sample_ok)
                    drone.ok_by_req[rid] = latched
                    # Valor observado no critério: amostra (threshold/range) ou agregado (statistical)
                    observed = (
                        float(verdict.value)
                        if verdict.value is not None
                        else raw
                    )
                    drone.last_actual_by_req[rid] = observed
                    drone.last_detail_by_req[rid] = verdict.detail
                    drone.sample_count_by_req[rid] = drone.sample_count_by_req.get(rid, 0) + 1
                    if sample_ok is False:
                        drone.fail_count_by_req[rid] = drone.fail_count_by_req.get(rid, 0) + 1
                        if rid not in drone.fail_actual_by_req:
                            drone.fail_actual_by_req[rid] = observed
                            drone.fail_detail_by_req[rid] = verdict.detail
                            drone.fail_ts_by_req[rid] = time.time()
                    # Relatório: evidência de falha se FAIL, senão último valor
                    if latched is False and rid in drone.fail_actual_by_req:
                        drone.actual_by_req[rid] = drone.fail_actual_by_req[rid]
                        series_note = (
                            f"série=[{drone.min_actual_by_req[rid]:g}..{drone.max_actual_by_req[rid]:g}]"
                            if is_window_statistical(req)
                            else f"min={drone.min_actual_by_req[rid]:g}"
                        )
                        drone.detail_by_req[rid] = (
                            f"1ª violação: {drone.fail_detail_by_req[rid]} "
                            f"(atual={observed:g}, {series_note}, "
                            f"falhas={drone.fail_count_by_req.get(rid, 0)}/"
                            f"{drone.sample_count_by_req.get(rid, 0)})"
                        )
                    else:
                        drone.actual_by_req[rid] = observed
                        drone.detail_by_req[rid] = verdict.detail

            self.drones[did] = drone

            # Distância global entre todos os drones com posição
            positions = {
                d.id: (d.latitude, d.longitude)
                for d in self.drones.values()
                if d.latitude is not None and d.longitude is not None
            }
            sep = min_separation_from_positions(positions)  # type: ignore[arg-type]
            if sep is not None and (needed & DISTANCE_METRICS):
                self.global_metrics["min_separation_m"] = sep
                if self.measuring:
                    self._note_extrema("min_separation_m", float(sep))
                for req in self.active_requirements():
                    if metric_name(req) in DISTANCE_METRICS and self.measuring:
                        verdict = evaluate_value(req, sep)
                        sample_ok = verdict.ok if verdict.supported else None
                        rid = req.req_id
                        prev = self.global_ok_by_req.get(rid)
                        latched = self._latch_ok(prev, sample_ok)
                        self.global_ok_by_req[rid] = latched
                        fv = float(sep)
                        self.global_last_actual_by_req[rid] = fv
                        self.global_sample_count_by_req[rid] = (
                            self.global_sample_count_by_req.get(rid, 0) + 1
                        )
                        if sample_ok is False:
                            self.global_fail_count_by_req[rid] = (
                                self.global_fail_count_by_req.get(rid, 0) + 1
                            )
                            if rid not in self.global_fail_actual_by_req:
                                self.global_fail_actual_by_req[rid] = fv
                                self.global_fail_detail_by_req[rid] = verdict.detail
                                self.global_fail_ts_by_req[rid] = time.time()
                        if latched is False and rid in self.global_fail_actual_by_req:
                            self.global_actual_by_req[rid] = self.global_fail_actual_by_req[rid]
                            self.global_detail_by_req[rid] = (
                                f"1ª violação: {self.global_fail_detail_by_req[rid]} "
                                f"(atual={fv:g}, falhas="
                                f"{self.global_fail_count_by_req.get(rid, 0)}/"
                                f"{self.global_sample_count_by_req.get(rid, 0)})"
                            )
                        else:
                            self.global_actual_by_req[rid] = fv
                            self.global_detail_by_req[rid] = verdict.detail

            # Log só com campos relevantes aos requisitos + id
            log_entry: dict[str, Any] = {"ts": time.time(), "drone": did, "violation": False}
            sample_violation = False
            for req in self.active_requirements():
                metric = metric_name(req)
                if metric in DISTANCE_METRICS:
                    continue
                if metric in drone.metrics and self.measuring and is_mvp_supported(req):
                    # amostra deste payload: violação se o valor actual falha o limiar
                    vnow = drone.last_actual_by_req.get(req.req_id)
                    if vnow is not None:
                        sample_verdict = evaluate_value(req, vnow)
                        if sample_verdict.supported and sample_verdict.ok is False:
                            sample_violation = True
            if sample_violation:
                log_entry["violation"] = True
            for m in needed:
                if m in DISTANCE_METRICS:
                    log_entry[m] = self.global_metrics.get("min_separation_m")
                elif m in drone.metrics:
                    log_entry[m] = drone.metrics[m]
                elif m in ("batteryLevel", "battery_level") and bat is not None:
                    log_entry[m] = bat
            if drone.latitude is not None:
                log_entry["lat"] = drone.latitude
                log_entry["lon"] = drone.longitude
            self.message_log.append(log_entry)
            self.message_log = self.message_log[-100:]

            if self.measuring:
                self.samples.append(
                    {
                        "timestamp": time.time(),
                        "drone": did,
                        "metrics": dict(drone.metrics),
                        "ok": dict(drone.ok_by_req),
                        "global_metrics": dict(self.global_metrics),
                    }
                )
                self.samples = self.samples[-500:]

    def overall_ok(self) -> bool | None:
        with self._lock:
            flags: list[bool] = []
            for req in self.active_requirements():
                metric = metric_name(req)
                if metric in DISTANCE_METRICS:
                    v = self.global_ok_by_req.get(req.req_id)
                    if v is not None:
                        flags.append(v)
                else:
                    for d in self.drones.values():
                        v = d.ok_by_req.get(req.req_id)
                        if v is not None:
                            flags.append(v)
            if not flags:
                return None
            return all(flags)

    def findings(self) -> list[dict[str, Any]]:
        """Lista legível: por requisito, o que era esperado vs o que ocorreu."""
        with self._lock:
            out: list[dict[str, Any]] = []
            for req in self.active_requirements():
                metric = metric_name(req)
                sc = req.success_criteria
                expected = constraint_text(req)
                unit = getattr(sc, "unit", "") or ""
                if metric in DISTANCE_METRICS:
                    ok = self.global_ok_by_req.get(req.req_id)
                    actual = self.global_fail_actual_by_req.get(req.req_id)
                    if actual is None:
                        actual = self.global_actual_by_req.get(req.req_id)
                    detail = self.global_fail_detail_by_req.get(req.req_id) or self.global_detail_by_req.get(
                        req.req_id, ""
                    )
                    why = ""
                    if ok is False and actual is not None:
                        why = (
                            f"Durante a medição, o valor {actual:g} {unit} violou «{expected}» "
                            f"(métrica {metric}; falha latched — all_timesteps)."
                        )
                    elif ok is True:
                        why = f"Separação observada satisfaz «{expected}» em todas as amostras."
                    elif ok is None:
                        why = "Sem amostra suficiente para avaliar (ex.: faltam 2 drones com GPS)."
                    out.append(
                        {
                            "req_id": req.req_id,
                            "title": req.title,
                            "metric": metric,
                            "expected": expected,
                            "actual": actual,
                            "unit": unit,
                            "ok": ok,
                            "scope": "global",
                            "detail": detail,
                            "why": why,
                            "entities": [],
                        }
                    )
                else:
                    entities = []
                    any_fail = False
                    any_ok = False
                    any_pending = False
                    for d in self.drones.values():
                        dok = d.ok_by_req.get(req.req_id)
                        dact_fail = d.fail_actual_by_req.get(req.req_id)
                        dact_last = d.last_actual_by_req.get(req.req_id)
                        dact_min = d.min_actual_by_req.get(req.req_id)
                        dact_max = d.max_actual_by_req.get(req.req_id)
                        n_fail = d.fail_count_by_req.get(req.req_id, 0)
                        n_samp = d.sample_count_by_req.get(req.req_id, 0)
                        fail_ts = d.fail_ts_by_req.get(req.req_id)
                        ddet = d.detail_by_req.get(req.req_id, "")
                        if dok is True:
                            any_ok = True
                        elif dok is False:
                            any_fail = True
                        else:
                            any_pending = True
                        entities.append(
                            {
                                "id": d.id,
                                "ok": dok,
                                "actual": dact_fail if dok is False else dact_last,
                                "last": dact_last,
                                "min": dact_min,
                                "max": dact_max,
                                "fail_count": n_fail,
                                "sample_count": n_samp,
                                "first_fail": dact_fail,
                                "first_fail_ts": fail_ts,
                                "detail": ddet,
                            }
                        )
                    if any_fail:
                        ok = False
                    elif any_pending:
                        ok = None
                    elif any_ok:
                        ok = True
                    else:
                        ok = None
                    fails = [e for e in entities if e["ok"] is False]
                    if ok is False and fails:
                        bits = ", ".join(
                            f"{e['id']}: 1ª={e['first_fail']} min={e['min']} "
                            f"atual={e['last']} ({e['fail_count']}/{e['sample_count']} falhas)"
                            for e in fails
                        )
                        why = (
                            f"Violação durante a medição (all_timesteps). {bits}. "
                            f"Critério: {expected}."
                        )
                    elif ok is True:
                        why = (
                            f"Todos os drones satisfizeram «{expected}» "
                            f"em todas as amostras da medição."
                        )
                    else:
                        why = "Aguardando telemetria com a métrica pedida."
                    out.append(
                        {
                            "req_id": req.req_id,
                            "title": req.title,
                            "metric": metric,
                            "expected": expected,
                            "actual": None,
                            "unit": unit,
                            "ok": ok,
                            "scope": "per_drone",
                            "detail": "",
                            "why": why,
                            "entities": entities,
                        }
                    )
            return out

    def summary(self) -> dict[str, Any]:
        with self._lock:
            batteries = [d.battery for d in self.drones.values() if d.battery is not None]
            bat_ext = self.metric_extrema.get("batteryLevel") or self.metric_extrema.get(
                "battery_level"
            )
            findings = self.findings()
            passed = sum(1 for f in findings if f["ok"] is True)
            failed = sum(1 for f in findings if f["ok"] is False)
            pending = sum(1 for f in findings if f["ok"] is None)
            return {
                "drone_count": len(self.drones),
                "message_count": self.message_count,
                "min_battery": (bat_ext or {}).get("min")
                if bat_ext
                else (min(batteries) if batteries else None),
                "max_battery": (bat_ext or {}).get("max")
                if bat_ext
                else (max(batteries) if batteries else None),
                "min_separation_m": self.global_metrics.get("min_separation_m"),
                "overall_ok": self.overall_ok(),
                "sample_count": len(self.samples),
                "measuring": self.measuring,
                "measurement_ended": self.measurement_ended,
                "tracked_metrics": self.tracked_metrics(),
                "reqs_pass": passed,
                "reqs_fail": failed,
                "reqs_pending": pending,
                "metric_extrema": dict(self.metric_extrema),
            }

    def to_public_dict(self) -> dict[str, Any]:
        with self._lock:
            active = self.active_requirements()
            reqs = []
            for req in active:
                sc = req.success_criteria
                metric = metric_name(req)
                reqs.append(
                    {
                        "req_id": req.req_id,
                        "title": req.title,
                        "text": req.text,
                        "metric": metric,
                        "metric_hint": metric_source_hint(metric),
                        "success_criteria": sc.model_dump(mode="json"),
                        "supported_live": is_mvp_supported(req),
                        "global_ok": self.global_ok_by_req.get(req.req_id),
                        "global_detail": self.global_detail_by_req.get(req.req_id),
                        "global_actual": self.global_actual_by_req.get(req.req_id),
                    }
                )

            drones = []
            for d in self.drones.values():
                drones.append(
                    {
                        "id": d.id,
                        "battery": d.battery,
                        "latitude": d.latitude,
                        "longitude": d.longitude,
                        "altitude": d.altitude,
                        "metrics": d.metrics,
                        "ok_by_req": d.ok_by_req,
                        "detail_by_req": d.detail_by_req,
                        "actual_by_req": d.actual_by_req,
                        "last_actual_by_req": d.last_actual_by_req,
                        "min_actual_by_req": d.min_actual_by_req,
                        "max_actual_by_req": d.max_actual_by_req,
                        "fail_count_by_req": d.fail_count_by_req,
                        "sample_count_by_req": d.sample_count_by_req,
                        "fail_actual_by_req": d.fail_actual_by_req,
                        "fail_detail_by_req": d.fail_detail_by_req,
                        "fail_ts_by_req": d.fail_ts_by_req,
                        "last_seen": d.last_seen,
                    }
                )

            positions = {
                d.id: (d.latitude, d.longitude)
                for d in self.drones.values()
                if d.latitude is not None and d.longitude is not None
            }

            primary = active[0]
            snap = None
            if self.approved_sc_snapshot is not None:
                snap = copy.deepcopy(self.approved_sc_snapshot)

            return {
                "id": self.id,
                "req_id": primary.req_id,
                "title": primary.title,
                "text": primary.text,
                "requirements": reqs,
                "tracked_metrics": self.tracked_metrics(),
                "mqtt_broker": self.mqtt_broker,
                "mqtt_port": self.mqtt_port,
                "mqtt_topic": self.mqtt_topic,
                "mqtt_username": self.mqtt_username,
                "connected": self.connected,
                "measuring": self.measuring,
                "measurement_ended": self.measurement_ended,
                "started_at": self.started_at,
                "ended_at": self.ended_at,
                "mqtt_status": self.mqtt_status,
                "last_error": self.last_error,
                "sysml_preview": self.sysml_text,
                "model_markdown": self.model_markdown,
                "llm_notes": self.llm_notes,
                "drones": drones,
                "separations": separation_pairs(positions),  # type: ignore[arg-type]
                "global_metrics": dict(self.global_metrics),
                "message_log": list(self.message_log[-50:]),
                "summary": self.summary(),
                "findings": self.findings(),
                "overall_ok": self.overall_ok(),
                "supported_live": all(is_mvp_supported(r) for r in active),
                "criteria_gate": self.criteria_gate.to_dict() if self.criteria_gate else None,
                "approved_sc_snapshot": snap,
                "sc_frozen": snap is not None,
                "thresholds": [
                    {
                        "req_id": r.req_id,
                        "metric": metric_name(r),
                        "success_criteria": r.success_criteria.model_dump(mode="json"),
                    }
                    for r in active
                ],
            }



class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, MeasurementSession] = {}
        self._lock = threading.RLock()

    def create_from_requirements(
        self,
        req_dicts: list[dict[str, Any]],
        *,
        mqtt_broker: str,
        mqtt_port: int,
        mqtt_username: str,
        mqtt_password: str,
        mqtt_topic: str,
        source_markdown: str = "",
        llm_notes: str = "",
    ) -> MeasurementSession:
        parsed: list[RequirementRecord] = []
        for data in req_dicts:
            req, issues = _validator.validate_single(data)
            if req is None:
                raise ValueError(f"Requisito inválido: {[i.message for i in issues]}")
            parsed.append(req)

        sid = uuid.uuid4().hex[:12]
        sysml = generate_sysml_multi(parsed, mqtt_topic)
        md = build_model_markdown(
            requirements=parsed,
            sysml_text=sysml,
            mqtt_topic=mqtt_topic,
            notes=llm_notes,
        )
        session = MeasurementSession(
            id=sid,
            requirements=parsed,
            mqtt_broker=mqtt_broker,
            mqtt_port=mqtt_port,
            mqtt_username=mqtt_username,
            mqtt_password=mqtt_password,
            mqtt_topic=mqtt_topic,
            sysml_text=sysml,
            model_markdown=md,
            source_markdown=source_markdown,
            llm_notes=llm_notes,
        )
        session.refresh_criteria_gate()
        with self._lock:
            self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> MeasurementSession | None:
        with self._lock:
            return self._sessions.get(session_id)


store = SessionStore()
