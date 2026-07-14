"""Subscriber MQTT embutido — connect separado de medir."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable

from paho.mqtt import client as mqtt

from reqvallive.models.session import MeasurementSession

logger = logging.getLogger(__name__)
OnSample = Callable[[MeasurementSession, Any], None]


class SessionMqttWorker:
    def __init__(self, session: MeasurementSession, on_sample: OnSample | None = None) -> None:
        self.session = session
        self.on_sample = on_sample
        self._client: mqtt.Client | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self.session.mqtt_status = "connecting"
        self.session.connected = False
        self.session.last_error = None
        self._thread = threading.Thread(
            target=self._run,
            name=f"mqtt-{self.session.id}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.session.measuring = False
        self.session.connected = False
        self.session.mqtt_status = "disconnected"
        client = self._client
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
            try:
                client.loop_stop()
            except Exception:
                pass

    def _run(self) -> None:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"reqvallive-{self.session.id}",
        )
        if self.session.mqtt_username:
            client.username_pw_set(
                self.session.mqtt_username,
                self.session.mqtt_password or None,
            )
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        self._client = client

        try:
            client.connect(self.session.mqtt_broker, self.session.mqtt_port, keepalive=60)
            idle_ticks = 0
            while not self._stop.is_set():
                client.loop(timeout=0.5)
                if self.session.connected and self.session.message_count == 0:
                    idle_ticks += 1
                    if idle_ticks > 6:  # ~3s
                        self.session.mqtt_status = "no_messages"
                else:
                    idle_ticks = 0
        except Exception as exc:
            self.session.last_error = str(exc)
            self.session.mqtt_status = "error"
            self.session.connected = False
            self.session.measuring = False
            logger.error("MQTT session %s failed: %s", self.session.id, exc)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if getattr(reason_code, "is_failure", False):
            self.session.connected = False
            self.session.mqtt_status = "error"
            self.session.last_error = str(reason_code)
            return
        self.session.connected = True
        self.session.last_error = None
        self.session.mqtt_status = "no_messages"
        client.subscribe(self.session.mqtt_topic)
        logger.info("Subscribed %s → %s", self.session.id, self.session.mqtt_topic)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.session.connected = False
        if not self._stop.is_set():
            self.session.mqtt_status = "error"
            self.session.last_error = f"disconnect: {reason_code}"

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                self.session.last_error = "Payload MQTT não é objeto JSON"
                return
        except Exception as exc:
            self.session.last_error = f"JSON inválido: {exc}"
            return
        self.session.ingest_payload(payload)
        if self.on_sample is not None:
            try:
                self.on_sample(self.session, payload)
            except Exception:
                logger.exception("on_sample failed")


class MqttManager:
    def __init__(self) -> None:
        self._workers: dict[str, SessionMqttWorker] = {}
        self._lock = threading.RLock()

    def connect(self, session: MeasurementSession) -> None:
        with self._lock:
            existing = self._workers.get(session.id)
            if existing:
                existing.stop()
            worker = SessionMqttWorker(session)
            self._workers[session.id] = worker
            worker.start()

    def disconnect(self, session_id: str) -> None:
        with self._lock:
            worker = self._workers.pop(session_id, None)
        if worker:
            worker.stop()

    def start(self, session: MeasurementSession, on_sample: OnSample | None = None) -> None:
        """Alias: garante conexão e marca measuring."""
        with self._lock:
            if session.id not in self._workers:
                worker = SessionMqttWorker(session, on_sample=on_sample)
                self._workers[session.id] = worker
                worker.start()
        session.measuring = True

    def stop(self, session_id: str) -> None:
        """Para medição mas mantém conexão se worker activo."""
        with self._lock:
            worker = self._workers.get(session_id)
        if worker:
            worker.session.measuring = False


mqtt_manager = MqttManager()
