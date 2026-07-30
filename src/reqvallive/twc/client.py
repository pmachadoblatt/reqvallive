"""Cliente REST SysML v2 / Teamwork Cloud (leitura cirúrgica)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

# Tipos SysML v2 que tratamos como requisito (metamodel OMG + variantes TWC).
_REQUIREMENT_TYPE_HINTS = (
    "RequirementUsage",
    "RequirementDefinition",
    "Requirement",
)


@dataclass
class TwcSettings:
    base_url: str = "https://161.24.23.18:8443"
    sysml_api_prefix: str = "/sysmlv2-api/api"
    auth_login_path: str = "/authentication/api/login"
    username: str = ""
    password: str = ""
    token: str = ""
    verify_ssl: bool = False
    timeout_seconds: float = 30.0


class TwcError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class TwcClient:
    """Cliente mínimo: auth + projects + commits + roots/elements filtrados."""

    def __init__(self, settings: TwcSettings):
        self.settings = settings
        self._token = (settings.token or "").strip()
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/"),
            verify=settings.verify_ssl,
            timeout=settings.timeout_seconds,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TwcClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self._token:
            # TWC clássico: "Token <…>"; alguns gateways aceitam Bearer.
            if self._token.lower().startswith("token ") or self._token.lower().startswith(
                "bearer "
            ):
                h["Authorization"] = self._token
            else:
                h["Authorization"] = f"Token {self._token}"
        return h

    def _sysml(self, path: str) -> str:
        prefix = self.settings.sysml_api_prefix.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        return f"{prefix}{path}"

    def login(self) -> str:
        """Obtém token via user/password se TWC_TOKEN não estiver definido."""
        if self._token:
            return self._token
        user = self.settings.username.strip()
        password = self.settings.password
        if not user or not password:
            raise TwcError(
                "Defina TWC_TOKEN ou TWC_USERNAME + TWC_PASSWORD no .env"
            )
        path = self.settings.auth_login_path
        payloads = [
            {"userName": user, "password": password},
            {"username": user, "password": password},
            {"loginName": user, "password": password},
        ]
        last_err: TwcError | None = None
        for body in payloads:
            r = self._client.post(path, json=body, headers={"Accept": "application/json"})
            if r.status_code >= 400:
                last_err = TwcError(
                    f"Login falhou HTTP {r.status_code} em {path}",
                    status_code=r.status_code,
                    body=r.text[:400],
                )
                continue
            data = r.json() if r.content else {}
            token = (
                data.get("token")
                or data.get("access_token")
                or data.get("id_token")
                or data.get("authToken")
            )
            if not token and isinstance(data, str):
                token = data
            if not token:
                last_err = TwcError(
                    f"Login OK mas sem token no JSON: {str(data)[:300]}",
                    status_code=r.status_code,
                    body=r.text[:400],
                )
                continue
            self._token = str(token).strip()
            return self._token
        assert last_err is not None
        raise last_err

    def ensure_auth(self) -> None:
        self.login()

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        self.ensure_auth()
        r = self._client.get(self._sysml(path), headers=self._headers(), params=params)
        if r.status_code >= 400:
            raise TwcError(
                f"GET {path} → HTTP {r.status_code}",
                status_code=r.status_code,
                body=r.text[:500],
            )
        if not r.content:
            return None
        return r.json()

    def list_projects(self) -> list[dict[str, Any]]:
        data = self.get_json("/projects")
        if data is None:
            return []
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("projects", "data", "value", "items"):
                val = data.get(key)
                if isinstance(val, list):
                    return [x for x in val if isinstance(x, dict)]
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
        # Preferir o primeiro (APIs costumam devolver newest-first); senão created/committedAt.
        def sort_key(c: dict[str, Any]) -> str:
            return str(
                c.get("created")
                or c.get("committedAt")
                or c.get("timestamp")
                or c.get("@id")
                or ""
            )

        ordered = sorted(commits, key=sort_key, reverse=True)
        top = ordered[0]
        return _id_of(top)

    def get_roots(
        self, project_id: str, commit_id: str, *, page_size: int = 50
    ) -> list[dict[str, Any]]:
        data = self.get_json(
            f"/projects/{project_id}/commits/{commit_id}/roots",
            params={"page[size]": page_size},
        )
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def get_element(
        self, project_id: str, commit_id: str, element_id: str
    ) -> dict[str, Any]:
        data = self.get_json(
            f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        )
        if not isinstance(data, dict):
            raise TwcError(f"Elemento {element_id} sem JSON de objeto")
        return data

    def get_elements_page(
        self,
        project_id: str,
        commit_id: str,
        *,
        page_size: int = 50,
        page_after: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"page[size]": page_size}
        if page_after:
            params["page[after]"] = page_after
        data = self.get_json(
            f"/projects/{project_id}/commits/{commit_id}/elements",
            params=params,
        )
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def find_requirements(
        self,
        project_id: str,
        commit_id: str,
        *,
        name_substring: str | None = None,
        max_pages: int = 20,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Varre páginas de elements e filtra requisitos (não descarrega o modelo todo)."""
        found: list[dict[str, Any]] = []
        page_after: str | None = None
        needle = (name_substring or "").lower()
        for _ in range(max_pages):
            page = self.get_elements_page(
                project_id, commit_id, page_size=page_size, page_after=page_after
            )
            if not page:
                break
            for el in page:
                if not _looks_like_requirement(el):
                    continue
                if needle and needle not in _element_name(el).lower():
                    continue
                found.append(el)
            if len(page) < page_size:
                break
            page_after = _id_of(page[-1])
            if not page_after:
                break
        return found

    def documentation_text(self, element: dict[str, Any]) -> str:
        """Extrai texto de Documentation / doc / body de um elemento SysML v2."""
        for key in (
            "documentation",
            "Documentation",
            "documentationBody",
            "Documentation Body",
            "body",
            "text",
            "declaredShortName",
        ):
            val = element.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, dict):
                for sub in ("value", "body", "text", "@value"):
                    if isinstance(val.get(sub), str) and val[sub].strip():
                        return val[sub].strip()
        # JSON-LD / ownedElement comments
        owned = element.get("ownedElement") or element.get("ownedRelationship") or []
        if isinstance(owned, list):
            for child in owned:
                if not isinstance(child, dict):
                    continue
                t = str(child.get("@type") or child.get("type") or "")
                if "Documentation" in t or "Comment" in t:
                    body = child.get("body") or child.get("documentation")
                    if isinstance(body, str) and body.strip():
                        return body.strip()
        return ""


