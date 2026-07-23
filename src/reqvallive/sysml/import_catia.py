"""Importação de requisitos SysML v2 exportados do CATIA Magic.

Contrato (Prof. Christopher): o campo ``doc`` marca o que o APP deve olhar,
como um markdown de parsing. Tag obrigatória:

    _go_to_verification

No ``doc`` pode vir também o Success Criteria em JSON fenced ou linhas chave:valor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

GO_TO_VERIFICATION = "_go_to_verification"

_REQ_START = re.compile(
    r"requirement\s*(?:\[[^\]]*\])?\s+(?P<name>[A-Za-z_][\w-]*)\s*\{",
    re.IGNORECASE,
)

_DOC_COMMENT = re.compile(
    r"doc\s*(?:\[[^\]]*\])?\s*/\*(?P<body>.*?)\*/",
    re.DOTALL | re.IGNORECASE,
)
_DOC_STRING = re.compile(
    r"doc\s*(?:\[[^\]]*\])?\s*(?P<q>\"\"\"|'''|\")(?P<body>.*?)(?P=q)",
    re.DOTALL | re.IGNORECASE,
)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


@dataclass
class ParsedCatiaRequirement:
    name: str
    doc_raw: str
    tagged_for_verification: bool
    text: str = ""
    success_criteria: dict[str, Any] | None = None
    vv_method: str = "test"
    level: str = "system"
    priority: str = "high"
    tags: list[str] = field(default_factory=list)
    parse_notes: list[str] = field(default_factory=list)

    def to_requirement_dict(self) -> dict[str, Any]:
        sc = self.success_criteria or {
            "type": "threshold",
            "metric": "batteryLevel",
            "operator": ">=",
            "value": 0.0,
            "unit": "",
            "scope": "all_entities",
            "tolerance": 0.0,
        }
        text = self.text.strip()
        if len(text) < 10:
            text = (
                f"Requisito {self.name} marcado para verificação "
                f"(_go_to_verification) no export CATIA."
            )
        return {
            "req_id": self.name,
            "title": self.name,
            "text": text,
            "rationale": "Importado do CATIA Magic (doc / _go_to_verification)",
            "level": self.level,
            "vv_method": self.vv_method,
            "priority": self.priority,
            "conops_ref": "CATIA",
            "source": "catia_sysml_export",
            "success_criteria": sc,
            "tags": list(self.tags) or ["catia", "go_to_verification"],
        }


def _extract_balanced_body(text: str, open_brace_index: int) -> str | None:
    """Devolve o conteúdo entre ``{`` e o ``}`` correspondente, ignorando
    comentários ``/* */``, ``//`` e strings."""
    if open_brace_index < 0 or open_brace_index >= len(text) or text[open_brace_index] != "{":
        return None
    i = open_brace_index + 1
    depth = 1
    n = len(text)
    while i < n and depth > 0:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            if end < 0:
                return None
            i = end + 2
            continue
        if ch == "/" and nxt == "/":
            end = text.find("\n", i + 2)
            i = n if end < 0 else end + 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : i]
        i += 1
    return None


def _extract_doc(body: str) -> str:
    m = _DOC_COMMENT.search(body)
    if m:
        return m.group("body").strip()
    m = _DOC_STRING.search(body)
    if m:
        return m.group("body").strip()
    return ""


