"""Tests for the Elasticsearch adapter (client mocked)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from jsondiff.adapters.elasticsearch import EsAdapter


def _fake_client_factory(*, get_body=None, search_body=None):
    client = SimpleNamespace()
    client.get = AsyncMock(return_value=SimpleNamespace(body=get_body or {}))
    client.search = AsyncMock(return_value=SimpleNamespace(body=search_body or {}))
    client.close = AsyncMock()
    return lambda: client


async def test_fetch_by_id_returns_source():
    factory = _fake_client_factory(
        get_body={"_source": {"id": 1, "name": "A"}, "_id": "1"}
    )
    adapter = EsAdapter(
        hosts=["http://es:9200"],
        index="users",
        mode="by_id",
        doc_id="1",
        _client_factory=factory,
    )
    loaded = await adapter.load()
    assert loaded.data == {"id": 1, "name": "A"}
    assert loaded.identifier == "es://users/1"


async def test_fetch_by_id_requires_doc_id():
    factory = _fake_client_factory()
    adapter = EsAdapter(
        hosts=["http://es:9200"], index="users", mode="by_id", _client_factory=factory
    )
    try:
        await adapter.load()
    except ValueError as e:
        assert "doc_id" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


async def test_query_returns_first_source_by_default():
    factory = _fake_client_factory(
        search_body={
            "hits": {
                "hits": [
                    {"_source": {"id": 1}},
                    {"_source": {"id": 2}},
                ]
            }
        }
    )
    adapter = EsAdapter(
        hosts=["http://es:9200"],
        index="users",
        mode="query",
        query={"query": {"term": {"active": True}}},
        _client_factory=factory,
    )
    loaded = await adapter.load()
    assert loaded.data == {"id": 1}


async def test_query_returns_all_hits_when_requested():
    factory = _fake_client_factory(
        search_body={"hits": {"hits": [{"_source": {"id": 1}}]}}
    )
    adapter = EsAdapter(
        hosts=["http://es:9200"],
        index="users",
        mode="query",
        query_return="hits",
        _client_factory=factory,
    )
    loaded = await adapter.load()
    assert loaded.data == [{"_source": {"id": 1}}]


async def test_query_empty_hits_returns_none():
    factory = _fake_client_factory(search_body={"hits": {"hits": []}})
    adapter = EsAdapter(
        hosts=["http://es:9200"],
        index="users",
        mode="query",
        _client_factory=factory,
    )
    loaded = await adapter.load()
    assert loaded.data is None


async def test_custom_identifier_is_used():
    factory = _fake_client_factory(get_body={"_source": {}})
    adapter = EsAdapter(
        hosts=["http://es:9200"],
        index="users",
        mode="by_id",
        doc_id="x",
        identifier="prod-users/x",
        _client_factory=factory,
    )
    loaded = await adapter.load()
    assert loaded.identifier == "prod-users/x"