def _id_of(obj: dict[str, Any]) -> str | None:
    for key in ("@id", "id", "identity", "elementId"):
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, dict):
            inner = val.get("@id") or val.get("id")
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
    return None


def _element_name(el: dict[str, Any]) -> str:
    for key in (
        "name",
        "declaredName",
        "qualifiedName",
        "shortName",
        "declaredShortName",
        "title",
    ):
        val = el.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    ident = el.get("identity")
    if isinstance(ident, dict):
        for key in ("name", "declaredName"):
            val = ident.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return _id_of(el) or ""


def _looks_like_requirement(el: dict[str, Any]) -> bool:
    types = el.get("@type") or el.get("type") or el.get("@types") or []
    if isinstance(types, str):
        types = [types]
    if not isinstance(types, list):
        types = [str(types)]
    joined = " ".join(str(t) for t in types)
    if any(h in joined for h in _REQUIREMENT_TYPE_HINTS):
        return True
    name = _element_name(el)
    return bool(re.match(r"(?i)^RQ[_-]?", name))


def settings_from_env(settings_obj: Any) -> TwcSettings:
    """Constrói TwcSettings a partir de reqvallive.config.settings."""
    return TwcSettings(
        base_url=getattr(settings_obj, "twc_base_url", "https://161.24.23.18:8443"),
        sysml_api_prefix=getattr(settings_obj, "twc_sysml_api_prefix", "/sysmlv2-api/api"),
        auth_login_path=getattr(
            settings_obj, "twc_auth_login_path", "/authentication/api/login"
        ),
        username=getattr(settings_obj, "twc_username", "") or "",
        password=getattr(settings_obj, "twc_password", "") or "",
        token=getattr(settings_obj, "twc_token", "") or "",
        verify_ssl=bool(getattr(settings_obj, "twc_verify_ssl", False)),
        timeout_seconds=float(getattr(settings_obj, "twc_timeout_seconds", 30.0)),
    )


def probe_summary(client: TwcClient, *, req_filter: str = "RQ_") -> dict[str, Any]:
    """Resumo para CLI / GET /api/twc/probe."""
    client.ensure_auth()
    projects = client.list_projects()
    out: dict[str, Any] = {
        "ok": True,
        "base_url": client.settings.base_url,
        "sysml_api_prefix": client.settings.sysml_api_prefix,
        "project_count": len(projects),
        "projects": [],
    }
    for p in projects[:20]:
        pid = _id_of(p)
        name = p.get("name") or p.get("declaredName") or pid
        entry: dict[str, Any] = {"id": pid, "name": name}
        if pid:
            try:
                cid = client.latest_commit_id(pid)
                entry["latest_commit_id"] = cid
                if cid:
                    reqs = client.find_requirements(
                        pid, cid, name_substring=req_filter, max_pages=5, page_size=50
                    )
                    entry["requirements_matched"] = [
                        {
                            "id": _id_of(r),
                            "name": _element_name(r),
                            "types": r.get("@type") or r.get("type"),
                            "documentation_preview": (client.documentation_text(r) or "")[
                                :240
                            ],
                        }
                        for r in reqs[:10]
                    ]
            except TwcError as exc:
                entry["error"] = str(exc)
        out["projects"].append(entry)
    return out
