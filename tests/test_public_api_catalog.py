from __future__ import annotations

from argparse import Namespace
import json

import pytest


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"ok": True}


def invoke_args(operation: str, **overrides):
    values = {
        "operation": operation,
        "param": [],
        "query": [],
        "body_json": None,
        "body_file": None,
        "out": None,
        "dry_run": False,
        "confirm": False,
        "cuit_trabajo": "30000000000",
        "cuit_trabajo_id": None,
        "cuit_trabajo_nombre": None,
    }
    values.update(overrides)
    return Namespace(**values)


def test_catalog_covers_current_postman_collection(sos_api):
    catalog = sos_api.load_public_api_catalog()
    operations = catalog["operations"]

    assert len(operations) == 71
    assert len({item["id"] for item in operations}) == 71
    assert {item["auth"] for item in operations} == {"none", "jwt", "jwtc"}
    assert sos_api.public_api_operation("indiceaniomes.list")["path"] == "indiceaniomes/listado"
    assert sos_api.public_api_operation("venta.save")["method"] == "PUT"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("path", "https://example.invalid/collect", "Path no relativo o inseguro"),
        ("side_effect", "false", "side_effect debe ser booleano"),
        ("body", "sometimes", "Modo de body invalido"),
        ("query", ["pagina", "pagina"], "queries duplicadas"),
    ],
)
def test_catalog_rejects_unsafe_or_ambiguous_contracts(sos_api, monkeypatch, tmp_path, field, value, message):
    operation = {
        "id": "demo.list",
        "module": "demo",
        "method": "GET",
        "path": "demo/listado",
        "auth": "jwtc",
        "query": [],
        "body": "none",
        "side_effect": False,
        "status": "documented",
        "summary": "Contrato de prueba",
    }
    operation[field] = value
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({"operations": [operation]}), encoding="utf-8")
    monkeypatch.setattr(sos_api, "PUBLIC_API_CATALOG_PATH", catalog_path)

    with pytest.raises(sos_api.CLIError, match=message):
        sos_api.load_public_api_catalog()


def test_render_operation_path_handles_optional_values_and_escapes(sos_api):
    assert sos_api.render_operation_path("actividad/listado/:busca?", {}) == "actividad/listado"
    assert sos_api.render_operation_path("tipo/listado/:modulo/:busca?", {"modulo": "venta"}) == "tipo/listado/venta"
    assert sos_api.render_operation_path("venta/detalle/:id", {"id": "a/b"}) == "venta/detalle/a%2Fb"

    with pytest.raises(sos_api.CLIError, match="Falta --param id"):
        sos_api.render_operation_path("venta/detalle/:id", {})

    with pytest.raises(sos_api.CLIError, match="no admitidos"):
        sos_api.render_operation_path("venta/detalle/:id", {"id": "1", "otro": "2"})


def test_jwt_request_uses_login_session_without_selecting_work_cuit(sos_api, monkeypatch):
    client = sos_api.SOSContadorClient()
    monkeypatch.setattr(
        client,
        "get_login_session",
        lambda: sos_api.LoginSession(jwt="jwt-demo", login_payload={}),
    )
    monkeypatch.setattr(client, "get_session", lambda: pytest.fail("No debe resolver una CUIT para auth_mode=jwt"))
    monkeypatch.setattr(
        client,
        "_send_request",
        lambda **kwargs: ({"items": []}, {}),
    )

    assert client.request("GET", "cuit/listado", auth_mode="jwt") == {"items": []}


def test_api_invoke_executes_documented_read_without_mutation_confirmation(sos_api, monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda raw_client, args, required=True: (raw_client, {"cuit": "30000000000", "nombre": "Empresa Demo S.R.L."}),
    )

    result = sos_api.command_api_invoke(invoke_args("indiceaniomes.list"), client)

    assert result == {"ok": True}
    assert client.calls == [
        (
            "GET",
            "indiceaniomes/listado",
            {"query": [], "body": None, "auth_mode": "jwtc", "out_path": None},
        )
    ]


def test_post_search_is_semantically_read_only(sos_api, monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda raw_client, args, required=True: (raw_client, {"cuit": "30000000000", "nombre": "Empresa Demo S.R.L."}),
    )
    monkeypatch.setattr(
        sos_api,
        "ensure_mutation_allowed",
        lambda *args, **kwargs: pytest.fail("Una consulta documentada no debe exigir confirmación"),
    )
    args = invoke_args(
        "venta.search",
        query=["pagina=1", "registros=50"],
        body_json='{"fecha_desde":"2026-01-01","fecha_hasta":"2026-01-31"}',
    )

    sos_api.command_api_invoke(args, client)

    assert client.calls[0][0:2] == ("POST", "venta/consulta")


def test_documented_sale_write_requires_preview_confirmation(sos_api, monkeypatch, capsys):
    client = FakeClient()
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda raw_client, args, required=True: (raw_client, {"cuit": "30000000000", "nombre": "Empresa Demo S.R.L."}),
    )
    fake_session = sos_api.Session(
        jwt="jwt-demo",
        jwtc="jwtc-demo",
        cuit_id="1001",
        cuit="30000000000",
        login_payload={},
        credentials_payload={},
    )
    client.get_session = lambda: fake_session
    args = invoke_args(
        "venta.save",
        body_json='{"fecha":"2026-07-30","idclipro":"1","obtienecae":false}',
        dry_run=True,
    )

    with pytest.raises(SystemExit) as exc:
        sos_api.command_api_invoke(args, client)

    assert exc.value.code == 0
    assert client.calls == []
    assert "venta.save" in capsys.readouterr().out


def test_comprobante_delete_remains_blocked(sos_api, monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda raw_client, args, required=True: (raw_client, {"cuit": "30000000000", "nombre": "Empresa Demo S.R.L."}),
    )
    fake_session = sos_api.Session(
        jwt="jwt-demo",
        jwtc="jwtc-demo",
        cuit_id="1001",
        cuit="30000000000",
        login_payload={},
        credentials_payload={},
    )
    client.get_session = lambda: fake_session

    with pytest.raises(sos_api.CLIError, match="anulaciones o bajas"):
        sos_api.command_api_invoke(
            invoke_args("venta.delete", param=["id=123"], confirm=True),
            client,
        )


def test_sensitive_values_are_redacted_from_previews(sos_api):
    preview = sos_api.redacted_preview(
        "POST",
        "register",
        None,
        {"usuario": "usuario@example.com", "password": "secreto", "nested": {"access_token": "abc"}},
        "none",
    )

    assert preview["body"]["password"] == "<redacted>"
    assert preview["body"]["nested"]["access_token"] == "<redacted>"
    assert preview["body"]["usuario"] == "usuario@example.com"


def test_internal_token_operations_are_not_directly_invokable(sos_api):
    with pytest.raises(sos_api.CLIError, match="auth info"):
        sos_api.command_api_invoke(
            invoke_args("auth.login", body_json='{"usuario":"usuario@example.com","password":"x"}'),
            FakeClient(),
        )
