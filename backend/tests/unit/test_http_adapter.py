"""Tests for the HTTP adapter."""

from __future__ import annotations

import httpx
import pytest
import respx

from mirror_match.adapters.http import HttpAdapter, HttpAuth


@respx.mock
async def test_get_returns_json_body():
    respx.get("https://api.example.com/doc").mock(
        return_value=httpx.Response(200, json={"x": 1})
    )
    adapter = HttpAdapter(url="https://api.example.com/doc")
    loaded = await adapter.load()
    assert loaded.data == {"x": 1}
    assert loaded.identifier == "GET https://api.example.com/doc"


@respx.mock
async def test_bearer_auth_sets_header():
    route = respx.get("https://api.example.com/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    adapter = HttpAdapter(
        url="https://api.example.com/x",
        auth=HttpAuth(kind="bearer", token="t0k"),
    )
    await adapter.load()
    assert route.calls.last.request.headers["authorization"] == "Bearer t0k"


@respx.mock
async def test_api_key_auth_uses_custom_header():
    route = respx.get("https://api.example.com/y").mock(
        return_value=httpx.Response(200, json={})
    )
    adapter = HttpAdapter(
        url="https://api.example.com/y",
        auth=HttpAuth(kind="api_key", token="k", header_name="X-My-Key"),
    )
    await adapter.load()
    assert route.calls.last.request.headers["x-my-key"] == "k"


@respx.mock
async def test_basic_auth():
    route = respx.get("https://api.example.com/z").mock(
        return_value=httpx.Response(200, json={})
    )
    adapter = HttpAdapter(
        url="https://api.example.com/z",
        auth=HttpAuth(kind="basic", username="u", password="p"),
    )
    await adapter.load()
    auth_hdr = route.calls.last.request.headers["authorization"]
    assert auth_hdr.startswith("Basic ")


@respx.mock
async def test_post_with_body():
    route = respx.post("https://api.example.com/search").mock(
        return_value=httpx.Response(200, json={"hits": 1})
    )
    adapter = HttpAdapter(
        url="https://api.example.com/search",
        method="POST",
        body={"q": "hello"},
    )
    loaded = await adapter.load()
    assert loaded.data == {"hits": 1}
    sent = route.calls.last.request
    assert sent.method == "POST"
    assert b'"q":"hello"' in sent.content or b'"q": "hello"' in sent.content


@respx.mock
async def test_json_pointer_extracts_nested():
    respx.get("https://api.example.com/d").mock(
        return_value=httpx.Response(
            200, json={"data": {"docs": [{"id": 1}, {"id": 2}]}}
        )
    )
    adapter = HttpAdapter(
        url="https://api.example.com/d", json_pointer="/data/docs/1"
    )
    loaded = await adapter.load()
    assert loaded.data == {"id": 2}


@respx.mock
async def test_non_2xx_raises():
    respx.get("https://api.example.com/err").mock(
        return_value=httpx.Response(500, text="boom")
    )
    adapter = HttpAdapter(url="https://api.example.com/err")
    with pytest.raises(httpx.HTTPStatusError):
        await adapter.load()