def _parse_kv_lines(doc: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in doc.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("```"):
            continue
        if s.startswith("_"):
            continue
        if ":" not in s:
            continue
        key, _, val = s.partition(":")
        key = key.strip().lower().replace(" ", "_")
        val = val.strip().strip('"').strip("'")
        if key and val:
            out[key] = val
    return out


def _parse_success_criteria(doc: str, notes: list[str]) -> dict[str, Any] | None:
    fence = _JSON_FENCE.search(doc)
    if fence:
        try:
            data = json.loads(fence.group(1))
            if isinstance(data, dict) and data.get("type"):
                return data
            if isinstance(data, dict) and "metric" in data:
                data.setdefault("type", "threshold")
                return data
        except json.JSONDecodeError as exc:
            notes.append(f"JSON no doc inválido: {exc}")

    brace = re.search(r"\{[^{}]*\"metric\"[^{}]*\}", doc, re.DOTALL)
    if brace:
        try:
            data = json.loads(brace.group(0))
            if isinstance(data, dict):
                data.setdefault("type", "threshold")
                return data
        except json.JSONDecodeError:
            pass

    kv = _parse_kv_lines(doc)
    if "metric" in kv and ("value" in kv or ("min_value" in kv and "max_value" in kv)):
        ctype = (kv.get("type") or "threshold").lower()
        if ctype == "range":
            try:
                return {
                    "type": "range",
                    "metric": kv["metric"],
                    "min_value": float(kv.get("min_value", 0)),
                    "max_value": float(kv.get("max_value", 100)),
                    "unit": kv.get("unit", ""),
                    "scope": kv.get("scope", "all_entities"),
                    "inclusive_min": True,
                    "inclusive_max": True,
                }
            except ValueError:
                notes.append("min_value/max_value não numéricos")
                return None
        if ctype == "statistical":
            try:
                return {
                    "type": "statistical",
                    "metric": kv["metric"],
                    "aggregation": kv.get("aggregation", "range"),
                    "operator": kv.get("operator", "<="),
                    "value": float(kv.get("value", 0)),
                    "unit": kv.get("unit", ""),
                }
            except ValueError:
                notes.append("value estatístico não numérico")
                return None
        try:
            return {
                "type": "threshold",
                "metric": kv["metric"],
                "operator": kv.get("operator", ">="),
                "value": float(kv.get("value", 0)),
                "unit": kv.get("unit", ""),
                "scope": kv.get("scope", "all_entities"),
                "tolerance": float(kv.get("tolerance", 0) or 0),
            }
        except ValueError:
            notes.append("value do threshold não numérico")
            return None
    return None


def _infer_text(doc: str, kv: dict[str, str]) -> str:
    if kv.get("text"):
        return kv["text"]
    lines = []
    for line in doc.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("_") or s.startswith("```") or s.startswith("{"):
            continue
        if re.match(
            r"^(type|metric|operator|value|unit|scope|aggregation|min_value|max_value|tolerance|vv_method|level|priority)\s*:",
            s,
            re.I,
        ):
            continue
        if s.startswith("#"):
            s = s.lstrip("#").strip()
        lines.append(s)
    return " ".join(lines).strip()


def parse_sysml_export(text: str) -> list[ParsedCatiaRequirement]:
    """Extrai requisitos com tag _go_to_verification do textual SysML v2."""
    found: list[ParsedCatiaRequirement] = []
    src = text or ""
    for m in _REQ_START.finditer(src):
        name = m.group("name")
        brace_at = m.end() - 1
        body = _extract_balanced_body(src, brace_at)
        if body is None:
            continue
        doc = _extract_doc(body)
        tagged = GO_TO_VERIFICATION in doc
        notes: list[str] = []
        kv = _parse_kv_lines(doc)
        sc = _parse_success_criteria(doc, notes) if tagged else None
        if tagged and sc is None:
            notes.append(
                "Tag de verificação presente, mas Success Criteria não encontrado no doc "
                "(use JSON ```json ...``` ou linhas metric:/operator:/value:)."
            )
        found.append(
            ParsedCatiaRequirement(
                name=name,
                doc_raw=doc,
                tagged_for_verification=tagged,
                text=_infer_text(doc, kv),
                success_criteria=sc,
                vv_method=(kv.get("vv_method") or "test").lower(),
                level=(kv.get("level") or "system").lower(),
                priority=(kv.get("priority") or "high").lower(),
                tags=["catia", "go_to_verification"] if tagged else ["catia"],
                parse_notes=notes,
            )
        )
    return found


def requirements_for_verification(text: str) -> list[ParsedCatiaRequirement]:
    return [r for r in parse_sysml_export(text) if r.tagged_for_verification]


def summary_dict(parsed: list[ParsedCatiaRequirement]) -> dict[str, Any]:
    tagged = [r for r in parsed if r.tagged_for_verification]
    return {
        "total_requirements": len(parsed),
        "tagged_for_verification": len(tagged),
        "ready_with_sc": sum(1 for r in tagged if r.success_criteria),
        "tag": GO_TO_VERIFICATION,
        "requirements": [
            {
                "name": r.name,
                "tagged": r.tagged_for_verification,
                "has_success_criteria": r.success_criteria is not None,
                "text_preview": (r.text[:120] + "…") if len(r.text) > 120 else r.text,
                "parse_notes": r.parse_notes,
                "success_criteria": r.success_criteria,
            }
            for r in parsed
        ],
    }
