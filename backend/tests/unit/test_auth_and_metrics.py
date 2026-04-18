"""Tests for optional auth and Prometheus metrics."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mirror_match.api import metrics as metrics_mod
from mirror_match.main import app


@pytest.fixture
def client_no_auth():
    metrics_mod.reset_metrics()
    return TestClient(app)


@pytest.fixture
def client_with_auth(monkeypatch):
    monkeypatch.setenv("MIRROR_MATCH_AUTH_TOKEN", "s3cret")
    metrics_mod.reset_metrics()
    return TestClient(app)


def test_no_auth_when_token_unset(client_no_auth):
    r = client_no_auth.post(
        "/api/v1/compare",
        json={
            "source_a": {"type": "raw", "data": {"x": 1}},
            "source_b": {"type": "raw", "data": {"x": 2}},
        },
    )
    assert r.status_code == 200


def test_auth_required_when_token_set(client_with_auth):
    r = client_with_auth.post(
        "/api/v1/compare",
        json={
            "source_a": {"type": "raw", "data": {"x": 1}},
            "source_b": {"type": "raw", "data": {"x": 2}},
        },
    )
    assert r.status_code == 401


def test_auth_accepts_correct_bearer(client_with_auth):
    r = client_with_auth.post(
        "/api/v1/compare",
        headers={"Authorization": "Bearer s3cret"},
        json={
            "source_a": {"type": "raw", "data": {"x": 1}},
            "source_b": {"type": "raw", "data": {"x": 2}},
        },
    )
    assert r.status_code == 200


def test_auth_rejects_wrong_bearer(client_with_auth):
    r = client_with_auth.post(
        "/api/v1/compare",
        headers={"Authorization": "Bearer nope"},
        json={
            "source_a": {"type": "raw", "data": {"x": 1}},
            "source_b": {"type": "raw", "data": {"x": 2}},
        },
    )
    assert r.status_code == 401


def test_healthz_open_even_with_auth(client_with_auth):
    assert client_with_auth.get("/api/v1/healthz").status_code == 200


def test_metrics_endpoint_open_and_counts_requests(client_no_auth):
    client_no_auth.get("/api/v1/healthz")
    r = client_no_auth.get("/metrics")
    assert r.status_code == 200
    assert "mirror_match_http_requests_total" in r.text
    assert 'path="/api/v1/healthz"' in r.text


def test_metrics_buckets_job_uuid(client_no_auth):
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1}},
        "source_b": {"type": "raw", "data": {"x": 2}},
    }
    job_id = client_no_auth.post("/api/v1/compare", json=payload).json()["job_id"]
    client_no_auth.get(f"/api/v1/jobs/{job_id}")
    client_no_auth.get(f"/api/v1/jobs/{job_id}/csv")
    r = client_no_auth.get("/metrics")
    assert "/api/v1/jobs/{id}" in r.text
    assert job_id not in r.text


def test_metrics_tracks_compare_duration(client_no_auth):
    client_no_auth.post(
        "/api/v1/compare",
        json={
            "source_a": {"type": "raw", "data": {"x": 1}},
            "source_b": {"type": "raw", "data": {"x": 2}},
        },
    )
    text = client_no_auth.get("/metrics").text
    assert "mirror_match_compare_seconds_count 1" in text
