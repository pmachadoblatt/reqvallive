"""Cliente LLM OpenAI-compatible (Ollama Conceptio)."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from reqvallive.config import settings

SYSTEM_PROMPT = """Você é um engenheiro de sistemas MBSE especializado em SysML V2 e V&V.
Recebe um documento Markdown com requisitos de missão.
Extraia requisitos verificáveis e critérios de sucesso mensuráveis ligados a telemetria MQTT de drones.

Responda APENAS com JSON válido (sem markdown fences, sem texto antes/depois) no formato:
{
  "requirements": [
    {
      "req_id": "RQ-BAT-001",
      "title": "Bateria mínima",
      "text": "O sistema deve manter batteryLevel acima de 20 por cento em cada drone",
      "rationale": "Segurança de voo",
      "level": "system",
      "vv_method": "test",
      "priority": "high",
      "conops_ref": "CONOPS",
      "source": "markdown",
      "success_criteria": {
        "type": "threshold",
        "metric": "batteryLevel",
        "operator": ">=",
        "value": 20.0,
        "unit": "percent",
        "scope": "all_entities",
        "tolerance": 0.0
      },
      "tags": ["battery"]
    }
  ],
  "sysml_notes": "resumo curto",
  "metrics_needed": ["batteryLevel"]
}

Regras:
- Extraia APENAS os requisitos explicitamente pedidos no Markdown. NÃO invente requisitos extra (ex.: bateria) se o documento não os mencionar.
- success_criteria.type: "threshold", "range" OU "statistical"
- metric deve ser exactamente o campo MQTT (NÃO invente métricas derivadas): batteryLevel, altitudeAGL, distanceToHome, min_separation_m, speed_horizontal, satelliteCount, remainingFlightTime, etc.
- Variação / amplitude / «não variar mais de X» / peak-to-peak: use type "statistical", aggregation "range", operator "<=", value = X, metric = o campo telemetria (ex.: altitudeAGL). NÃO crie metric inventada tipo altitude_variation.
- Máximo/mínimo na janela de medição: statistical com aggregation "max" ou "min".
- NÃO use aggregation mean/std/percentile (ainda não suportadas no live).
- operator: ">=", "<=", ">", "<", "==", "!="
- scope (threshold/range): "all_entities" ou "all_timesteps"
- req_id: só letras, números, hífen e underscore
- text com pelo menos 10 caracteres
"""


def _strip_think(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.I)
    text = re.sub(r"<reasoning>[\s\S]*?</reasoning>", "", text, flags=re.I)
    return text.strip()


def _extract_json(text: str) -> dict[str, Any]:
    text = _strip_think(text or "")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # maior objeto JSON na resposta
        candidates = list(re.finditer(r"\{[\s\S]*\}", text))
        if not candidates:
            raise ValueError(f"LLM não devolveu JSON. Início da resposta: {text[:240]!r}")
        last_err: Exception | None = None
        for match in reversed(candidates):
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                last_err = exc
                continue
        raise ValueError(f"JSON inválido na resposta LLM: {last_err}") from last_err


def _normalize_requirement(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    """Corrige saídas comuns do LLM para o schema canónico."""
    data = dict(raw)
    rid = str(data.get("req_id") or f"RQ-AUTO-{idx+1:03d}")
    rid = re.sub(r"[^A-Za-z0-9_\-.]", "-", rid)
    if not re.match(r"^[A-Za-z0-9]", rid):
        rid = f"RQ-{rid}"
    data["req_id"] = rid
    data.setdefault("title", rid)
    text = str(data.get("text") or data.get("title") or "Requisito gerado automaticamente")
    if len(text) < 10:
        text = f"O sistema deve cumprir o requisito {rid}: {text}"
    data["text"] = text
    data.setdefault("rationale", "Gerado a partir de Markdown via LLM")
    data.setdefault("conops_ref", "CONOPS")
    data.setdefault("source", "markdown")
    data.setdefault("tags", [])

    level = str(data.get("level") or "system").lower().strip()
    if level not in ("mission", "system", "subsystem", "component"):
        level = "system"
    data["level"] = level

    vv = str(data.get("vv_method") or "test").lower().strip()
    if vv not in (
        "inspection",
        "analysis",
        "demonstration",
        "test",
        "similarity",
        "review_of_design",
    ):
        vv = "test"
    data["vv_method"] = vv

    priority = str(data.get("priority") or "high").lower().strip()
    if priority not in ("high", "medium", "low"):
        # LLMs inventam Critical/High/etc.
        if "crit" in priority or "alta" in priority or priority in ("h", "1"):
            priority = "high"
        elif "med" in priority or "média" in priority or "media" in priority:
            priority = "medium"
        elif "low" in priority or "baixa" in priority:
            priority = "low"
        else:
            priority = "high"
    data["priority"] = priority

    sc = data.get("success_criteria") or {}
    if not isinstance(sc, dict):
        sc = {}
    sc_type = str(sc.get("type") or "threshold").lower()
    if sc_type not in ("threshold", "range", "statistical"):
        sc_type = "threshold"
    sc["type"] = sc_type

    metric = str(sc.get("metric") or "batteryLevel")
    metric = metric.replace("speed.horizontal", "speed_horizontal")
    if metric in ("altitude", "altitude_m", "alt"):
        metric = "altitudeAGL"
    # Não inventar métricas de variação: forçar statistical+range
    variation_aliases = (
        "altitude_variation",
        "altitude_variation_m",
        "variation",
        "peak_to_peak",
        "amplitude",
    )
    if metric.lower() in variation_aliases or metric.lower().endswith("_variation"):
        base = "altitudeAGL" if "alt" in metric.lower() else metric.replace("_variation", "").replace("_m", "")
        if not base or base.lower() in variation_aliases:
            base = "altitudeAGL"
        metric = base if base else "altitudeAGL"
        sc_type = "statistical"
        sc["type"] = "statistical"
        sc["aggregation"] = "range"
        if "operator" not in sc:
            sc["operator"] = "<="
    sc["metric"] = metric

    if sc_type == "threshold":
        op = str(sc.get("operator") or ">=")
        if op not in (">=", "<=", ">", "<", "==", "!="):
            op = ">="
        sc["operator"] = op
        try:
            sc["value"] = float(sc.get("value", 0))
        except (TypeError, ValueError):
            sc["value"] = 0.0
        sc.setdefault("unit", "")
        sc.setdefault("tolerance", 0.0)
        scope = str(sc.get("scope") or "all_entities")
        allowed = {
            "all_timesteps",
            "all_flights",
            "final_state",
            "any_timestep",
            "all_entities",
            "per_entity",
        }
        if scope not in allowed:
            scope = "all_entities"
        sc["scope"] = scope
    elif sc_type == "range":
        try:
            sc["min_value"] = float(sc.get("min_value", 0))
            sc["max_value"] = float(sc.get("max_value", 100))
        except (TypeError, ValueError):
            sc["min_value"] = 0.0
            sc["max_value"] = 100.0
        sc.setdefault("unit", "")
        sc.setdefault("inclusive_min", True)
        sc.setdefault("inclusive_max", True)
        scope = str(sc.get("scope") or "all_entities")
        allowed = {
            "all_timesteps",
            "all_flights",
            "final_state",
            "any_timestep",
            "all_entities",
            "per_entity",
        }
        if scope not in allowed:
            scope = "all_entities"
        sc["scope"] = scope
    else:
        # statistical — janela live: range | max | min
        agg = str(sc.get("aggregation") or "range").lower().strip()
        if agg not in ("range", "max", "min"):
            # mean/etc. → forçar range se o texto/context sugerir variação; senão range default
            agg = "range"
        sc["aggregation"] = agg
        op = str(sc.get("operator") or "<=")
        if op not in (">=", "<=", ">", "<", "==", "!="):
            op = "<="
        sc["operator"] = op
        try:
            sc["value"] = float(sc.get("value", 0))
        except (TypeError, ValueError):
            sc["value"] = 0.0
        sc.setdefault("unit", "")
        sc.pop("percentile_value", None)
        sc.pop("scope", None)  # StatisticalCriteria schema sem scope

    data["success_criteria"] = sc
    return data


def normalize_llm_payload(parsed: dict[str, Any]) -> dict[str, Any]:
    reqs = parsed.get("requirements") or []
    if not isinstance(reqs, list) or not reqs:
        raise ValueError("LLM não retornou requirements")
    parsed["requirements"] = [
        _normalize_requirement(r if isinstance(r, dict) else {}, i) for i, r in enumerate(reqs)
    ]
    parsed.setdefault("sysml_notes", "")
    parsed.setdefault("metrics_needed", [])
    return parsed


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    # alguns modelos colocam o JSON só em reasoning
    reasoning = message.get("reasoning") or message.get("reasoning_content")
    if isinstance(reasoning, str) and "{" in reasoning:
        return reasoning
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                parts.append(str(p.get("text") or ""))
            elif isinstance(p, str):
                parts.append(p)
        return "\n".join(parts)
    return str(content or "")


async def interpret_requirements_markdown(markdown: str) -> dict[str, Any]:
    if not settings.llm_base_url:
        raise RuntimeError("LLM_BASE_URL não configurado")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": 0,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Documento de requisitos em Markdown:\n\n"
                    f"{markdown}\n\n"
                    "Devolva SOMENTE o JSON pedido."
                ),
            },
        ],
    }
    # Pedido de JSON object (Ollama OpenAI-compat pode ignorar)
    payload["response_format"] = {"type": "json_object"}

    timeout = httpx.Timeout(settings.llm_timeout_seconds, connect=30.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Ollama HTTP {response.status_code}: {response.text[:400]}"
                )
            data = response.json()
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"Timeout ao contactar LLM ({settings.llm_timeout_seconds}s). "
            "Tente um Markdown mais curto ou aumente LLM_TIMEOUT_SECONDS."
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Erro de rede até ao Ollama: {exc}") from exc

    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Resposta Ollama inesperada: {str(data)[:400]}") from exc

    content = _message_text(message if isinstance(message, dict) else {})
    parsed = _extract_json(content)
    return normalize_llm_payload(parsed)
