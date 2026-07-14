"""Estado de sessão — multi-requisito e multi-drone."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.validator import SchemaValidator

from reqvallive.eval.live import constraint_text, evaluate_value, is_mvp_supported, metric_name
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
    ok_by_req: dict[str, bool | None] = field(default_factory=dict)
    detail_by_req: dict[str, str] = field(default_factory=dict)
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
    mqtt_status: str = "disconnected"  # disconnected|connecting|listening|no_messages|error
    last_error: str | None = None
    drones: dict[str, DroneState] = field(default_factory=dict)
    message_log: list[dict[str, Any]] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)
    global_metrics: dict[str, float] = field(default_factory=dict)
    global_ok_by_req: dict[str, bool | None] = field(default_factory=dict)
    global_detail_by_req: dict[str, str] = field(default_factory=dict)
    global_actual_by_req: dict[str, float] = field(default_factory=dict)
    message_count: int = 0
    last_message_at: float | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def tracked_metrics(self) -> list[str]:
        """Métricas pedidas pelos requisitos (única fonte para UI/relatório)."""
        seen: list[str] = []
        for req in self.requirements:
            m = metric_name(req)
            if m and m not in seen:
                seen.append(m)
        return seen

    def start_measurement(self) -> None:
        with self._lock:
            self.measuring = True
            self.measurement_ended = False
            self.started_at = time.time()
            self.ended_at = None
            # limpa veredictos anteriores para uma nova corrida
            self.global_ok_by_req.clear()
            self.global_detail_by_req.clear()
            self.global_actual_by_req.clear()
            self.samples.clear()
            for d in self.drones.values():
                d.ok_by_req.clear()
                d.detail_by_req.clear()
                d.actual_by_req.clear()

    def stop_measurement(self) -> None:
        with self._lock:
            self.measuring = False
            self.measurement_ended = True
            self.ended_at = time.time()

    def primary_requirement(self) -> RequirementRecord:
        return self.requirements[0]

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
            for req in self.requirements:
                metric = metric_name(req)
                if metric in DISTANCE_METRICS:
                    continue
                val = extract_metric_from_payload(metric, payload)
                if val is None:
                    continue
                drone.metrics[metric] = val
                if self.measuring and is_mvp_supported(req):
                    verdict = evaluate_value(req, val)
                    drone.ok_by_req[req.req_id] = verdict.ok if verdict.supported else None
                    drone.detail_by_req[req.req_id] = verdict.detail
                    if verdict.value is not None:
                        drone.actual_by_req[req.req_id] = float(verdict.value)

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
                for req in self.requirements:
                    if metric_name(req) in DISTANCE_METRICS and self.measuring:
                        verdict = evaluate_value(req, sep)
                        self.global_ok_by_req[req.req_id] = (
                            verdict.ok if verdict.supported else None
                        )
                        self.global_detail_by_req[req.req_id] = verdict.detail
                        if verdict.value is not None:
                            self.global_actual_by_req[req.req_id] = float(verdict.value)

            # Log só com campos relevantes aos requisitos + id
            log_entry: dict[str, Any] = {"ts": time.time(), "drone": did}
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
            for req in self.requirements:
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
            for req in self.requirements:
                metric = metric_name(req)
                sc = req.success_criteria
                expected = constraint_text(req)
                unit = getattr(sc, "unit", "") or ""
                if metric in DISTANCE_METRICS:
                    ok = self.global_ok_by_req.get(req.req_id)
                    actual = self.global_actual_by_req.get(req.req_id)
                    detail = self.global_detail_by_req.get(req.req_id, "")
                    why = ""
                    if ok is False and actual is not None:
                        why = (
                            f"Valor observado {actual:g} {unit} não satisfaz "
                            f"«{expected}» (métrica {metric})."
                        )
                    elif ok is True:
                        why = f"Separação observada {actual} satisfaz «{expected}»."
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
                        dact = d.actual_by_req.get(req.req_id)
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
                                "actual": dact,
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
                            f"{e['id']}={e['actual']}" for e in fails if e["actual"] is not None
                        )
                        why = (
                            f"Falhou em {len(fails)} drone(s): {bits}. "
                            f"Esperado: {expected} ({metric})."
                        )
                    elif ok is True:
                        why = f"Todos os drones avaliados satisfazem «{expected}»."
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
            findings = self.findings()
            passed = sum(1 for f in findings if f["ok"] is True)
            failed = sum(1 for f in findings if f["ok"] is False)
            pending = sum(1 for f in findings if f["ok"] is None)
            return {
                "drone_count": len(self.drones),
                "message_count": self.message_count,
                "min_battery": min(batteries) if batteries else None,
                "max_battery": max(batteries) if batteries else None,
                "min_separation_m": self.global_metrics.get("min_separation_m"),
                "overall_ok": self.overall_ok(),
                "sample_count": len(self.samples),
                "measuring": self.measuring,
                "measurement_ended": self.measurement_ended,
                "tracked_metrics": self.tracked_metrics(),
                "reqs_pass": passed,
                "reqs_fail": failed,
                "reqs_pending": pending,
            }

    def to_public_dict(self) -> dict[str, Any]:
        with self._lock:
            reqs = []
            for req in self.requirements:
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
                        "last_seen": d.last_seen,
                    }
                )

            positions = {
                d.id: (d.latitude, d.longitude)
                for d in self.drones.values()
                if d.latitude is not None and d.longitude is not None
            }

            primary = self.requirements[0]
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
                "supported_live": all(is_mvp_supported(r) for r in self.requirements),
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
        with self._lock:
            self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> MeasurementSession | None:
        with self._lock:
            return self._sessions.get(session_id)


store = SessionStore()
