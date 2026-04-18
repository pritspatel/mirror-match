"""Tests for request redaction before job persistence."""

from __future__ import annotations

from mirror_match.api.redact import REDACTED, redact_request


def test_redacts_http_bearer_token():
    req = {
        "source_a": {
            "type": "http",
            "url": "https://api.example.com/x",
            "auth": {"kind": "bearer", "token": "sekret-abc"},
            "headers": {},
        },
        "source_b": {"type": "raw", "data": {}},
    }
    out = redact_request(req)
    assert out["source_a"]["auth"]["token"] == REDACTED


def test_redacts_http_basic_username_and_password():
    req = {
        "source_a": {
            "type": "http",
            "url": "https://x",
            "auth": {"kind": "basic", "username": "svc", "password": "pw"},
            "headers": {},
        },
        "source_b": {"type": "raw", "data": {}},
    }
    out = redact_request(req)
    assert out["source_a"]["auth"]["username"] == REDACTED
    assert out["source_a"]["auth"]["password"] == REDACTED


def test_redacts_api_key_header_case_insensitive():
    req = {
        "source_a": {
            "type": "http",
            "url": "https://x",
            "auth": {"kind": "none"},
            "headers": {"Authorization": "Bearer abc", "X-Trace": "ok"},
        },
        "source_b": {
            "type": "http",
            "url": "https://x",
            "auth": {"kind": "none"},
            "headers": {"cookie": "session=xyz"},
        },
    }
    out = redact_request(req)
    assert out["source_a"]["headers"]["Authorization"] == REDACTED
    assert out["source_a"]["headers"]["X-Trace"] == "ok"  # non-sensitive kept
    assert out["source_b"]["headers"]["cookie"] == REDACTED


def test_redacts_elasticsearch_api_key():
    req = {
        "source_a": {
            "type": "elasticsearch",
            "hosts": ["https://es:9200"],
            "index": "prod",
            "auth": {"kind": "api_key", "api_key": "encoded=="},
        },
        "source_b": {"type": "raw", "data": {}},
    }
    out = redact_request(req)
    assert out["source_a"]["auth"]["api_key"] == REDACTED


def test_redaction_does_not_mutate_input():
    req = {
        "source_a": {
            "type": "http",
            "url": "https://x",
            "auth": {"kind": "bearer", "token": "sekret"},
            "headers": {},
        },
        "source_b": {"type": "raw", "data": {}},
    }
    redact_request(req)
    assert req["source_a"]["auth"]["token"] == "sekret"


def test_raw_source_untouched():
    req = {
        "source_a": {"type": "raw", "data": {"x": 1}},
        "source_b": {"type": "raw", "data": {"y": 2}},
    }
    out = redact_request(req)
    assert out == req


def test_empty_auth_values_not_replaced_with_redacted():
    # Redacting a None / empty field would be misleading — only overwrite
    # actual secret values.
    req = {
        "source_a": {
            "type": "http",
            "url": "https://x",
            "auth": {"kind": "none", "token": None, "username": ""},
            "headers": {},
        },
        "source_b": {"type": "raw", "data": {}},
    }
    out = redact_request(req)
    assert out["source_a"]["auth"]["token"] is None
    assert out["source_a"]["auth"]["username"] == ""
