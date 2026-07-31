from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def make_args(**overrides):
    data = {
        "cuit_trabajo": None,
        "cuit_trabajo_id": None,
        "cuit_trabajo_nombre": None,
        "cliente": True,
        "proveedor": True,
        "pagina": 1,
        "registros": 50,
        "body_json": None,
        "body_file": None,
        "dry_run": False,
        "confirm": False,
        "auth_mode": "jwtc",
        "out": None,
        "query": None,
        "method": "GET",
        "path": "",
        "source": [],
        "cliente_cuit": None,
        "cliente_nombre": None,
        "fecha": None,
        "comentarios": None,
        "centrocosto": None,
        "factura": None,
        "venta_id": None,
        "json_out": None,
        "preview_format": "json",
        "draft_id": None,
        "draft_file": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_command_auth_info_works_without_default_work_cuit(monkeypatch, sos_api):
    for env_name in sos_api.DEPRECATED_WORK_CUIT_ENV_KEYS:
        monkeypatch.delenv(env_name, raising=False)

    dummy_client = SimpleNamespace(
        base_url="https://api.example.test",
        get_login_session=lambda: SimpleNamespace(
            jwt="jwt-login",
            login_payload={
                "cuits": [
                    {"id": "1001", "cuit": "30000000000", "razon_social": "Empresa Demo"},
                    {"id": "1002", "cuit": "30000000001", "razon_social": "Cliente Demo"},
                ]
            },
        ),
    )

    result = sos_api.command_auth_info(SimpleNamespace(show_tokens=False), dummy_client)

    assert result["jwt_obtenido"] is True
    assert result["jwtc_obtenido"] is False
    assert result["cuit"] is None
    assert result["available_cuits_count"] == 2


def test_command_auth_web_info_requires_explicit_work_cuit(monkeypatch, sos_api):
    for env_name in sos_api.DEPRECATED_WORK_CUIT_ENV_KEYS:
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(sos_api.CLIError, match="Debe indicar el CUIT de trabajo"):
        sos_api.command_auth_web_info(make_args(), SimpleNamespace())


def test_business_command_requires_explicit_work_cuit(monkeypatch, sos_api):
    for env_name in sos_api.DEPRECATED_WORK_CUIT_ENV_KEYS:
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(sos_api.CLIError, match="Debe indicar el CUIT de trabajo"):
        sos_api.command_cliente_list(make_args(), SimpleNamespace())


def test_resolve_work_cuit_target_accepts_name(monkeypatch, sos_api):
    monkeypatch.setattr(
        sos_api,
        "resolve_cuit_name",
        lambda client, name, refresh=False: {
            "id": "1001",
            "cuit": "30000000000",
            "razon_social": "Empresa Demo S.R.L.",
            "matched_by": "alias",
        },
    )

    result = sos_api.resolve_work_cuit_target(
        sos_api.SOSContadorClient(),
        explicit_name="Empresa Demo",
    )

    assert result["cuit_id"] == "1001"
    assert result["cuit"] == "30000000000"
    assert result["nombre"] == "Empresa Demo S.R.L."


def test_build_cobro_draft_infers_work_cuit_from_buyer_section(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "factura-compra.txt"
    txt_path.write_text(
        "\n".join(
            [
                "Factura de compra",
                "Datos del comprador",
                "EMPRESA DEMO S.R.L.",
                "CUIT 30-00000000-0",
                "Datos del vendedor",
                "Proveedor Demo S.A.",
                "CUIT 30-00000000-1",
                "Fecha: 15/03/2026",
                "Factura A-0001-00001234 1.250.000,00",
            ]
        ),
        encoding="utf-8",
    )

    class DummyClient:
        base_url = "https://example.test"
        explicit_cuit = "30000000000"

        def get_session(self):
            return SimpleNamespace(cuit="30000000000")

    dummy_client = DummyClient()
    monkeypatch.setattr(
        sos_api,
        "ensure_cuit_catalog",
        lambda client, refresh=False: [
            {"id": "1001", "cuit": "30000000000", "razon_social": "Empresa Demo S.R.L."},
        ],
    )
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1001", "nombre": "Empresa Demo S.R.L."})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "2001",
                "clipro": "Proveedor Demo S.A.",
                "cuit": "30-00000000-1",
                "cuit_digits": "30000000001",
                "normalized_name": "proveedor demo s a",
            }
        ],
    )
    monkeypatch.setattr(sos_api, "parse_structured_movements", lambda rows: [])
    monkeypatch.setattr(sos_api, "parse_line_movements", lambda lines, client: [])
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5002", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000")),
    )

    draft = sos_api.build_cobro_draft(make_args(source=[str(txt_path)]), sos_api.SOSContadorClient())

    assert draft["contexto"]["cuit_trabajo"]["cuit"] == "30000000000"
    assert draft["contexto"]["cuit_trabajo"]["estado"] == "inferido"


