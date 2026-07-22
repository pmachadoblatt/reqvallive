"""Probe antigo do Ollama — preferir GET /api/llm/probe na UI.

Credenciais vêm do ambiente / .env (LLM_BASE_URL, LLM_API_KEY).
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    _load_dotenv(root / ".env")
    base = os.environ.get("LLM_BASE_URL", "https://ollama.conceptio.com.br/v1").rstrip("/")
    key = os.environ.get("LLM_API_KEY", "")
    url = f"{base}/models"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    print(f"GET {url}")
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        print(r.status_code, r.text[:400])
    except Exception as exc:
        print(f"ERR: {exc}")


if __name__ == "__main__":
    main()
