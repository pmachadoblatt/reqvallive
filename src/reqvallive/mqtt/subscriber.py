"""Subscriber MQTT embutido (um por sessão ativa)."""

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
    """Um cliente Paho por sessão; thread daemon com loop_forever."""

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
        self.session.measuring = True
        self._thread = threading.Thread(
            target=self._run,
            name=f"mqtt-{self.session.id}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.session.measuring = False
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
        self.session.mqtt_connected = False

    def _run(self) -> None:
        client_id = f"reqvallive-{self.session.id}"
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
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
            while not self._stop.is_set():
                client.loop(timeout=0.5)
        except Exception as exc:
            self.session.last_error = str(exc)
            self.session.mqtt_connected = False
            self.session.measuring = False
            logger.error("MQTT session %s failed: %s", self.session.id, exc)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        if getattr(reason_code, "is_failure", False):
            self.session.mqtt_connected = False
            self.session.last_error = str(reason_code)
            return
        self.session.mqtt_connected = True
        self.session.last_error = None
        client.subscribe(self.session.mqtt_topic)
        logger.info(
            "Session %s subscribed to %s@%s:%s",
            self.session.id,
            self.session.mqtt_topic,
            self.session.mqtt_broker,
            self.session.mqtt_port,
        )

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        self.session.mqtt_connected = False

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                self.session.last_error = "Payload MQTT não é um objeto JSON"
                return
        except Exception as exc:
            self.session.last_error = f"JSON inválido: {exc}"
            return

        sample = self.session.ingest_payload(payload)
        if sample is not None and self.on_sample is not None:
            try:
                self.on_sample(self.session, sample)
            except Exception:
                logger.exception("on_sample handler failed")


class MqttManager:
    """Regista workers activos por session_id."""

    def __init__(self) -> None:
        self._workers: dict[str, SessionMqttWorker] = {}
        self._lock = threading.RLock()

    def start(self, session: MeasurementSession, on_sample: OnSample | None = None) -> None:
        with self._lock:
            existing = self._workers.get(session.id)
            if existing:
                existing.stop()
            worker = SessionMqttWorker(session, on_sample=on_sample)
            self._workers[session.id] = worker
            worker.start()

    def stop(self, session_id: str) -> None:
        with self._lock:
            worker = self._workers.pop(session_id, None)
        if worker:
            worker.stop()


mqtt_manager = MqttManager()