def test_command_venta_create_dry_run_returns_business_preview(capsys, sos_api, monkeypatch):
    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000"))
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (dummy_client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )
    monkeypatch.setattr(
        sos_api,
        "build_venta_create_body",
        lambda args, client: {
            "idclipro": "2002",
            "fecha": "17/03/2026",
            "letra": "C",
            "sucursal": "2",
            "numero": "5",
            "productos": [
                {"id": "4001", "fc": "1.000", "fu": "2800.000", "fa": "0.00", "cuid": "3001"}
            ],
        },
    )
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [{"idclipro": "2002", "clipro": "Consumidor Final", "cuit": "20000000000", "cuit_digits": "20000000000"}],
    )
    monkeypatch.setattr(
        sos_api,
        "get_account_catalog",
        lambda client: [{"id": "3001", "label": "Ventas Generales"}],
    )

    with pytest.raises(SystemExit):
        sos_api.command_venta_create(make_args(dry_run=True), sos_api.SOSContadorClient())

    output = capsys.readouterr().out
    assert "business_preview" in output
    assert "preview_markdown" in output
    assert "venta_create" in output


def test_command_pago_create_dry_run_returns_business_preview(capsys, sos_api, monkeypatch):
    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000"))
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (dummy_client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )
    monkeypatch.setattr(
        sos_api,
        "build_cobro_or_pago_body",
        lambda args, client: {
            "fecha": "15/03/2026",
            "idclipro": "2002",
            "imputaciones": [{"fv": "1500.00", "cuid": "1"}],
        },
    )
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [{"idclipro": "2002", "clipro": "Proveedor SA", "cuit": "30000000001", "cuit_digits": "30000000001"}],
    )

    with pytest.raises(SystemExit):
        sos_api.command_pago_create(make_args(dry_run=True), sos_api.SOSContadorClient())

    output = capsys.readouterr().out
    assert "pago_create" in output
    assert "preview_markdown" in output


def test_command_cliente_create_dry_run_returns_business_preview(capsys, sos_api, monkeypatch):
    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000"))
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (dummy_client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )

    with pytest.raises(SystemExit):
        sos_api.command_cliente_create(
            make_args(dry_run=True, body_json='{"clipro":"Nuevo Cliente","cuit":"30700000008"}'),
            sos_api.SOSContadorClient(),
        )

    output = capsys.readouterr().out
    assert "cliente_create" in output
    assert "Nuevo Cliente" in output


def test_ensure_mutation_allowed_blocks_comprobante_cancellation_fields(sos_api):
    with pytest.raises(sos_api.CLIError, match="anulacion/cancelacion"):
        sos_api.ensure_mutation_allowed(
            "POST",
            "back/comprobante_altamodi.asp",
            None,
            {"cancelado": "1", "fecha": "20/03/2026"},
            make_args(confirm=True),
        )


