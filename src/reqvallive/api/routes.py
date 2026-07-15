"""Rotas REST do ReqValLive."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel
import httpx

from reqvallive.config import settings
from reqvallive.eval.criteria_gate import success_criteria_model_doc
from reqvallive.eval.live import is_mvp_supported
from reqvallive.llm.client import interpret_requirements_markdown
from reqvallive.models.session import store
from reqvallive.mqtt.subscriber import mqtt_manager
from reqvallive.reports.html_report import build_html_report

router = APIRouter(prefix="/api")

_EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "examples"


class MdInterpretBody(BaseModel):
    markdown: str
    mqtt_broker: str | None = None
    mqtt_port: int | None = None
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str | None = None


class SessionCreateBody(BaseModel):
    requirement: dict[str, Any] | None = None
    requirements: list[dict[str, Any]] | None = None
    source_markdown: str | None = None
    llm_notes: str | None = None
    mqtt_broker: str | None = None
    mqtt_port: int | None = None
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str | None = None


class MqttConfigBody(BaseModel):
    mqtt_broker: str | None = None
    mqtt_port: int | None = None
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str | None = None


def _mqtt_kwargs(body: Any) -> dict[str, Any]:
    return {
        "mqtt_broker": getattr(body, "mqtt_broker", None) or settings.mqtt_broker,
        "mqtt_port": getattr(body, "mqtt_port", None)
        if getattr(body, "mqtt_port", None) is not None
        else settings.mqtt_port,
        "mqtt_username": getattr(body, "mqtt_username", None)
        if getattr(body, "mqtt_username", None) is not None
        else settings.mqtt_username,
        "mqtt_password": getattr(body, "mqtt_password", None)
        if getattr(body, "mqtt_password", None) is not None
        else settings.mqtt_password,
        "mqtt_topic": getattr(body, "mqtt_topic", None) or settings.mqtt_topic,
    }


@router.get("/defaults")
def defaults() -> dict[str, Any]:
    return {
        "mqtt_broker": settings.mqtt_broker,
        "mqtt_port": settings.mqtt_port,
        "mqtt_username": settings.mqtt_username,
        "mqtt_topic": settings.mqtt_topic,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_configured": bool(settings.llm_api_key),
    }


@router.post("/requirements/from-markdown")
async def from_markdown(body: MdInterpretBody) -> dict[str, Any]:
    if not body.markdown.strip():
        raise HTTPException(status_code=400, detail="Markdown vazio")
    try:
        parsed = await interpret_requirements_markdown(body.markdown)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha LLM: {exc}") from exc

    reqs = parsed.get("requirements") or []
    try:
        session = store.create_from_requirements(
            reqs,
            source_markdown=body.markdown,
            llm_notes=str(parsed.get("sysml_notes", "")),
            **_mqtt_kwargs(body),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Requisitos gerados pelo LLM inválidos para o schema: {exc}",
        ) from exc

    public = session.to_public_dict()
    public["metrics_needed"] = parsed.get("metrics_needed", [])
    public["llm_notes"] = parsed.get("sysml_notes", "")
    return public


@router.post("/requirements/from-markdown-file")
async def from_markdown_file(
    file: UploadFile = File(...),
    mqtt_broker: str | None = Form(None),
    mqtt_port: int | None = Form(None),
    mqtt_username: str | None = Form(None),
    mqtt_password: str | None = Form(None),
    mqtt_topic: str | None = Form(None),
) -> dict[str, Any]:
    raw = (await file.read()).decode("utf-8")
    body = MdInterpretBody(
        markdown=raw,
        mqtt_broker=mqtt_broker,
        mqtt_port=mqtt_port,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_topic=mqtt_topic,
    )
    return await from_markdown(body)


@router.post("/sessions")
def create_session(body: SessionCreateBody) -> dict[str, Any]:
    if body.requirements:
        reqs = body.requirements
    elif body.requirement:
        reqs = [body.requirement]
    else:
        raise HTTPException(400, detail="Forneça requirement ou requirements")
    try:
        session = store.create_from_requirements(
            reqs,
            source_markdown=body.source_markdown or "",
            llm_notes=body.llm_notes or "",
            **_mqtt_kwargs(body),
        )
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    return session.to_public_dict()


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    return session.to_public_dict()


@router.post("/sessions/{session_id}/mqtt")
def update_mqtt(session_id: str, body: MqttConfigBody) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    if body.mqtt_broker is not None:
        session.mqtt_broker = body.mqtt_broker
    if body.mqtt_port is not None:
        session.mqtt_port = body.mqtt_port
    if body.mqtt_username is not None:
        session.mqtt_username = body.mqtt_username
    if body.mqtt_password is not None:
        session.mqtt_password = body.mqtt_password
    if body.mqtt_topic is not None:
        session.mqtt_topic = body.mqtt_topic
    return session.to_public_dict()


@router.get("/criteria/model")
def criteria_model() -> dict[str, Any]:
    """Modelo pedagógico de Success Criteria (MSFC / SIS-08 Methods)."""
    return success_criteria_model_doc()


@router.get("/criteria/example.md")
def criteria_example_md() -> PlainTextResponse:
    """Exemplo bem feito de Success Criteria (download)."""
    path = _EXAMPLES_DIR / "success_criteria_model.md"
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = success_criteria_model_doc().get("markdown_example") or ""
    return PlainTextResponse(
        text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="success_criteria_modelo.md"'},
    )


@router.post("/sessions/{session_id}/criteria/evaluate")
def reevaluate_criteria(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    session.refresh_criteria_gate()
    return session.to_public_dict()


def _require_gate_accept(session) -> None:
    if not session.gate_allows_measurement():
        gate = session.criteria_gate.to_dict() if session.criteria_gate else {}
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Medição bloqueada: Success Criteria não aprovados no gate "
                    "(MSFC: critérios devem estar maduros antes da actividade de V&V)."
                ),
                "criteria_gate": gate,
            },
        )


@router.post("/sessions/{session_id}/connect")
def connect_mqtt(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    _require_gate_accept(session)
    mqtt_manager.connect(session)
    return session.to_public_dict()


@router.post("/sessions/{session_id}/disconnect")
def disconnect_mqtt(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    mqtt_manager.disconnect(session_id)
    return session.to_public_dict()


@router.post("/sessions/{session_id}/start")
def start_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    _require_gate_accept(session)
    if not all(is_mvp_supported(r) for r in session.requirements):
        raise HTTPException(400, detail="Há requisitos com critério não suportado (use threshold/range)")
    if not session.connected:
        mqtt_manager.connect(session)
    session.start_measurement()
    return session.to_public_dict()


@router.post("/sessions/{session_id}/stop")
def stop_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    session.stop_measurement()
    # Mantém MQTT ligado para nova corrida; resultados ficam congelados
    return session.to_public_dict()


@router.get("/sessions/{session_id}/sysml")
def download_sysml(session_id: str) -> StreamingResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    filename = f"{session.primary_requirement().req_id}.sysml"
    return StreamingResponse(
        iter([session.sysml_text.encode("utf-8")]),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/model.md")
def download_model_md(session_id: str) -> StreamingResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    filename = f"{session.primary_requirement().req_id}_model.md"
    return StreamingResponse(
        iter([session.model_markdown.encode("utf-8")]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/report")
def download_report(session_id: str) -> HTMLResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")
    return HTMLResponse(build_html_report(session))


@router.get("/sessions/{session_id}/stream")
async def stream_session(session_id: str, request: Request) -> StreamingResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, detail="Sessão não encontrada")

    async def event_generator():
        last_fp = None
        while True:
            if await request.is_disconnected():
                break
            current = store.get(session_id)
            if current is None:
                break
            public = current.to_public_dict()
            fp = (
                f"{public['mqtt_status']}:{public['measuring']}:{public.get('measurement_ended')}"
                f":{public['summary']}:{len(public.get('message_log', []))}:{public.get('overall_ok')}"
            )
            if fp != last_fp:
                last_fp = fp
                yield f"data: {json.dumps(public)}\n\n"
            await asyncio.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/llm/probe")
async def llm_probe() -> dict[str, Any]:
    """Testa conectividade com Ollama / OpenAI-compatible no lab."""
    base = settings.llm_base_url.rstrip("/")
    root = base[:-3] if base.endswith("/v1") else base
    headers: dict[str, str] = {}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    result: dict[str, Any] = {
        "base_url": settings.llm_base_url,
        "model": settings.llm_model,
        "api_key_set": bool(settings.llm_api_key),
        "tags": None,
        "models": None,
        "chat": None,
        "ok": False,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Ollama nativo
            try:
                tags = await client.get(f"{root}/api/tags", headers=headers)
                result["tags"] = {"status": tags.status_code, "body": tags.text[:800]}
            except Exception as exc:
                result["tags"] = {"error": str(exc)}

            # OpenAI-compatible models
            try:
                models = await client.get(f"{base}/models", headers=headers)
                result["models"] = {"status": models.status_code, "body": models.text[:800]}
            except Exception as exc:
                result["models"] = {"error": str(exc)}

            chat = await client.post(
                f"{base}/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "model": settings.llm_model,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": "Responda exatamente: PONG"}],
                },
            )
            result["chat"] = {"status": chat.status_code, "body": chat.text[:800]}
            result["ok"] = chat.status_code < 400
            if not result["ok"]:
                result["error"] = f"chat HTTP {chat.status_code}"
    except Exception as exc:
        result["error"] = str(exc)

    return result


@router.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "llm_configured": bool(settings.llm_api_key)}
