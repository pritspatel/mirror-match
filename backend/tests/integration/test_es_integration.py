"""Elasticsearch adapter round-trip against a real ES container.

Skipped automatically when Docker is unavailable or the `testcontainers`
extra is not installed. Run explicitly with `pytest tests/integration`.
"""

from __future__ import annotations

import pytest

testcontainers_es = pytest.importorskip("testcontainers.elasticsearch")

from mirror_match.adapters.elasticsearch import EsAdapter, EsAuth  # noqa: E402

ES_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch:8.15.0"


@pytest.fixture(scope="module")
def es_container():
    try:
        with testcontainers_es.ElasticSearchContainer(ES_IMAGE) as es:
            yield es
    except Exception as exc:  # docker unavailable, image pull fails, etc.
        pytest.skip(f"Elasticsearch container unavailable: {exc}")


@pytest.fixture(scope="module")
def es_client(es_container):
    from elasticsearch import Elasticsearch

    url = es_container.get_url()
    client = Elasticsearch(hosts=[url], verify_certs=False)
    yield client
    client.close()


def test_by_id_roundtrip(es_container, es_client):
    es_client.index(index="docs", id="1", document={"name": "Alice", "age": 30}, refresh=True)

    adapter = EsAdapter(
        hosts=[es_container.get_url()],
        index="docs",
        mode="by_id",
        doc_id="1",
        auth=EsAuth(kind="none"),
        verify_certs=False,
    )
    import asyncio

    loaded = asyncio.run(adapter.load())
    assert loaded.data == {"name": "Alice", "age": 30}
    assert loaded.identifier == "es://docs/1"


def test_query_first_source(es_container, es_client):
    es_client.index(index="docs", id="2", document={"name": "Bob", "age": 40}, refresh=True)

    adapter = EsAdapter(
        hosts=[es_container.get_url()],
        index="docs",
        mode="query",
        query={"query": {"term": {"name.keyword": "Bob"}}},
        auth=EsAuth(kind="none"),
        verify_certs=False,
    )
    import asyncio

    loaded = asyncio.run(adapter.load())
    assert loaded.data == {"name": "Bob", "age": 40}
