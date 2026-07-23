"""Garante Aggregation.RANGE no Sim_Req_Validator (pasta irmã).

O ReqValLive usa aggregation=range para variação temporal live.
O schema Vampire no lab já tem o enum; em casa, se a cópia for antiga,
este script adiciona a linha em falta.

Uso (a partir de reqvallive/):
    python scripts/ensure_simreq_range.py
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = 'RANGE = "range"'
LINE = '    RANGE = "range"         # Peak-to-peak: max(série) − min(série)\n'
ANCHOR = '    MIN = "min"\n'


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    target = root / "Sim_Req_Validator" / "src" / "simreqvalidator" / "schema" / "success_criteria.py"
    if not target.is_file():
        print(f"ERRO: não encontrei {target}")
        print("Coloque Sim_Req_Validator como pasta IRMÃ de reqvallive.")
        return 1

    text = target.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"OK: Aggregation.RANGE já existe em {target}")
        return 0

    if ANCHOR not in text:
        print(f"ERRO: âncora MIN = \"min\" não encontrada em {target}")
        return 1

    updated = text.replace(ANCHOR, ANCHOR + LINE, 1)
    target.write_text(updated, encoding="utf-8")
    print(f"Atualizado: adicionado Aggregation.RANGE em {target}")
    print("Reinstale: pip install -e ../Sim_Req_Validator")
    return 0


if __name__ == "__main__":
    sys.exit(main())
