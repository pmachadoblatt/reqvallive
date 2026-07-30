"""Testes do cliente TWC com HTTP mock (sem rede)."""

from __future__ import annotations

import httpx
import pytest

from reqvallive.twc.client import (
    TwcClient,
    TwcSettings,
    _looks_like_requirement,
)


def test_looks_like_requirement_by_type_and_name():
    assert _looks_like_requirement({"@type": "RequirementUsage", "name": "X"})
    assert _looks_like_requirement({"@type": ["Package"], "declaredName": "RQ_BAT_001"})
    assert not _looks_like_requirement({"@type": "PartUsage", "name": "Battery"})


def test_login_and_list_projects(monkeypatch):
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.url.path.endswith("/authentication/api/login"):
            return httpx.Response(200, json={"token": "abc123"})
        if request.url.path.endswith("/sysmlv2-api/api/projects"):
            assert request.headers.get("Authorization") == "Token abc123"
            return httpx.Response(
                200,
                json=[{"@id": "p1", "name": "Demo"}, {"@id": "p2", "name": "Other"}],
            )
        return httpx.Response(404, text="nope")

    transport = httpx.MockTransport(handler)
    settings = TwcSettings(
        base_url="https://example.test",
        username="pedroblatt",
        password="secret",
        verify_ssl=False,
    )
    client = TwcClient(settings)
    client._client = httpx.Client(
        base_url=settings.base_url, transport=transport, verify=False
    )
    try:
        token = client.login()
        assert token == "abc123"
        projects = client.list_projects()
        assert len(projects) == 2
        assert projects[0]["name"] == "Demo"
    finally:
        client.close()


def test_find_requirements_filters_pages():
    pages = {
        None: [
            {"@id": "e1", "@type": "PartUsage", "name": "Motor"},
            {"@id": "e2", "@type": "RequirementUsage", "name": "RQ_BAT_001", "body": "doc"},
        ],
        "e2": [
            {"@id": "e3", "@type": "RequirementUsage", "name": "RQ_ALT_001"},
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/authentication/api/login"):
            return httpx.Response(200, json={"token": "t"})
        if "/elements" in request.url.path and not request.url.path.rstrip("/").endswith(
            "elements/x"
        ):
            after = request.url.params.get("page[after]")
            return httpx.Response(200, json=pages.get(after, []))
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    settings = TwcSettings(
        base_url="https://example.test", username="u", password="p", verify_ssl=False
    )
    client = TwcClient(settings)
    client._client = httpx.Client(
        base_url=settings.base_url, transport=transport, verify=False
    )
    try:
        found = client.find_requirements("p1", "c1", name_substring="RQ_BAT", max_pages=5)
        assert len(found) == 1
        assert found[0]["name"] == "RQ_BAT_001"
        assert client.documentation_text(found[0]) == "doc"
    finally:
        client.close()
