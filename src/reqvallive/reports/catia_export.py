"""Exportos CATIA pós-medição: CSV Sync (modelo aberto) + .sysml (arquivo)."""

from __future__ import annotations

import csv
import io
import re
from typing import Any

# Import SysML v2 textual NÃO atualiza o modelo aberto — cria namespace separado.
# Ver docs/CATIA_UPDATE_FORMATOS.md
SYSML_IMPORT_DISCLAIMER = (
    "// ReqValLive UPDATE — arquivo/diff.\n"
    "// ATENÇÃO (docs CATIA Magic): File > Import From > SysML v2 Textual Notation\n"
    "// importa para um NAMESPACE RAIZ SEPARADO — NÃO edita o modelo já aberto.\n"
    "// Para atualizar o projeto aberto: use verification_sync.csv + Excel/CSV Sync\n"
    "// (Identification Property = Id). Ver docs/CATIA_UPDATE_FORMATOS.md\n"
)


def doc_text_for_requirement(req_upd: dict[str, Any]) -> str:
    """Preferir texto LLM se existir; senão o bloco determinístico."""
    llm = (req_upd.get("catia_doc_llm") or "").strip()
    if llm:
        return llm
    return (req_upd.get("catia_doc_append") or "").strip()


def build_csv_sync(update: dict[str, Any]) -> str:
    """CSV para Excel/CSV Sync no Magic (atualiza Documentation por Id)."""
    buf = io.StringIO()
    # utf-8-sig: Excel no Windows reconhece Unicode
    writer = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Id", "Name", "Documentation", "VerificationTag"])
    for req in update.get("requirements") or []:
        rid = str(req.get("req_id") or "")
        name = str(req.get("title") or rid)
        doc = doc_text_for_requirement(req)
        tag = str(req.get("verification_tag") or "")
        writer.writerow([rid, name, doc, tag])
    return "\ufeff" + buf.getvalue()


def build_plugin_bridge(update: dict[str, Any]) -> dict[str, Any]:
    """Contrato para futuro plugin Open API (edição in-process do modelo aberto)."""
    actions = []
    for req in update.get("requirements") or []:
        actions.append(
            {
                "op": "set_documentation",
                "element_name": req.get("req_id"),
                "element_id": req.get("req_id"),
                "documentation": doc_text_for_requirement(req),
                "verification_tag": req.get("verification_tag"),
            }
        )
    return {
        "protocol": "reqvallive.catia.plugin.v1",
        "updates_open_model": True,
        "requires": "MagicDraw/Cameo Java Open API plugin (SessionManager)",
        "actions": actions,
        "note_pt": (
            "Só um plugin (ou SysML v2 REST no Teamwork Cloud) atualiza o modelo "
            "aberto automaticamente. O CSV Sync é o caminho nativo sem plugin."
        ),
    }


_REQ_DOC_RE = re.compile(
    r"(requirement\s+(\w+)\s*\{)(.*?)(\n\s*\})",
    re.DOTALL,
)
_DOC_BLOCK_RE = re.compile(
    r"doc\s*/\*(.*?)\*/",
    re.DOTALL,
)


def patch_sysml_docs(source_sysml: str, update: dict[str, Any]) -> str:
    """Substitui doc /* ... */ dos requisitos medidos; mantém resto do export."""
    by_id = {
        str(r.get("req_id")): doc_text_for_requirement(r)
        for r in (update.get("requirements") or [])
        if r.get("req_id")
    }
    if not by_id:
        return SYSML_IMPORT_DISCLAIMER + "\n" + (source_sysml or "")

    def repl_req(m: re.Match[str]) -> str:
        head, rid, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        if rid not in by_id:
            return m.group(0)
        new_doc = by_id[rid]

        def repl_doc(_dm: re.Match[str]) -> str:
            return f"doc /*\n{new_doc}\n        */"

        if _DOC_BLOCK_RE.search(body):
            new_body = _DOC_BLOCK_RE.sub(repl_doc, body, count=1)
        else:
            new_body = f"\n        doc /*\n{new_doc}\n        */\n" + body
        return head + new_body + tail

    patched = _REQ_DOC_RE.sub(repl_req, source_sysml or "")
    return SYSML_IMPORT_DISCLAIMER + "\n" + patched


def attach_export_artifacts(
    update: dict[str, Any],
    *,
    source_sysml: str = "",
) -> dict[str, Any]:
    """Acrescenta metadados e pré-visualizações dos exportos no pacote UPDATE."""
    csv_text = build_csv_sync(update)
    sysml_text = patch_sysml_docs(source_sysml, update)
    update = dict(update)
    update["catia_channels"] = {
        "open_model_update": {
            "recommended": "excel_csv_sync",
            "file": "verification_sync.csv",
            "updates_open_project": True,
            "how_pt": (
                "No projeto ABERTO: tabela de requisitos → Excel/CSV Sync → "
                "Select File (verification_sync.csv) → Identification Property=Id → "
                "mapear Documentation → Read From File."
            ),
            "doc": "docs/CATIA_UPDATE_FORMATOS.md",
        },
        "sysml_textual": {
            "file": "verification_update.sysml",
            "updates_open_project": False,
            "how_pt": (
                "Import From > SysML v2 Textual Notation cria namespace SEPARADO. "
                "Use só como arquivo/diff — não como sync do modelo aberto."
            ),
        },
        "plugin_open_api": {
            "updates_open_project": True,
            "status": "contract_only",
            "protocol": "reqvallive.catia.plugin.v1",
        },
    }
    update["plugin_bridge"] = build_plugin_bridge(update)
    update["exports_preview"] = {
        "csv_sync_lines": len(csv_text.splitlines()),
        "sysml_chars": len(sysml_text),
    }
    update["instructions_pt"] = (
        "ATUALIZAR O MODELO ABERTO (recomendado):\n"
        "1) Baixe verification_sync.csv\n"
        "2) No CATIA Magic, na tabela de requisitos do projeto aberto, "
        "Excel/CSV Sync → ficheiro → Id como Identification Property → "
        "mapear Documentation → Read From File.\n"
        "3) Os requisitos existentes (mesmo Id) têm Documentation atualizada "
        "com _verification_PASS/_FAIL.\n\n"
        "NÃO use o .sysml para sync do aberto: o import cria namespace novo "
        "(docs CATIA Magic). O .sysml serve de arquivo/diff.\n\n"
        "Automação total: plugin Open API (secção plugin_bridge) ou SysML v2 REST no TWC."
    )
    # Pré-visualização curta (não embutir ficheiros inteiros no JSON da UI)
    update["exports_preview"]["csv_head"] = "\n".join(csv_text.splitlines()[:4])
    update["exports_preview"]["sysml_head"] = "\n".join(sysml_text.splitlines()[:8])
    return update
