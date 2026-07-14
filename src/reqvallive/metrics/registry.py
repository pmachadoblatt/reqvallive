"""Mapeamento métrica do requisito → valor no payload MQTT.

Estratégia genérica:
1. Se o payload tem um campo numérico com o mesmo nome da métrica → usa directo
2. Se a métrica é conhecida e calculável (ex.: distância) → calcula
3. Caso contrário → None (sessão reporta erro de cobertura)
"""

from __future__ import annotations

import math
from typing import Any, Callable


# Aliases aceites para métricas de separação / distância
DISTANCE_METRICS = frozenset(
    {
        "min_separation_m",
        "min_separation",
        "collision_distance",
        "distance_m",
        "separation_m",
    }
)


def extract_metric(metric: str, payload: dict[str, Any]) -> float | None:
    """Extrai valor numérico da métrica a partir do envelope MQTT."""
    if not metric:
        return None

    # 1) Campo directo (genérico — qualquer métrica no JSON)
    direct = _as_float(payload.get(metric))
    if direct is not None:
        return direct

    # 2) Calculadores conhecidos
    extractor = _COMPUTED.get(metric)
    if extractor is not None:
        return extractor(payload)

    # 3) Aliases de distância → mesmo cálculo
    if metric in DISTANCE_METRICS:
        return _min_separation(payload)

    return None


def is_live_supported(metric: str) -> bool:
    """MVP: qualquer métrica pode ser medida se o payload a fornecer (directo ou calculável)."""
    return bool(metric)


def metric_source_hint(metric: str) -> str:
    if metric in DISTANCE_METRICS or metric in _COMPUTED:
        return (
            "Calculada a partir de entities[] {latitude,longitude} "
            "ou campo directo no payload MQTT"
        )
    return f"Campo numérico '{metric}' no payload MQTT (mesmo nome)"


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


def _entity_points(payload: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    entities = payload.get("entities") or payload.get("drones") or payload.get("vehicles")
    if isinstance(entities, list):
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            lat = _as_float(ent.get("latitude", ent.get("lat")))
            lon = _as_float(ent.get("longitude", ent.get("lon", ent.get("lng"))))
            if lat is not None and lon is not None:
                points.append((lat, lon))

    # Pares nomeados entity_a / entity_b
    a_lat = _as_float(payload.get("latitude_a", payload.get("lat_a")))
    a_lon = _as_float(payload.get("longitude_a", payload.get("lon_a")))
    b_lat = _as_float(payload.get("latitude_b", payload.get("lat_b")))
    b_lon = _as_float(payload.get("longitude_b", payload.get("lon_b")))
    if None not in (a_lat, a_lon, b_lat, b_lon):
        points.extend([(a_lat, a_lon), (b_lat, b_lon)])  # type: ignore[arg-type]

    return points


def _min_separation(payload: dict[str, Any]) -> float | None:
    # valor pré-calculado sob nomes comuns
    for key in ("min_separation_m", "min_separation", "collision_distance", "distance_m", "separation_m"):
        val = _as_float(payload.get(key))
        if val is not None:
            return val

    points = _entity_points(payload)
    if len(points) < 2:
        return None

    best = None
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = _haversine_m(points[i][0], points[i][1], points[j][0], points[j][1])
            if best is None or d < best:
                best = d
    return best


_COMPUTED: dict[str, Callable[[dict[str, Any]], float | None]] = {
    "min_separation_m": _min_separation,
    "min_separation": _min_separation,
    "collision_distance": _min_separation,
    "distance_m": _min_separation,
    "separation_m": _min_separation,
}
