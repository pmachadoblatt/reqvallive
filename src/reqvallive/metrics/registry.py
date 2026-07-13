"""Mapeamento métrica do requisito → valor no payload MQTT."""

from __future__ import annotations

from typing import Any, Callable


SUPPORTED_LIVE_METRICS = frozenset({"battery_level"})


def extract_metric(metric: str, payload: dict[str, Any]) -> float | None:
    """Extrai valor numérico da métrica a partir do envelope MQTT."""
    extractor = _REGISTRY.get(metric)
    if extractor is None:
        return None
    return extractor(payload)


def is_live_supported(metric: str) -> bool:
    return metric in SUPPORTED_LIVE_METRICS


def _battery_level(payload: dict[str, Any]) -> float | None:
    raw = payload.get("battery_level")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


_REGISTRY: dict[str, Callable[[dict[str, Any]], float | None]] = {
    "battery_level": _battery_level,
}
