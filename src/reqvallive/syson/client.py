"""Cliente REST SysON (localhost) — leitura de projetos e requisitos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

_REQUIREMENT_TYPE_HINTS = (
    "RequirementUsage",
    "RequirementDefinition",
    "Requirement",
)


@dataclass
class SysonSettings:
    base_url: str = "http://127.0.0.1:8081"
    api_prefix: str = "/api/rest"
    timeout_seconds: float = 30.0


class SysonError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def settings_from_env(app_settings: Any) -> SysonSettings:
    return SysonSettings(
        base_url=str(getattr(app_settings, "syson_base_url", "http://127.0.0.1:8081")),
        api_prefix=str(getattr(app_settings, "syson_api_prefix", "/api/rest")),
        timeout_seconds=float(getattr(app_settings, "syson_timeout_seconds", 30.0)),
    )


def _id_of(obj: dict[str, Any] | None) -> str | None:
    if not isinstance(obj, dict):
        return None
    for key in ("@id", "id", "elementId"):
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, dict):
            nested = _id_of(val)
            if nested:
                return nested
    return None


def _element_name(el: dict[str, Any]) -> str:
    for key in ("declaredName", "name", "qualifiedName", "reqId", "shortName"):
        val = el.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _looks_like_requirement(el: dict[str, Any]) -> bool:
    t = str(el.get("@type") or el.get("type") or "")
    return any(hint.lower() in t.lower() for hint in _REQUIREMENT_TYPE_HINTS)


class SysonClient:
    """Cliente minimo: health + projects + commits + elements (sem auth no perfil local)."""

    def __init__(self, settings: SysonSettings):
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/"),
            timeout=settings.timeout_seconds,
            follow_redirects=True,
            headers={"Accept": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SysonClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _path(self, path: str) -> str:
        prefix = self.settings.api_prefix.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        return f"{prefix}{path}"

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        r = self._client.get(self._path(path), params=params)
        if r.status_code >= 400:
            raise SysonError(
                f"GET {path} -> HTTP {r.status_code}",
                status_code=r.status_code,
                body=r.text[:500],
            )
        ctype = (r.headers.get("content-type") or "").lower()
        if "json" not in ctype:
            raise SysonError(
                f"GET {path} nao devolveu JSON (content-type={ctype})",
                status_code=r.status_code,
                body=r.text[:200],
            )
        if not r.content:
            return None
        return r.json()

    def health(self) -> dict[str, Any]:
        """UI + lista de projetos (prova de vida do contentor)."""
        ui_ok = False
        ui_status: int | None = None
        try:
            r = self._client.get("/", headers={"Accept": "text/html"})
            ui_status = r.status_code
            ui_ok = 200 <= r.status_code < 500
        except httpx.HTTPError as exc:
            return {
                "ok": False,
                "ui_reachable": False,
                "error": str(exc),
                "base_url": self.settings.base_url,
            }
        try:
            projects = self.list_projects()
            api_ok = True
            api_error = ""
        except SysonError as exc:
            projects = []
            api_ok = False
            api_error = str(exc)
        return {
            "ok": ui_ok and api_ok,
            "base_url": self.settings.base_url,
            "api_prefix": self.settings.api_prefix,
            "ui_reachable": ui_ok,
            "ui_status": ui_status,
            "api_ok": api_ok,
            "api_error": api_error,
            "project_count": len(projects),
            "projects": [
                {"id": _id_of(p), "name": p.get("name") or p.get("declaredName")}
                for p in projects
            ],
        }

    def list_projects(self) -> list[dict[str, Any]]:
        data = self.get_json("/projects")
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def list_commits(self, project_id: str) -> list[dict[str, Any]]:
        data = self.get_json(f"/projects/{project_id}/commits")
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def latest_commit_id(self, project_id: str) -> str | None:
        commits = self.list_commits(project_id)
        if not commits:
            return None
        # SysON local (v2025.6): muitas vezes project/branch/commit partilham o mesmo @id.
        return _id_of(commits[0])

    def list_elements(self, project_id: str, commit_id: str) -> list[dict[str, Any]]:
        data = self.get_json(f"/projects/{project_id}/commits/{commit_id}/elements")
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def find_requirements(
        self,
        project_id: str,
        commit_id: str,
        *,
        name_substring: str | None = None,
    ) -> list[dict[str, Any]]:
        needle = (name_substring or "").lower()
        found: list[dict[str, Any]] = []
        for el in self.list_elements(project_id, commit_id):
            if not _looks_like_requirement(el):
                continue
            if needle and needle not in _element_name(el).lower():
                continue
            found.append(el)
        return found

    def documentation_hint(self, element: dict[str, Any]) -> str:
        """Indica se ha documentation/text no JSON REST (pode estar vazio ate editar na UI)."""
        doc = element.get("documentation")
        text = element.get("text")
        parts: list[str] = []
        if isinstance(doc, list) and doc:
            parts.append(f"documentation[{len(doc)}]")
        elif isinstance(doc, dict) and doc.get("@id"):
            parts.append("documentation[1]")
        elif isinstance(doc, str) and doc.strip() and doc.strip() != "[]":
            parts.append("documentation:str")
        if isinstance(text, list) and text:
            parts.append(f"text[{len(text)}]")
        elif isinstance(text, str) and text.strip() and text.strip() != "[]":
            parts.append("text:str")
        return ", ".join(parts) if parts else "(vazio — cola markers na UI)"

    def get_element(
        self, project_id: str, commit_id: str, element_id: str
    ) -> dict[str, Any]:
        data = self.get_json(
            f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        )
        if not isinstance(data, dict):
            raise SysonError(f"Elemento {element_id} sem objeto JSON")
        return data

    def resolve_documentation(
        self,
        project_id: str,
        commit_id: str,
        requirement: dict[str, Any],
        *,
        elements_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[str, str | None]:
        """Devolve (body, documentation_element_id)."""
        doc_ref = requirement.get("documentation")
        doc_ids: list[str] = []
        if isinstance(doc_ref, dict):
            did = _id_of(doc_ref)
            if did:
                doc_ids.append(did)
        elif isinstance(doc_ref, list):
            for item in doc_ref:
                did = _id_of(item) if isinstance(item, dict) else None
                if did:
                    doc_ids.append(did)

        for did in doc_ids:
            el = (elements_by_id or {}).get(did)
            if el is None:
                try:
                    el = self.get_element(project_id, commit_id, did)
                except SysonError:
                    continue
            body = el.get("body")
            if isinstance(body, str) and body.strip():
                return body.strip(), did

        text = requirement.get("text")
        if isinstance(text, str) and text.strip() and text.strip() != "[]":
            cleaned = text.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                cleaned = cleaned[1:-1].strip()
            return cleaned, doc_ids[0] if doc_ids else None
        if isinstance(text, list):
            parts = [str(x) for x in text if x]
            if parts:
                return "\n".join(parts), doc_ids[0] if doc_ids else None
        return "", doc_ids[0] if doc_ids else None

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> Any:
        r = self._client.post(
            "/api/graphql",
            json={"query": query, "variables": variables or {}},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if r.status_code >= 400:
            raise SysonError(
                f"GraphQL HTTP {r.status_code}",
                status_code=r.status_code,
                body=r.text[:500],
            )
        data = r.json()
        if data.get("errors"):
            msg = data["errors"][0].get("message") if data["errors"] else "GraphQL error"
            raise SysonError(str(msg), body=str(data["errors"])[:500])
        return data.get("data")

    def import_tagged_requirements(
        self,
        project_id: str,
        *,
        project_name: str = "",
        req_filter: str = "",
    ) -> dict[str, Any]:
        """Importa requisitos com `_go_to_verification` no Documentation."""
        from reqvallive.sysml.import_catia import GO_TO_VERIFICATION
        from reqvallive.syson.model_sc import (
            requirement_dict_from_syson,
            success_criteria_from_syson_elements,
        )

        cid = self.latest_commit_id(project_id)
        if not cid:
            raise SysonError(f"Projeto {project_id} sem commits")
        elements = self.list_elements(project_id, cid)
        by_id = {_id_of(e): e for e in elements if _id_of(e)}
        reqs = [
            e
            for e in elements
            if _looks_like_requirement(e)
            and (
                not req_filter
                or req_filter.lower() in _element_name(e).lower()
            )
        ]
        imported: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for req in reqs:
            name = _element_name(req)
            eid = _id_of(req)
            if not name or not eid:
                continue
            body, doc_id = self.resolve_documentation(
                project_id, cid, req, elements_by_id=by_id
            )
            if GO_TO_VERIFICATION not in body:
                skipped.append({"name": name, "reason": "sem _go_to_verification"})
                continue
            sc = success_criteria_from_syson_elements(req, by_id)
            imported.append(
                requirement_dict_from_syson(
                    name=name,
                    element_id=eid,
                    documentation_id=doc_id,
                    doc_body=body,
                    project_id=project_id,
                    project_name=project_name,
                    success_criteria=sc,
                )
            )
        return {
            "project_id": project_id,
            "project_name": project_name,
            "commit_id": cid,
            "imported": imported,
            "skipped": skipped,
            "tag": GO_TO_VERIFICATION,
            "missing_sc": [
                x["req_id"]
                for x in imported
                if not (x.get("_syson") or {}).get("sc_from_model")
            ],
        }


def probe_summary(client: SysonClient, *, req_filter: str = "RQ_") -> dict[str, Any]:
    health = client.health()
    out: dict[str, Any] = {
        "health": health,
        "requirements": [],
    }
    if not health.get("api_ok"):
        return out
    for proj in client.list_projects():
        pid = _id_of(proj)
        if not pid:
            continue
        cid = client.latest_commit_id(pid)
        if not cid:
            continue
        reqs = client.find_requirements(pid, cid, name_substring=req_filter or None)
        for r in reqs:
            out["requirements"].append(
                {
                    "project": proj.get("name"),
                    "project_id": pid,
                    "commit_id": cid,
                    "element_id": _id_of(r),
                    "name": _element_name(r),
                    "type": r.get("@type"),
                    "qualifiedName": r.get("qualifiedName"),
                    "doc_status": client.documentation_hint(r),
                }
            )
    return out
