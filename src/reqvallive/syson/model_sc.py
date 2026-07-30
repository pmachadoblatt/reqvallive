"""Extrai Success Criteria de elementos do modelo SysON (não do Documentation)."""

from __future__ import annotations

import re
from typing import Any

# Nomes de atributos reconhecidos (case-insensitive).
_ATTR_ALIASES = {
    "sctype": "type",
    "sc_type": "type",
    "type": "type",
    "metric": "metric",
    "operator": "operator",
    "value": "value",
    "unit": "unit",
    "scope": "scope",
    "tolerance": "tolerance",
    "min_value": "min_value",
    "minvalue": "min_value",
    "max_value": "max_value",
    "maxvalue": "max_value",
    "aggregation": "aggregation",
}

_ATTR_LINE = re.compile(
    r"\battribute\b\s+"
    r"(?:(?P<name>[A-Za-z_][\w]*)\s*)?"
    r"(?::[^;=]*)?"
    r"(?:=\s*(?P<val>[^;]+))?"
    r"\s*;",
    re.IGNORECASE,
)

# UI SysON (F2): o rótulo inteiro vira declaredName, ex. metric = "batteryLevel"
_INLINE_ATTR_ASSIGN = re.compile(
    r"^\s*(?P<name>[A-Za-z_][\w]*)\s*=\s*(?P<val>.+?)\s*$"
)


def _coerce_value(raw: str) -> Any:
    s = raw.strip().strip('"').strip("'")
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    return s


def attrs_from_textual_block(body: str) -> dict[str, Any]:
    """Lê `attribute name = value;` de um bloco textual SysML."""
    out: dict[str, Any] = {}
    for m in _ATTR_LINE.finditer(body or ""):
        name = (m.group("name") or "").strip()
        val = m.group("val")
        if not name or val is None:
            continue
        key = _ATTR_ALIASES.get(name.lower())
        if key:
            out[key] = _coerce_value(val)
    return out


