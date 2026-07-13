"""Rotas REST do ReqValLive."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from simreqvalidator.schema.requirement import RequirementRecord
from simreqvalidator.schema.validator import SchemaValidator

from reqvallive.config import settings
from reqvallive.eval.live import is_mvp_supported, metric_name
from reqvallive.models.session import store
from reqvallive.mqtt.subscriber import mqtt_manager
from reqvallive.reports.html_report import build_html_report

router = APIRouter(prefix="/api")
_validator = SchemaValidator()


class ValidateBody(BaseModel):
    requirement: dict[str, Any] | None = None
    requirements: list[dict[str, Any]] | None = None


class SessionCreateBody(BaseModel):
    requirement: dict[str, Any] | None = None
    requirements: list[dict[str, Any]] | None = None
    mqtt_broker: str | None = None
    mqtt_port: int | None = None
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str | None = None


def _extract_one(body: ValidateBody | SessionCreateBody) -> dict[str, Any]:
    if body.requirement is not None:
        return body.requirement
    if body.requirements:
        return body.requirements[0]
    raise HTTPException(status_code=400, detail="Forneça 'requirement' ou 'requirements[0]'")


def _parse_requirement(data: dict[str, Any]) -> tuple[RequirementRecord, list[dict[str, Any]]]:
    # Aceita payload wrapped {requirements:[...]} colado por engano
    if "requirements" in data and isinstance(data["requirements"], list) and data.get("req_id") is None:
        if not data["requirements"]:
            raise HTTPException(status_code=400, detail="Lista requirements vazia")
        data = data["requirements"][0]

    req, issues = _validator.validate_single(data)
    issue_dicts = [
        {
            "code": getattr(i, "code", ""),
            "message": getattr(i, "message", str(i)),
            "severity": str(getattr(i, "severity", "")),
            "field": getattr(i, "field", None),
        }
        for i in issues
    ]
    if req is None:
        raise HTTPException(
            status_code=422,
            detail={"message": "Requisito inválido (Vampire/Schema)", "issues": issue_dicts},
        )
    return req, issue_dicts


@router.post("/requirements/validate")
def validate_requirement(body: ValidateBody) -> dict[str, Any]:
    data = _extract_one(body)
    req, issues = _parse_requirement(data)
    return {
        "ok": True,
        "supported_live": is_mvp_supported(req),
        "metric": metric_name(req),
        "requirement": req.model_dump(mode="json"),
        "issues": issues,
    }


@router.post("/sessions")
def create_session(body: SessionCreateBody) -> dict[str, Any]:
    data = _extract_one(body)
    req, issues = _parse_requirement(data)
    session = store.create(
        req,
        mqtt_broker=body.mqtt_broker or settings.mqtt_broker,
        mqtt_port=body.mqtt_port if body.mqtt_port is not None else settings.mqtt_port,
        mqtt_username=body.mqtt_username if body.mqtt_username is not None else settings.mqtt_username,
        mqtt_password=body.mqtt_password if body.mqtt_password is not None else settings.mqtt_password,
        mqtt_topic=body.mqtt_topic or settings.mqtt_topic,
    )
    public = session.to_public_dict()
    public["issues"] = issues
    return public


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return session.to_public_dict()


@router.post("/sessions/{session_id}/start")
def start_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not session.supported_live:
        raise HTTPException(
            status_code=400,
            detail="Critério/métrica não suportados no MVP live (use threshold|range + battery_level)",
        )
    mqtt_manager.start(session)
    return session.to_public_dict()


@router.post("/sessions/{session_id}/stop")
def stop_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    mqtt_manager.stop(session_id)
    session.measuring = False
    return session.to_public_dict()


@router.get("/sessions/{session_id}/sysml")
def download_sysml(session_id: str) -> StreamingResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    filename = f"{session.requirement.req_id}.sysml"
    return StreamingResponse(
        iter([session.sysml_text.encode("utf-8")]),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/report")
def download_report(session_id: str) -> HTMLResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return HTMLResponse(build_html_report(session))


@router.get("/sessions/{session_id}/stream")
async def stream_session(session_id: str, request: Request) -> StreamingResponse:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    async def event_generator():
        last_fingerprint: str | None = None
        while True:
            if await request.is_disconnected():
                break
            current = store.get(session_id)
            if current is None:
                break
            public = current.to_public_dict()
            fingerprint = f"{public['measuring']}:{public['mqtt_connected']}:{len(public['samples'])}:{public['last_value']}:{public['last_ok']}"
            if fingerprint != last_fingerprint:
                last_fingerprint = fingerprint
                yield f"data: {json.dumps(public)}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
