"""ReqValLive — app FastAPI local."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from reqvallive.api.routes import router
from reqvallive.config import settings

PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"
TEMPLATES_DIR = PACKAGE_DIR / "templates"

app = FastAPI(
    title="ReqValLive",
    description="Validação de requisitos em tempo real via MQTT + SysML V2",
    version="0.1.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(TEMPLATES_DIR / "index.html")


def run() -> None:
    uvicorn.run(
        "reqvallive.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
