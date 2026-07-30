#!/usr/bin/env python3
"""Probe SysON local (Docker) — projetos e requisitos via REST.

Uso:
  .\\.venv\\Scripts\\Activate.ps1
  python scripts/probe_syson.py
  python scripts/probe_syson.py --req RQ_01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reqvallive.config import settings
from reqvallive.syson import SysonClient, SysonError, probe_summary, settings_from_env
from reqvallive.sysml.import_catia import parse_sysml_export


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe SysON REST API (local)")
    parser.add_argument("--req", default="RQ_", help="Substring do nome do requisito")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Valida models/syson/reqvallive_demo.sysml com o parser do app",
    )
    args = parser.parse_args()

    if args.demo:
        demo = ROOT / "models" / "syson" / "reqvallive_demo.sysml"
        text = demo.read_text(encoding="utf-8")
        parsed = parse_sysml_export(text)
        tagged = [r for r in parsed if r.tagged_for_verification]
        print(f"Demo: {demo}")
        print(f"Requisitos com _go_to_verification: {len(tagged)}")
        for r in tagged:
            sc = r.success_criteria or {}
            print(
                f"  - {r.name}: metric={sc.get('metric')} "
                f"{sc.get('operator')} {sc.get('value')}"
            )
        return 0 if tagged else 1

    cfg = settings_from_env(settings)
    print(f"Base: {cfg.base_url}")
    print(f"API:  {cfg.base_url.rstrip('/')}{cfg.api_prefix}")

    try:
        with SysonClient(cfg) as client:
            summary = probe_summary(client, req_filter=args.req)
    except SysonError as exc:
        print(f"ERRO: {exc}")
        if exc.body:
            print(exc.body)
        return 1
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"ERRO de ligacao: {exc}")
        print("Confirme: .\\deploy\\syson\\up.ps1  e  http://localhost:8081")
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary.get("health", {}).get("ok"):
        return 1
    if not summary.get("requirements"):
        print(
            f"\nAviso: 0 requisitos com filtro '{args.req}'. "
            "Crie um RequirementUsage na UI ou importe models/syson/reqvallive_demo.sysml."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
