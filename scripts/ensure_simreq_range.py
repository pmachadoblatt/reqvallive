"""Garante Aggregation.RANGE no Sim_Req_Validator (vendor ou pasta irmã).

Uso (a partir de reqvallive/):
    python scripts/ensure_simreq_range.py
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = 'RANGE = "range"'
LINE = '    RANGE = "range"         # Peak-to-peak: max(série) − min(série)\n'
ANCHOR = '    MIN = "min"\n'


def _candidates(root: Path) -> list[Path]:
    return [
        root / "vendor" / "Sim_Req_Validator" / "src" / "simreqvalidator" / "schema" / "success_criteria.py",
        root.parent / "Sim_Req_Validator" / "src" / "simreqvalidator" / "schema" / "success_criteria.py",
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    targets = [p for p in _candidates(root) if p.is_file()]
    if not targets:
        print("ERRO: não encontrei Sim_Req_Validator em vendor/ nem como pasta irmã.")
        print("Faça git pull — o schema deve estar em vendor/Sim_Req_Validator.")
        return 1

    rc = 0
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if MARKER in text:
            print(f"OK: Aggregation.RANGE já existe em {target}")
            continue
        if ANCHOR not in text:
            print(f"ERRO: âncora MIN = \"min\" não encontrada em {target}")
            rc = 1
            continue
        updated = text.replace(ANCHOR, ANCHOR + LINE, 1)
        target.write_text(updated, encoding="utf-8")
        print(f"Atualizado: adicionado Aggregation.RANGE em {target}")
        print("Reinstale: pip install -e ./vendor/Sim_Req_Validator")
    return rc


if __name__ == "__main__":
    sys.exit(main())
