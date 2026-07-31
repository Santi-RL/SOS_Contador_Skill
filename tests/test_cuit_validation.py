from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "value",
    [
        "30-00000000-7",
        "30000000007",
        "30-00000001-5",
    ],
)
def test_is_valid_argentina_cuit_accepts_valid_values(sos_api, value):
    assert sos_api.is_valid_argentina_cuit(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "30-00000000-8",
        "30000000008",
        "00000000000",
        "10000000006",
        "123",
        "",
    ],
)
def test_is_valid_argentina_cuit_rejects_invalid_values(sos_api, value):
    assert sos_api.is_valid_argentina_cuit(value) is False


def test_cliente_get_rejects_invalid_cuit_before_authentication(sos_api, monkeypatch):
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda *args, **kwargs: pytest.fail("No debe autenticarse con un CUIT inválido."),
    )
    args = SimpleNamespace(
        id=None,
        cuit="30-00000000-8",
        nombre=None,
    )

    with pytest.raises(sos_api.CLIError, match="dígito verificador correcto"):
        sos_api.command_cliente_get(args, SimpleNamespace())


def test_cliente_create_rejects_invalid_cuit_before_authentication(sos_api, monkeypatch):
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda *args, **kwargs: pytest.fail("No debe autenticarse con un CUIT inválido."),
    )
    args = SimpleNamespace(
        body_json='{"cuit":"30-00000000-8","clipro":"Empresa Demo S.R.L."}',
        body_file=None,
    )

    with pytest.raises(sos_api.CLIError, match="CUIT del cliente/proveedor inválido"):
        sos_api.command_cliente_create(args, SimpleNamespace())