def test_build_afip_mis_comprobantes_draft_ignores_annulled_existing_purchase(tmp_path, sos_api, monkeypatch):
    workbook_path = tmp_path / "mis-comprobantes.xlsx"
    workbook_path.write_text("dummy", encoding="utf-8")

    row = {
        "source_row": 3,
        "fecha": "2026-02-25",
        "puntoventa": 154,
        "numero": 9083,
        "numerohasta": 9083,
        "counterparty_cuit": "30000000008",
        "counterparty_name": "Proveedor Demo B S.A.",
        "cae": "",
        "validation_errors": [],
        "amounts_raw": {
            "neto_21": "124793.38",
            "neto_10_5": "0.00",
            "neto_27": "0.00",
            "neto_0": "0.00",
            "nogravado": "0.00",
            "exento": "0.00",
            "otros": "7487.61",
            "imp_total": "158487.60",
        },
        "type_rule": {
            "fcncnd": "F",
            "letra": "A",
            "tipocomprobante": 1,
            "sign": sos_api.Decimal("1"),
        },
    }
    dummy_bound_client = SimpleNamespace(
        get_session=lambda: SimpleNamespace(cuit="30000000000", cuit_id="1001"),
        request=lambda method, path, **kwargs: {"cabecera": {}, "imputaciones": []},
    )

    monkeypatch.setattr(
        sos_api,
        "read_afip_mis_comprobantes_workbook",
        lambda path: {
            "operation_kind": "compra",
            "work_cuit": "30000000000",
            "row1": "Mis Comprobantes Recibidos - CUIT 30000000000",
            "rows": [row],
        },
    )
    monkeypatch.setattr(
        sos_api,
        "resolve_afip_work_target",
        lambda client, args, workbook_work_cuit: (
            dummy_bound_client,
            {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo S.R.L."},
        ),
    )
    monkeypatch.setattr(
        sos_api,
        "fetch_all_clientes_catalog",
        lambda client: {"30000000008": {"id": "2003", "clipro": "Proveedor Demo B S.A."}},
    )
    monkeypatch.setattr(sos_api, "fetch_compra_consulta_items", lambda client, desde, hasta: [{"id": "800865875"}])
    monkeypatch.setattr(
        sos_api,
        "fetch_web_comprobante_status_index",
        lambda client, idtipo_operacion, desde_iso, hasta_iso: {
            "800865875": {
                "id": "800865875",
                "comprobante": "A-0154-00009083",
                "clipro": "Proveedor Demo B S.A.",
                "cancelado": "1",
                "fechabaja": "2026-03-20T13:25:33.000",
                "annulled": True,
            }
        },
    )
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")

    draft = sos_api.build_afip_mis_comprobantes_draft(make_args(source=str(workbook_path)), sos_api.SOSContadorClient())

    assert draft["rows"][0]["status"] == "pendiente"
    assert draft["rows"][0]["existing_match_id"] == ""
    assert draft["stats"]["ya_cargado"] == 0


def test_command_afip_import_raises_if_post_create_verification_finds_annulled_purchase(sos_api, monkeypatch):
    draft = {
        "draft_id": "abc123",
        "draft_file": "draft.json",
        "source": "file.xlsx",
        "stats": {"pendiente": 1, "ya_cargado": 0, "verificar": 0},
        "contexto": {
            "fecha_desde": "2026-02-01",
            "fecha_hasta": "2026-02-28",
            "cuit_trabajo": {"cuit": "30000000000", "cuit_id": "1001"},
        },
        "rows": [
            {
                "status": "pendiente",
                "source_row": 3,
                "documento": "A-0154-00009083",
                "counterparty_name": "Proveedor Demo B S.A.",
                "row_payload": {
                    "fecha": "2026-02-25",
                    "counterparty_cuit": "30000000008",
                    "counterparty_name": "Proveedor Demo B S.A.",
                    "puntoventa": 154,
                    "numero": 9083,
                    "numerohasta": 9083,
                    "cae": "",
                    "amounts_raw": {
                        "neto_21": "124793.38",
                        "neto_10_5": "0.00",
                        "neto_27": "0.00",
                        "neto_0": "0.00",
                        "nogravado": "0.00",
                        "exento": "0.00",
                        "otros": "7487.61",
                        "imp_total": "158487.60",
                    },
                    "type_rule": {
                        "fcncnd": "F",
                        "letra": "A",
                        "tipocomprobante": 1,
                        "sign": sos_api.Decimal("1"),
                    },
                },
            }
        ],
    }
    dummy_bound_client = SimpleNamespace(
        get_session=lambda: SimpleNamespace(cuit="30000000000", cuit_id="1001"),
        request=lambda method, path, **kwargs: {"id": "900"} if (method, path) == ("PUT", "compra/0") else {},
    )

    monkeypatch.setattr(sos_api, "build_afip_mis_comprobantes_draft", lambda args, client: draft)
    monkeypatch.setattr(sos_api, "build_afip_draft_preview", lambda draft: {"titulo": "afip_draft"})
    monkeypatch.setattr(sos_api, "render_afip_draft_markdown", lambda draft: "preview")
    monkeypatch.setattr(sos_api, "set_mutation_preview", lambda *args, **kwargs: None)
    monkeypatch.setattr(sos_api, "ensure_mutation_allowed", lambda *args, **kwargs: None)
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_bound_client)
    monkeypatch.setattr(
        sos_api,
        "fetch_all_clientes_catalog",
        lambda client: {"30000000008": {"id": "2003", "clipro": "Proveedor Demo B S.A."}},
    )
    monkeypatch.setattr(
        sos_api,
        "fetch_web_comprobante_status_index",
        lambda client, idtipo_operacion, desde_iso, hasta_iso: {
            "900": {
                "id": "900",
                "comprobante": "A-0154-00009083",
                "clipro": "Proveedor Demo B S.A.",
                "cancelado": "1",
                "fechabaja": "2026-03-20T13:25:33.000",
                "annulled": True,
            }
        },
    )

    with pytest.raises(sos_api.CLIError, match="compras anuladas inmediatamente"):
        sos_api.command_afip_import(make_args(confirm=True), sos_api.SOSContadorClient())


def test_command_call_dry_run_returns_business_preview(capsys, sos_api, monkeypatch):
    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000"))
    monkeypatch.setattr(
        sos_api,
        "bind_business_client",
        lambda client, args, required=True: (dummy_client, {"cuit": "30000000000", "cuit_id": "1001", "nombre": "Empresa Demo"}),
    )

    with pytest.raises(SystemExit):
        sos_api.command_call(
            make_args(
                dry_run=True,
                method="POST",
                path="cliente",
                body_json='{"clipro":"Cliente desde call"}',
                query=["pagina=1"],
                auth_mode="jwtc",
            ),
            sos_api.SOSContadorClient(),
        )

    output = capsys.readouterr().out
    assert "call" in output
    assert "Cliente desde call" in output



