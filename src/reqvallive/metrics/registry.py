"""Extração de métricas do payload MQTT do laboratório (multi-drone)."""

from __future__ import annotations

import math
from typing import Any


DISTANCE_METRICS = frozenset(
    {
        "min_separation_m",
        "min_separation",
        "collision_distance",
        "distance_m",
        "separation_m",
    }
)

BATTERY_ALIASES = frozenset(
    {
        "batteryLevel",
        "battery_level",
        "remainingCharge",
        "phoneBattery",
    }
)


def drone_id(payload: dict[str, Any]) -> str:
    for key in ("droneName", "drone_name", "name", "id"):
        val = payload.get(key)
        if val:
            return str(val)
    model = payload.get("droneModel")
    return str(model) if model else "unknown"


def extract_position(payload: dict[str, Any]) -> tuple[float, float, float | None] | None:
    loc = payload.get("location")
    if isinstance(loc, dict):
        lat = _as_float(loc.get("latitude"))
        lon = _as_float(loc.get("longitude"))
        alt = _as_float(loc.get("altitude"))
        if lat is not None and lon is not None:
            return lat, lon, alt
    lat = _as_float(payload.get("latitude"))
    lon = _as_float(payload.get("longitude"))
    if lat is not None and lon is not None:
        return lat, lon, _as_float(payload.get("altitude"))
    return None


def extract_battery(payload: dict[str, Any]) -> float | None:
    for key in ("batteryLevel", "battery_level", "remainingCharge"):
        val = _as_float(payload.get(key))
        if val is not None:
            return val
    phone = payload.get("phoneLocation")
    if isinstance(phone, dict):
        return _as_float(phone.get("battery"))
    return None


def _dig(payload: dict[str, Any], dotted: str) -> Any:
    cur: Any = payload
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def extract_metric_from_payload(metric: str, payload: dict[str, Any]) -> float | None:
    """Extrai métrica de UM payload de drone (não agregações entre drones)."""
    if not metric:
        return None

    # Aliases bateria
    if metric in BATTERY_ALIASES:
        return extract_battery(payload)

    # Campo directo
    direct = _as_float(payload.get(metric))
    if direct is not None:
        return direct

    # Caminhos aninhados (speed.horizontal → speed_horizontal ou speed.horizontal)
    dotted = metric.replace("_", ".")
    nested = _as_float(_dig(payload, dotted))
    if nested is not None:
        return nested

    if metric == "speed_horizontal":
        speed = payload.get("speed")
        if isinstance(speed, dict):
            return _as_float(speed.get("horizontal"))

    if metric == "altitudeAGL":
        return _as_float(payload.get("altitudeAGL"))

    if metric == "distanceToHome":
        return _as_float(payload.get("distanceToHome"))

    return None


def min_separation_from_positions(
    positions: dict[str, tuple[float, float]],
) -> float | None:
    ids = list(positions.keys())
    if len(ids) < 2:
        return None
    best = None
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = positions[ids[i]]
            b = positions[ids[j]]
            d = _haversine_m(a[0], a[1], b[0], b[1])
            if best is None or d < best:
                best = d
    return best


def separation_pairs(
    positions: dict[str, tuple[float, float]],
) -> list[dict[str, Any]]:
    ids = list(positions.keys())
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            d = _haversine_m(positions[a][0], positions[a][1], positions[b][0], positions[b][1])
            pairs.append({"a": a, "b": b, "distance_m": round(d, 2)})
    return pairs


def is_live_supported(metric: str) -> bool:
    return bool(metric)


def metric_source_hint(metric: str) -> str:
    if metric in DISTANCE_METRICS:
        return "Calculada entre location de todos os drones activos"
    if metric in BATTERY_ALIASES:
        return "Campo batteryLevel (ou remainingCharge) por drone"
    return f"Campo '{metric}' no payload MQTT de cada drone"


def extract_metric(metric: str, payload: dict[str, Any]) -> float | None:
    """Compat: um payload — usa extract_metric_from_payload excepto distância (precisa multi)."""
    if metric in DISTANCE_METRICS:
        # valor pré-calculado no payload
        for key in DISTANCE_METRICS:
            val = _as_float(payload.get(key))
            if val is not None:
                return val
        return None
    return extract_metric_from_payload(metric, payload)


def _as_float(raw: Any) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
