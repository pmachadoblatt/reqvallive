"""Cliente LLM OpenAI-compatible (Ollama / Open WebUI no lab)."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from reqvallive.config import settings

SYSTEM_PROMPT = """Você é um engenheiro de sistemas MBSE especializado em SysML V2 e V&V.
Recebe um documento Markdown com requisitos de missão.
Extraia requisitos verificáveis e critérios de sucesso mensuráveis ligados a telemetria MQTT de drones.

Responda APENAS com JSON válido (sem markdown fences) no formato:
{
  "requirements": [
    {
      "req_id": "RQ-...",
      "title": "...",
      "text": "O sistema deve...",
      "rationale": "...",
      "level": "system",
      "vv_method": "test",
      "priority": "high",
      "conops_ref": "",
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
      "tags": []
    }
  ],
  "sysml_notes": "resumo curto do modelo",
  "metrics_needed": ["batteryLevel"]
}

Métricas preferidas alinhadas ao payload do lab:
- batteryLevel (bateria do drone)
- altitudeAGL
- distanceToHome
- min_separation_m (distância mínima entre drones)
- speed.horizontal (use metric speed_horizontal se necessário)

Para vários drones, use scope "all_entities" ou "all_timesteps".
Só use type threshold ou range.
Se o texto for vago, invente critérios mensuráveis razoáveis e marque em rationale.
"""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


async def interpret_requirements_markdown(markdown: str) -> dict[str, Any]:
    if not settings.llm_api_key and not settings.llm_base_url:
        raise RuntimeError("LLM não configurado (LLM_BASE_URL / LLM_API_KEY)")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    payload = {
        "model": settings.llm_model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Documento de requisitos em Markdown:\n\n"
                    f"{markdown}\n\n"
                    "Gere o JSON de requisitos e métricas."
                ),
            },
        ],
    }

    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    if "requirements" not in parsed or not parsed["requirements"]:
        raise ValueError("LLM não retornou requirements")
    return parsed


def interpret_requirements_markdown_sync(markdown: str) -> dict[str, Any]:
    """Wrapper síncrono para testes / fallback."""
    import anyio

    return anyio.run(interpret_requirements_markdown, markdown)
