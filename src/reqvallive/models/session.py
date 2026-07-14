"""Estado de sessão — multi-requisito e multi-drone."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.validator import SchemaValidator

from reqvallive.eval.live import evaluate_value, is_mvp_supported, metric_name
from reqvallive.metrics.registry import (
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
    mqtt_status: str = "disconnected"  # disconnected|connecting|listening|no_messages|error
    last_error: str | None = None
    drones: dict[str, DroneState] = field(default_factory=dict)
    message_log: list[dict[str, Any]] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)
    global_metrics: dict[str, float] = field(default_factory=dict)
    global_ok_by_req: dict[str, bool | None] = field(default_factory=dict)
    message_count: int = 0
    last_message_at: float | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def primary_requirement(self) -> RequirementRecord:
        return self.requirements[0]

    def ingest_payload(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self.message_count += 1
            self.last_message_at = time.time()
            if self.mqtt_status in ("connecting", "no_messages", "listening"):
                self.mqtt_status = "listening"

            did = drone_id(payload)
            drone = self.drones.get(did) or DroneState(id=did)
            drone.last_seen = time.time()
            drone.last_payload = payload

            bat = extract_battery(payload)
            if bat is not None:
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

            self.drones[did] = drone

            # Distância global entre todos os drones com posição
            positions = {
                d.id: (d.latitude, d.longitude)
                for d in self.drones.values()
                if d.latitude is not None and d.longitude is not None
            }
            sep = min_separation_from_positions(positions)  # type: ignore[arg-type]
            if sep is not None:
                self.global_metrics["min_separation_m"] = sep
                for req in self.requirements:
                    if metric_name(req) in DISTANCE_METRICS and self.measuring:
                        verdict = evaluate_value(req, sep)
                        self.global_ok_by_req[req.req_id] = (
                            verdict.ok if verdict.supported else None
                        )

            # Log compacto
            self.message_log.append(
                {
                    "ts": time.time(),
                    "drone": did,
                    "batteryLevel": bat,
                    "lat": drone.latitude,
                    "lon": drone.longitude,
                }
            )
            self.message_log = self.message_log[-100:]

            if self.measuring:
                self.samples.append(
                    {
                        "timestamp": time.time(),
                        "drone": did,
                        "battery": bat,
                        "ok": drone.ok_by_req,
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

    def summary(self) -> dict[str, Any]:
        with self._lock:
            batteries = [d.battery for d in self.drones.values() if d.battery is not None]
            return {
                "drone_count": len(self.drones),
                "message_count": self.message_count,
                "min_battery": min(batteries) if batteries else None,
                "max_battery": max(batteries) if batteries else None,
                "min_separation_m": self.global_metrics.get("min_separation_m"),
                "overall_ok": self.overall_ok(),
                "sample_count": len(self.samples),
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
                "mqtt_broker": self.mqtt_broker,
                "mqtt_port": self.mqtt_port,
                "mqtt_topic": self.mqtt_topic,
                "mqtt_username": self.mqtt_username,
                "connected": self.connected,
                "measuring": self.measuring,
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
