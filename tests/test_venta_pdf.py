from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


def make_args(tmp_path: Path, **overrides):
    data = {
        "id": "790683285",
        "out": str(tmp_path / "venta.pdf"),
        "cuit_trabajo": "30000000000",
        "cuit_trabajo_id": None,
        "cuit_trabajo_nombre": None,
        "allow_web_session_fallback": False,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_extract_ofinube_lote_id(sos_api):
    payload = {
        "statusCode": 200,
        "resultados": [
            {
                "resultados_impresion": {
                    "lote": {
                        "id": "261723",
                    }
                }
            }
        ],
    }

    lote_id = sos_api.extract_ofinube_lote_id(payload)

    assert lote_id == "261723"


def test_command_venta_pdf_uses_api_first(tmp_path, sos_api, monkeypatch):
    out_path = tmp_path / "venta-api.pdf"

    class DummyClient:
        def request_raw(self, method, path, **kwargs):
            assert method == "GET"
            assert path == "venta/pdf/790683285"
            return (b"%PDF-1.4\n%api\n", {"Content-Type": "application/pdf"})

    class DummyWebClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("web-session no debe consultarse si la API funciono")

    monkeypatch.setattr(sos_api, "SOSContadorWebClient", DummyWebClient)
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )

    result = sos_api.command_venta_pdf(make_args(tmp_path, out=str(out_path)), DummyClient())

    assert result["transport"] == "api"
    assert out_path.read_bytes().startswith(b"%PDF-1.4")


def test_command_venta_pdf_requires_explicit_permission_before_websession(tmp_path, sos_api, monkeypatch):
    out_path = tmp_path / "venta-blocked.pdf"

    class DummyClient:
        def request_raw(self, method, path, **kwargs):
            assert method == "GET"
            assert path == "venta/pdf/790683285"
            return (b"not a pdf", {"Content-Type": "text/plain"})

    class DummyWebClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("web-session requiere permiso explicito")

    monkeypatch.setattr(sos_api, "SOSContadorWebClient", DummyWebClient)
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )

    try:
        sos_api.command_venta_pdf(make_args(tmp_path, out=str(out_path)), DummyClient())
    except sos_api.CLIError as exc:
        assert "requiere permiso explicito" in str(exc)
    else:
        raise AssertionError("Se esperaba CLIError")

    assert not out_path.exists()


def test_command_venta_pdf_can_use_websession_when_explicitly_allowed(tmp_path, sos_api, monkeypatch):
    out_path = tmp_path / "venta-web.pdf"

    class DummyClient:
        def request_raw(self, method, path, **kwargs):
            assert method == "GET"
            assert path == "venta/pdf/790683285"
            return (b"not a pdf", {"Content-Type": "text/plain"})

    class DummyWebClient:
        def __init__(self, *args, **kwargs):
            pass

        def download_venta_pdf(
            self,
            *,
            venta_id,
            out_path,
        ):
            assert venta_id == "790683285"
            Path(out_path).write_bytes(b"%PDF-1.4\n%web\n")
            return {"written_to": out_path, "content_type": "application/pdf"}

    monkeypatch.setattr(sos_api, "SOSContadorWebClient", DummyWebClient)
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )

    result = sos_api.command_venta_pdf(
        make_args(tmp_path, out=str(out_path), allow_web_session_fallback=True),
        DummyClient(),
    )

    assert result["transport"] == "web-session"
    assert "fallback_reason" in result
    assert out_path.read_bytes().startswith(b"%PDF-1.4")


