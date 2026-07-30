#!/usr/bin/env python3
"""Spike Fase 1 — probe Teamwork Cloud SysML v2 REST (lab CONCEPTIO).

Uso:
  .\\.venv\\Scripts\\Activate.ps1
  # no .env: TWC_USERNAME=pedroblatt  TWC_PASSWORD=...  (ou TWC_TOKEN=...)
  python scripts/probe_twc.py
  python scripts/probe_twc.py --req RQ_BAT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reqvallive.config import settings
from reqvallive.twc import TwcClient, TwcError, probe_summary, settings_from_env


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe TWC SysML v2 REST API")
    parser.add_argument("--req", default="RQ_", help="Substring do nome do requisito")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Só testa se /sysmlv2-api/api/projects responde (401/200)",
    )
    args = parser.parse_args()

    twc = settings_from_env(settings)
    print(f"Base: {twc.base_url}")
    print(f"API:  {twc.base_url.rstrip('/')}{twc.sysml_api_prefix}")
    print(f"Auth: {twc.base_url.rstrip('/')}{twc.auth_login_path}")
    print(f"SSL verify: {twc.verify_ssl}")

    if args.discover:
        import httpx

        url = twc.base_url.rstrip("/") + twc.sysml_api_prefix.rstrip("/") + "/projects"
        r = httpx.get(url, verify=twc.verify_ssl, timeout=10.0)
        print(f"GET {url} -> HTTP {r.status_code} (401=API viva sem token; 200=ok)")
        return 0 if r.status_code in (200, 401) else 1

    try:
        with TwcClient(twc) as client:
            summary = probe_summary(client, req_filter=args.req)
    except TwcError as exc:
        print(f"ERRO: {exc}")
        if exc.body:
            print(exc.body)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("project_count", 0) == 0:
        print(
            "\nAviso: 0 projetos. Faça Collaborate → Publish do modelo SysML v2 "
            "ou confirme o user/token."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
