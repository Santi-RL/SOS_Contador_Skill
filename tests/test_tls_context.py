from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_api_ssl_context_uses_certifi_by_default(sos_api, monkeypatch):
    monkeypatch.delenv("SOS_CONTADOR_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.setattr(sos_api, "certifi", SimpleNamespace(where=lambda: "demo-ca.pem"))
    calls = []
    expected = object()
    monkeypatch.setattr(
        sos_api.ssl,
        "create_default_context",
        lambda *, cafile=None: calls.append(cafile) or expected,
    )

    assert sos_api.build_api_ssl_context() is expected
    assert calls == ["demo-ca.pem"]


def test_api_ssl_context_prefers_explicit_bundle(sos_api, monkeypatch, tmp_path):
    bundle = tmp_path / "corporate-ca.pem"
    bundle.write_text("demo", encoding="utf-8")
    monkeypatch.setenv("SOS_CONTADOR_CA_BUNDLE", str(bundle))
    monkeypatch.setenv("SSL_CERT_FILE", "ignored.pem")
    calls = []
    expected = object()
    monkeypatch.setattr(
        sos_api.ssl,
        "create_default_context",
        lambda *, cafile=None: calls.append(cafile) or expected,
    )

    assert sos_api.build_api_ssl_context() is expected
    assert calls == [str(bundle)]


def test_api_ssl_context_rejects_missing_explicit_bundle(sos_api, monkeypatch, tmp_path):
    missing = tmp_path / "missing.pem"
    monkeypatch.setenv("SOS_CONTADOR_CA_BUNDLE", str(missing))

    with pytest.raises(sos_api.CLIError, match="bundle CA configurado no existe"):
        sos_api.build_api_ssl_context()


def test_api_requests_receive_the_verified_ssl_context(sos_api, monkeypatch):
    monkeypatch.delenv("SOS_CONTADOR_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    client = sos_api.SOSContadorClient(base_url="https://api.example.invalid")
    expected_context = object()
    client.ssl_context = expected_context

    class FakeResponse:
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(request, *, timeout, context):
        assert timeout == 60
        assert context is expected_context
        return FakeResponse()

    monkeypatch.setattr(sos_api.urllib.request, "urlopen", fake_urlopen)

    raw, headers = client._send_request_raw(method="GET", path="health")

    assert raw == b"{}"
    assert headers == {}
