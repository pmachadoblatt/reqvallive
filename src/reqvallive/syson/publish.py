"""Publicar VerificationResult no SysON (item ligado ao requirement)."""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from reqvallive.syson.client import SysonClient, SysonError, _element_name, _id_of
from reqvallive.syson.verification_result import (
    VR_ITEM_NAME,
    attach_verification_results_to_update,
    is_verification_result_name,
    verification_result_textual,
)


class SysonPublisher:
    def __init__(self, client: SysonClient):
        self.client = client

    def editing_context_id(self, project_id: str) -> str:
        q = """
        query($projectId: ID!) {
          viewer {
            project(projectId: $projectId) {
              currentEditingContext { id }
            }
          }
        }
        """
        data = self.client.graphql(q, {"projectId": project_id})
        try:
            return data["viewer"]["project"]["currentEditingContext"]["id"]
        except (KeyError, TypeError) as exc:
            raise SysonError(f"Sem editingContext para projeto {project_id}") from exc

    def resolve_requirement_element_id(
        self, project_id: str, req_name: str
    ) -> str | None:
        """Re-resolve @id actual (pode mudar entre sessões SysON)."""
        cid = self.client.latest_commit_id(project_id)
        if not cid:
            return None
        for el in self.client.find_requirements(project_id, cid, name_substring=req_name):
            if _element_name(el) == req_name:
                return _id_of(el)
        return None

    def find_verification_results(
        self, project_id: str, requirement_id: str
    ) -> list[dict[str, Any]]:
        cid = self.client.latest_commit_id(project_id)
        if not cid:
            return []
        found: list[dict[str, Any]] = []
        for el in self.client.list_elements(project_id, cid):
            if el.get("@type") != "ItemUsage":
                continue
            if not is_verification_result_name(_element_name(el)):
                continue
            owner = el.get("owner") or el.get("owningUsage") or el.get("owningNamespace")
            if _id_of(owner if isinstance(owner, dict) else None) == requirement_id:
                found.append(el)
        return found

    def find_verification_result_id(
        self,
        project_id: str,
        requirement_id: str,
        *,
        session_id: str | None = None,
    ) -> str | None:
        items = self.find_verification_results(project_id, requirement_id)
        if not items:
            return None
        if not session_id:
            return _id_of(items[-1])
        cid = self.client.latest_commit_id(project_id)
        assert cid
        els = self.client.list_elements(project_id, cid)
        by_id = {_id_of(e): e for e in els if _id_of(e)}
        from reqvallive.syson.model_sc import _attr_value_from_element

        for item in reversed(items):
            iid = _id_of(item)
            for el in els:
                if _element_name(el) != "sessionId":
                    continue
                owner = el.get("owner") or el.get("owningUsage")
                if _id_of(owner if isinstance(owner, dict) else None) != iid:
                    continue
                if str(_attr_value_from_element(el, by_id) or "") == str(session_id):
                    return iid
        return _id_of(items[-1])

    def read_vr_attributes(
        self, project_id: str, vr_id: str
    ) -> dict[str, Any]:
        cid = self.client.latest_commit_id(project_id)
        assert cid
        els = self.client.list_elements(project_id, cid)
        by_id = {_id_of(e): e for e in els if _id_of(e)}
        from reqvallive.syson.model_sc import _attr_value_from_element

        attrs: dict[str, Any] = {}
        for el in els:
            if "Attribute" not in str(el.get("@type") or ""):
                continue
            owner = el.get("owner") or el.get("owningUsage")
            if _id_of(owner if isinstance(owner, dict) else None) != vr_id:
                continue
            name = _element_name(el)
            if not name:
                continue
            val = _attr_value_from_element(el, by_id)
            if val is not None:
                # Se houver atributos duplicados (re-publish), o último ganha.
                attrs[name] = val
        return attrs

    def verify_result_on_rest(
        self,
        project_id: str,
        requirement_id: str,
        *,
        expect_status: str,
        session_id: str = "",
    ) -> dict[str, Any]:
        vr_id = self.find_verification_result_id(
            project_id, requirement_id, session_id=session_id or None
        )
        if not vr_id:
            return {"ok": False, "error": f"{VR_ITEM_NAME} não encontrado via REST"}
        attrs = self.read_vr_attributes(project_id, vr_id)
        status = attrs.get("status")
        return {
            "ok": str(status).upper() == str(expect_status).upper(),
            "verification_result_id": vr_id,
            "attributes": attrs,
            "expected_status": expect_status,
            "observed_status": status,
            "duplicates": len(self.find_verification_results(project_id, requirement_id)),
        }

    def insert_textual(
        self, *, project_id: str, object_id: str, textual: str
    ) -> dict[str, Any]:
        ec = self.editing_context_id(project_id)
        # Confirmar que o objecto é visível no editing context
        probe = self.client.graphql(
            """
            query($e: ID!, $o: ID!) {
              viewer {
                editingContext(editingContextId: $e) {
                  object(objectId: $o) { id label kind }
                }
              }
            }
            """,
            {"e": ec, "o": object_id},
        )
        obj = (
            ((probe or {}).get("viewer") or {})
            .get("editingContext", {})
            .get("object")
        )
        if not obj:
            raise SysonError(
                f"Objecto {object_id} não está no editing context — "
                "abra o projeto ReqTest no SysON e tente de novo."
            )
        mut = """
        mutation($input: InsertTextualSysMLv2Input!) {
          insertTextualSysMLv2(input: $input) {
            __typename
            ... on SuccessPayload { id }
            ... on ErrorPayload { message }
          }
        }
        """
        data = self.client.graphql(
            mut,
            {
                "input": {
                    "id": str(uuid.uuid4()),
                    "editingContextId": ec,
                    "objectId": object_id,
                    "textualContent": textual,
                }
            },
        )
        result = (data or {}).get("insertTextualSysMLv2") or {}
        return {
            "ok": result.get("__typename") == "SuccessPayload",
            "typename": result.get("__typename"),
            "message": result.get("message"),
            "graphql_id": result.get("id"),
            "object_id": object_id,
            "object_label": obj.get("label"),
        }

    def publish_session_update(
        self,
        *,
        project_id: str,
        req_links: list[dict[str, Any]],
        update: dict[str, Any],
        findings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        update = attach_verification_results_to_update(update, findings=findings)
        results: list[dict[str, Any]] = []
        for link in req_links:
            rid = str(link.get("req_id") or "")
            req_upd = next(
                (r for r in (update.get("requirements") or []) if r.get("req_id") == rid),
                None,
            )
            if not req_upd:
                continue
            fields = req_upd.get("syson_verification_result") or {}
            textual = req_upd.get("syson_verification_textual") or verification_result_textual(
                fields
            )
            element_id = self.resolve_requirement_element_id(project_id, rid) or link.get(
                "element_id"
            )
            if not element_id:
                results.append(
                    {
                        "req_id": rid,
                        "ok": False,
                        "error": "requirement não encontrado no SysON",
                    }
                )
                continue
            try:
                inserted = self.insert_textual(
                    project_id=project_id, object_id=element_id, textual=textual
                )
                session_key = str(fields.get("sessionId") or "")
                verified = self.verify_result_on_rest(
                    project_id,
                    element_id,
                    expect_status=str(fields.get("status") or ""),
                    session_id=session_key,
                )
                results.append(
                    {
                        "req_id": rid,
                        "ok": bool(inserted.get("ok") and verified.get("ok")),
                        "requirement_element_id": element_id,
                        "insert": inserted,
                        "verified": verified,
                        "fields": fields,
                        "textual": textual,
                    }
                )
            except (SysonError, httpx.HTTPError) as exc:
                results.append(
                    {
                        "req_id": rid,
                        "ok": False,
                        "error": str(exc),
                        "fields": fields,
                        "textual": textual,
                    }
                )
        all_ok = all(r.get("ok") for r in results) if results else False
        return {
            "project_id": project_id,
            "ok": all_ok,
            "block": VR_ITEM_NAME,
            "results": results,
            "note": (
                f"Cada requisito recebe um item «{VR_ITEM_NAME}_STATUS_…» "
                "(nome já mostra PASS/FAIL + extremo). "
                "Seleccione o item → Documentation tem o resumo; "
                "expanda para ver atributos status/reason/failedAt/extremeValue. "
                "Documentation do requisito permanece só com _go_to_verification. "
                "Refresque o explorador SysON. "
                "Itens antigos só com o nome genérico podem ser apagados à mão."
            ),
            "update": update,
        }
