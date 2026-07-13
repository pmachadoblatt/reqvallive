"""Estado de sessão de medição (em memória)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from simreqvalidator.schema.requirement import RequirementRecord

from reqvallive.eval.live import LiveVerdict, evaluate_value, is_mvp_supported, metric_name
from reqvallive.metrics.registry import extract_metric
from reqvallive.sysml.generator import generate_sysml


@dataclass
class Sample:
    timestamp: float
    value: float
    ok: bool
    detail: str
    payload: dict[str, Any]


@dataclass
class MeasurementSession:
    id: str
    requirement: RequirementRecord
    mqtt_broker: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_topic: str
    sysml_text: str
    supported_live: bool
    created_at: float = field(default_factory=time.time)
    measuring: bool = False
    samples: list[Sample] = field(default_factory=list)
    last_value: float | None = None
    last_ok: bool | None = None
    last_detail: str = ""
    last_error: str | None = None
    mqtt_connected: bool = False
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def ingest_payload(self, payload: dict[str, Any]) -> Sample | None:
        with self._lock:
            if not self.measuring:
                return None
            metric = metric_name(self.requirement)
            value = extract_metric(metric, payload)
            if value is None:
                self.last_error = f"Métrica '{metric}' ausente no payload"
                return None
            verdict: LiveVerdict = evaluate_value(self.requirement, value)
            sample = Sample(
                timestamp=time.time(),
                value=value,
                ok=verdict.ok if verdict.supported else False,
                detail=verdict.detail,
                payload=payload,
            )
            self.samples.append(sample)
            self.last_value = value
            self.last_ok = sample.ok
            self.last_detail = sample.detail
            self.last_error = None
            return sample

    def summary(self) -> dict[str, Any]:
        with self._lock:
            values = [s.value for s in self.samples]
            violations = sum(1 for s in self.samples if not s.ok)
            final_ok = None
            if self.samples:
                # PASS só se todas as amostras OK (escopo all_timesteps default)
                final_ok = violations == 0
            return {
                "sample_count": len(self.samples),
                "violations": violations,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "last": self.last_value,
                "final_pass": final_ok,
            }

    def to_public_dict(self) -> dict[str, Any]:
        with self._lock:
            sc = self.requirement.success_criteria
            return {
                "id": self.id,
                "req_id": self.requirement.req_id,
                "title": self.requirement.title,
                "metric": metric_name(self.requirement),
                "criteria_type": getattr(sc, "type", type(sc).__name__),
                "success_criteria": sc.model_dump(mode="json"),
                "mqtt_broker": self.mqtt_broker,
                "mqtt_port": self.mqtt_port,
                "mqtt_topic": self.mqtt_topic,
                "supported_live": self.supported_live,
                "measuring": self.measuring,
                "mqtt_connected": self.mqtt_connected,
                "last_value": self.last_value,
                "last_ok": self.last_ok,
                "last_detail": self.last_detail,
                "last_error": self.last_error,
                "sysml_preview": self.sysml_text,
                "summary": self.summary(),
                "samples": [
                    {
                        "timestamp": s.timestamp,
                        "value": s.value,
                        "ok": s.ok,
                        "detail": s.detail,
                    }
                    for s in self.samples[-200:]
                ],
            }


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, MeasurementSession] = {}
        self._lock = threading.RLock()

    def create(
        self,
        requirement: RequirementRecord,
        *,
        mqtt_broker: str,
        mqtt_port: int,
        mqtt_username: str,
        mqtt_password: str,
        mqtt_topic: str,
    ) -> MeasurementSession:
        sid = uuid.uuid4().hex[:12]
        sysml = generate_sysml(requirement, mqtt_topic)
        session = MeasurementSession(
            id=sid,
            requirement=requirement,
            mqtt_broker=mqtt_broker,
            mqtt_port=mqtt_port,
            mqtt_username=mqtt_username,
            mqtt_password=mqtt_password,
            mqtt_topic=mqtt_topic,
            sysml_text=sysml,
            supported_live=is_mvp_supported(requirement),
        )
        with self._lock:
            self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> MeasurementSession | None:
        with self._lock:
            return self._sessions.get(session_id)


store = SessionStore()