def extract_success_criteria_item_body(req_body: str) -> str | None:
    """Devolve o corpo de `item SuccessCriteria { ... }` se existir."""
    m = re.search(
        r"\bitem\b\s+SuccessCriteria\s*\{",
        req_body or "",
        re.IGNORECASE,
    )
    if not m:
        return None
    # extrair bloco balanceado a partir do `{`
    start = m.end() - 1
    depth = 0
    i = start
    while i < len(req_body):
        ch = req_body[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return req_body[start + 1 : i]
        i += 1
    return None


def success_criteria_from_attr_map(attrs: dict[str, Any]) -> dict[str, Any] | None:
    """Monta o dict Vampire a partir de um mapa de atributos do modelo."""
    if not attrs or "metric" not in attrs:
        return None
    ctype = str(attrs.get("type") or "threshold").lower()
    metric = str(attrs["metric"])
    if ctype == "range":
        try:
            return {
                "type": "range",
                "metric": metric,
                "min_value": float(attrs.get("min_value", 0)),
                "max_value": float(attrs.get("max_value", 100)),
                "unit": str(attrs.get("unit") or ""),
                "scope": str(attrs.get("scope") or "all_entities"),
                "inclusive_min": True,
                "inclusive_max": True,
            }
        except (TypeError, ValueError):
            return None
    if ctype == "statistical":
        try:
            return {
                "type": "statistical",
                "metric": metric,
                "aggregation": str(attrs.get("aggregation") or "range"),
                "operator": str(attrs.get("operator") or "<="),
                "value": float(attrs["value"]),
                "unit": str(attrs.get("unit") or ""),
            }
        except (TypeError, ValueError, KeyError):
            return None
    # threshold
    if "value" not in attrs:
        return None
    try:
        return {
            "type": "threshold",
            "metric": metric,
            "operator": str(attrs.get("operator") or ">="),
            "value": float(attrs["value"]),
            "unit": str(attrs.get("unit") or ""),
            "scope": str(attrs.get("scope") or "all_entities"),
            "tolerance": float(attrs.get("tolerance") or 0),
        }
    except (TypeError, ValueError):
        return None


def success_criteria_from_requirement_textual(req_body: str) -> dict[str, Any] | None:
    """SC a partir do corpo textual do requirement (item SuccessCriteria ou atributos)."""
    item_body = extract_success_criteria_item_body(req_body)
    if item_body is not None:
        sc = success_criteria_from_attr_map(attrs_from_textual_block(item_body))
        if sc:
            return sc
    return success_criteria_from_attr_map(attrs_from_textual_block(req_body))


def _element_name(el: dict[str, Any]) -> str:
    for key in ("declaredName", "name", "qualifiedName"):
        val = el.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _id_of(obj: dict[str, Any] | None) -> str | None:
    if not isinstance(obj, dict):
        return None
    for key in ("@id", "id", "elementId"):
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _looks_like_attribute(el: dict[str, Any]) -> bool:
    t = str(el.get("@type") or "")
    return "Attribute" in t or t.endswith("AttributeUsage")


def _looks_like_item(el: dict[str, Any]) -> bool:
    t = str(el.get("@type") or "")
    return "ItemUsage" in t or t == "ItemDefinition"


def attr_key_and_value_from_element(
    el: dict[str, Any],
    elements_by_id: dict[str, dict[str, Any]] | None = None,
) -> tuple[str | None, Any | None]:
    """Nome canónico + valor — inclui padrão F2 `metric = \"batteryLevel\"` no declaredName."""
    name = _element_name(el)
    if not name:
        return None, None
    inline = _INLINE_ATTR_ASSIGN.match(name)
    if inline:
        key = _ATTR_ALIASES.get(inline.group("name").lower())
        if key:
            return key, _coerce_value(inline.group("val"))
    key = _ATTR_ALIASES.get(name.lower())
    if not key:
        return None, None
    return key, _attr_value_from_element(el, elements_by_id)


def _attr_value_from_element(
    el: dict[str, Any],
    elements_by_id: dict[str, dict[str, Any]] | None = None,
) -> Any | None:
    """Resolve valor de AttributeUsage via FeatureValue → Literal*."""
    by_id = elements_by_id or {}

    def _resolve(obj: Any, depth: int = 0) -> Any | None:
        if depth > 6 or obj is None:
            return None
        if isinstance(obj, (int, float, bool)):
            return obj
        if isinstance(obj, str):
            s = obj.strip()
            if not s or s == "[]":
                return None
            return _coerce_value(s)
        if isinstance(obj, dict):
            # LiteralString / LiteralRational / etc.
            t = str(obj.get("@type") or "")
            if "Literal" in t and "value" in obj:
                return _resolve(obj.get("value"), depth + 1)
            if "@id" in obj and len(obj) <= 2:
                ref = by_id.get(obj["@id"])
                if ref is not None:
                    return _resolve(ref, depth + 1)
            for sub in ("value", "body", "text", "@value"):
                if sub in obj and obj[sub] is not None:
                    got = _resolve(obj[sub], depth + 1)
                    if got is not None:
                        return got
        return None

    # Caminho SysON: attribute.valuation → FeatureValue → Literal*.value
    valuation = el.get("valuation")
    if isinstance(valuation, dict):
        fv = by_id.get(valuation.get("@id") or "") if valuation.get("@id") else valuation
        if fv is None and valuation.get("@id"):
            fv = valuation
        if isinstance(fv, dict):
            got = _resolve(fv.get("value"), 0)
            if got is not None:
                return got
            got = _resolve(fv.get("ownedMemberElement") or fv.get("memberElement"), 0)
            if got is not None:
                return got

    for key in ("value", "operatorExpression", "ownedExpression"):
        got = _resolve(el.get(key), 0)
        if got is not None:
            return got
    return None


def success_criteria_from_syson_elements(
    requirement: dict[str, Any],
    elements_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Lê SC a partir de ItemUsage SuccessCriteria ou atributos do requirement (REST)."""
    req_id = _id_of(requirement)
    # 1) Item SuccessCriteria cujo owner é o requirement
    sc_item = None
    for el in elements_by_id.values():
        if not _looks_like_item(el):
            continue
        if _element_name(el).lower() != "successcriteria":
            continue
        owner = el.get("owner") or el.get("owningNamespace") or el.get("owningUsage")
        if _id_of(owner if isinstance(owner, dict) else None) == req_id:
            sc_item = el
            break

    container_id = _id_of(sc_item) if sc_item else req_id
    attrs: dict[str, Any] = {}
    for el in elements_by_id.values():
        if not _looks_like_attribute(el):
            continue
        owner = el.get("owner") or el.get("owningNamespace") or el.get("owningUsage")
        if _id_of(owner if isinstance(owner, dict) else None) != container_id:
            continue
        key, val = attr_key_and_value_from_element(el, elements_by_id)
        if key and val is not None:
            attrs[key] = val

    return success_criteria_from_attr_map(attrs)


def requirement_dict_from_syson(
    *,
    name: str,
    element_id: str,
    documentation_id: str | None,
    doc_body: str,
    project_id: str,
    project_name: str,
    success_criteria: dict[str, Any] | None,
) -> dict[str, Any]:
    """Monta dict de requisito. SC tem de vir do modelo (pode ser None → gate REJECT)."""
    sc = success_criteria
    metric = (sc or {}).get("metric", "?")
    text = (
        f"Requisito {name} marcado para verificação live (métrica no modelo: {metric})."
        if sc
        else (
            f"Requisito {name} com _go_to_verification, mas sem SuccessCriteria no modelo. "
            "Crie o item SuccessCriteria sob o requirement no SysON."
        )
    )
    # Sem SC: placeholder válido no schema Vampire (metric min_length=1);
    # o gate rejeita métrica desconhecida / critério incompleto via evaluate.
    if sc is None:
        sc = {
            "type": "threshold",
            "metric": "_missing_sc_",
            "operator": ">=",
            "value": 0.0,
            "unit": "",
            "scope": "all_entities",
            "tolerance": 0.0,
        }
    return {
        "req_id": name,
        "title": name,
        "text": text,
        "rationale": "Importado do SysON (doc=marcador; SC=elementos do modelo)",
        "level": "system",
        "vv_method": "test",
        "priority": "high",
        "conops_ref": "SysON",
        "source": "syson",
        "success_criteria": sc,
        "tags": ["syson", "go_to_verification"],
        "_syson": {
            "project_id": project_id,
            "project_name": project_name,
            "element_id": element_id,
            "documentation_id": documentation_id,
            "doc_body": doc_body,
            "sc_from_model": success_criteria is not None,
        },
    }
