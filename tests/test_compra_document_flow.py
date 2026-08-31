from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def make_args(**overrides):
    defaults = {
        "source": None,
        "document_json": None,
        "document_file": None,
        "cuit_trabajo": None,
        "cuit_trabajo_id": None,
        "cuit_trabajo_nombre": None,
        "json_out": None,
        "preview_format": "both",
        "draft_id": None,
        "draft_file": None,
        "dry_run": False,
        "confirm": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def mixed_rate_text() -> str:
    return "\n".join(
        [
            "PROVEEDOR: ACME Demo S.A.",
            "C.U.I.T. 30-00000001-5",
            "Inicio de Actividades: 01/01/2010",
            'TIQUE FACTURA "A" N° 00002-00000077',
            "Fecha 03/02/2026",
            "Datos del comprador Empresa Demo S.R.L.",
            "C.U.I.T. 30-00000000-0",
            "Subtotal 330,00",
            "DTO. DESCUENTO GENERAL (21,00) -10,00",
            "DTO. DESCUENTO GENERAL (10,50) -20,00",
            "SUBTOT. IMP. NETO GRAVADO 300,00",
            "ALICUOTA 21,00% 21,00",
            "ALICUOTA 10,50% 21,00",
            "IIBB PROVINCIAL 15,00",
            "IMPORTE TOTAL OTROS TRIBUTOS 15,00",
            "TOTAL 357,00",
        ]
    )


def matching_detail(*, compra_id: int = 900) -> dict:
    return {
        "cabecera": {
            "id": compra_id,
            "fecha": "2026-02-03T03:00:00.000Z",
            "clipro": "ACME Demo S.A.",
            "cuit": "30000000015",
            "fcncnd": "F",
            "letra": "A",
            "puntoventa": 2,
            "numero": 77,
            "idcuenta": 8100,
            "cuenta": "Gastos de comercialización",
            "idcentrocosto": 8200,
            "centrocosto": "General",
            "idprovinciaiibb": 19,
        },
        "imputaciones": [
            {
                "identificador": "neto",
                "alicuota": 21,
                "montodebe": 100,
                "iva_debe": 21,
            },
            {
                "identificador": "neto",
                "alicuota": 10.5,
                "montodebe": 200,
                "iva_debe": 21,
            },
            {
                "identificador": "percepcioniibb",
                "alicuota": 0,
                "montodebe": 15,
                "iva_debe": 0,
            },
        ],
        "productos": [],
    }


def test_compra_parser_prioritizes_invoice_date_and_reconciles_mixed_rates(sos_api):
    source = {
        "lines": sos_api.clean_text_lines(mixed_rate_text()),
        "warnings": [],
        "capabilities": [],
    }

    fields, issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={},
    )

    assert issues == []
    assert fields["fecha"] == "2026-02-03"
    assert fields["proveedor_cuit"] == "30000000015"
    assert fields["letra"] == "A"
    assert fields["puntoventa"] == 2
    assert fields["numero"] == 77
    assert fields["amounts"]["neto_21"] == sos_api.Decimal("100.00")
    assert fields["amounts"]["neto_10_5"] == sos_api.Decimal("200.00")
    assert fields["amounts"]["iva_21"] == sos_api.Decimal("21.00")
    assert fields["amounts"]["iva_10_5"] == sos_api.Decimal("21.00")
    assert fields["amounts"]["percepcion_iibb"] == sos_api.Decimal("15.00")
    assert fields["amounts"]["total"] == sos_api.Decimal("357.00")
    assert "otros" not in fields["amounts"]


def test_compra_parser_blocks_unallocated_global_discount_across_rates(sos_api):
    amounts, issues = sos_api.normalize_compra_amounts(
        {
            "neto_21": "100.00",
            "iva_21": "21.00",
            "neto_10_5": "200.00",
            "iva_10_5": "21.00",
            "descuento_global": "-30.00",
            "total": "342.00",
        }
    )

    assert amounts["descuento_global"] == sos_api.Decimal("-30.00")
    assert any("no puede asignarse" in issue for issue in issues)


def test_compra_parser_marks_invalid_supplier_cuit_for_review(sos_api):
    source = {
        "lines": sos_api.clean_text_lines(mixed_rate_text().replace("30-00000001-5", "30-00000000-8")),
        "warnings": [],
        "capabilities": [],
    }

    fields, issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={},
    )

    assert fields["proveedor_cuit"] == ""
    assert any("dígito verificador correcto" in issue for issue in issues)


def test_compra_parser_requires_explicit_classification_for_generic_other_taxes(sos_api):
    source = {
        "lines": sos_api.clean_text_lines(
            "\n".join(
                [
                    "PROVEEDOR: Combustibles Demo S.A.",
                    "C.U.I.T. 30-00000001-5",
                    'TIQUE FACTURA "A" N° 00012-00000077',
                    "Fecha 26/08/2026",
                    "Comprador Empresa Demo S.R.L.",
                    "C.U.I.T. 30-00000000-0",
                    "SUBTOT. IMP. NETO GRAVADO 100,00",
                    "ALICUOTA 21,00% 21,00",
                    "IMPUESTO INTERNO 10,00",
                    "IMPORTE TOTAL OTROS TRIBUTOS 10,00",
                    "TOTAL 131,00",
                ]
            )
        ),
        "warnings": [],
        "capabilities": [],
    }

    fields, issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={},
    )

    assert fields["amounts"]["otros"] == sos_api.Decimal("10.00")
    assert any("otros tributos sin clasificación" in issue for issue in issues)

    corrected, corrected_issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={"nogravado": "10.00"},
    )

    assert corrected_issues == []
    assert corrected["amounts"]["nogravado"] == sos_api.Decimal("10.00")
    assert "otros" not in corrected["amounts"]


def test_compra_parser_blocks_unreviewed_structured_extraction_conflict(sos_api):
    source = {
        "lines": sos_api.clean_text_lines(mixed_rate_text()),
        "warnings": [],
        "capabilities": [],
    }

    fields, issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={"numero": 78},
    )

    assert fields["numero"] == 78
    assert fields["extraction_conflicts"] == [
        {
            "field": "numero",
            "label": "número",
            "automatic_value": "77",
            "structured_value": "78",
            "reviewed": False,
        }
    ]
    assert any("_reviewed_conflicts" in issue for issue in issues)


def test_compra_parser_accepts_only_explicitly_reviewed_conflict(sos_api):
    source = {
        "lines": sos_api.clean_text_lines(mixed_rate_text()),
        "warnings": [],
        "capabilities": [],
    }

    fields, issues = sos_api.build_compra_source_fields(
        source,
        work_cuit="30000000000",
        overrides={"numero": 78, "_reviewed_conflicts": ["numero"]},
    )

    assert issues == []
    assert fields["numero"] == 78
    assert fields["extraction_conflicts"][0]["reviewed"] is True


def test_compra_draft_blocks_body_when_extractions_disagree(tmp_path, sos_api, monkeypatch):
    source_path = tmp_path / "factura-demo.txt"
    source_path.write_text(mixed_rate_text(), encoding="utf-8")
    bound_client = SimpleNamespace()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda *args, **kwargs: bound_client)
    monkeypatch.setattr(
        sos_api,
        "resolve_cliente_match",
        lambda *args, **kwargs: {
            "id": 7001,
            "clipro": "ACME Demo S.A.",
            "cuit": "30000000015",
            "idprovincia": 19,
        },
    )
    monkeypatch.setattr(
        sos_api,
        "fetch_recent_supplier_purchase_details",
        lambda *args, **kwargs: [matching_detail(compra_id=800)],
    )
    monkeypatch.setattr(sos_api, "find_compra_duplicate", lambda *args, **kwargs: None)

    draft = sos_api.build_compra_document_draft(
        make_args(
            source=[str(source_path)],
            document_json=[json.dumps({"numero": 78})],
            cuit_trabajo="30000000000",
        ),
        sos_api.SOSContadorClient(),
    )

    row = draft["rows"][0]
    assert row["status"] == "verificar"
    assert row["body"] is None
    assert "extracción automática" in row["reason"]


def test_compra_override_rejects_unknown_reviewed_conflict(sos_api):
    args = make_args(
        source=["factura-demo.txt"],
        document_json=[json.dumps({"_reviewed_conflicts": ["todos"]})],
    )

    try:
        sos_api.load_compra_document_overrides(args, 1)
    except sos_api.CLIError as exc:
        assert "campos no comparables" in str(exc)
    else:
        raise AssertionError("Se esperaba CLIError para un campo de conflicto desconocido")


def test_compra_preview_exposes_all_tax_components(sos_api):
    draft = {
        "contexto": {"cuit_trabajo": {"cuit": "30000000000", "nombre": "Empresa Demo S.R.L."}},
        "rows": [
            {
                "status": "pendiente",
                "documento": "FA-0012-00000077",
                "fields": {"fecha": "2026-08-26", "proveedor_nombre": "Combustibles Demo S.A."},
                "expected_amounts": {
                    "neto_21": "100.00",
                    "iva_21": "21.00",
                    "nogravado": "10.00",
                    "otros": "0.00",
                    "total": "131.00",
                },
                "reason": "",
            }
        ],
        "stats": {"pendiente": 1, "ya_cargado": 0, "verificar": 0},
        "validacion": {"warnings": []},
    }

    row = sos_api.build_compra_draft_preview(draft)["tablas"][0]["rows"][0]

    assert row["IVA 21 %"] == "21.00"
    assert row["No gravado"] == "10.00"
    assert row["Otros tributos"] == "0.00"


def test_compra_credit_note_comparison_keeps_document_amounts_positive(sos_api):
    summary = {
        "neto_21": "-100.00",
        "iva_21": "-21.00",
        "total": "-121.00",
    }
    expected = {
        "neto_21": "100.00",
        "iva_21": "21.00",
        "total": "121.00",
    }

    assert sos_api.compra_summary_matches_expected(summary, expected, fcncnd="C")
    assert not sos_api.compra_summary_matches_expected(summary, expected, fcncnd="F")


@pytest.mark.parametrize(
    "overrides,account_id,center_id,account_label,center_label",
    [
        ({}, 8100, 8200, "Gastos de comercialización", "General"),
        ({"idcuenta": "8100", "idcentrocosto": 8200}, 8100, 8200, "Gastos de comercialización", "General"),
        ({"idcuenta": 8300}, 8300, 8200, "8300", "General"),
        ({"idcentrocosto": "8400"}, 8100, 8400, "Gastos de comercialización", "8400"),
    ],
)
def test_compra_draft_reuses_consistent_history_and_freezes_body(
    tmp_path, sos_api, monkeypatch, overrides, account_id, center_id, account_label, center_label
):
    source_path = tmp_path / "factura-demo.txt"
    source_path.write_text(mixed_rate_text(), encoding="utf-8")
    bound_client = SimpleNamespace()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda *args, **kwargs: bound_client)
    monkeypatch.setattr(
        sos_api,
        "resolve_cliente_match",
        lambda *args, **kwargs: {
            "id": 7001,
            "clipro": "ACME Demo S.A.",
            "cuit": "30000000015",
            "idprovincia": 19,
        },
    )
    monkeypatch.setattr(
        sos_api,
        "fetch_recent_supplier_purchase_details",
        lambda *args, **kwargs: [matching_detail(compra_id=800)],
    )
    monkeypatch.setattr(sos_api, "find_compra_duplicate", lambda *args, **kwargs: None)

    draft = sos_api.build_compra_document_draft(
        make_args(
            source=[str(source_path)],
            cuit_trabajo="30000000000",
            document_json=[json.dumps(overrides)],
        ),
        sos_api.SOSContadorClient(),
    )

    row = draft["rows"][0]
    body = row["body"]
    assert row["status"] == "pendiente"
    assert row["body_sha256"] == sos_api.compra_payload_hash(body)
    assert body["fecha"] == "2026-02-03"
    assert body["fechaiva"] == "2026-02-03"
    assert body["idclipro"] == 7001
    assert body["idcentrocosto"] == center_id
    assert body["idprovinciaiibb"] == 19
    assert body["imputaciones"][0]["cuid"] == account_id
    preview = sos_api.build_compra_draft_preview(draft)["tablas"][0]["rows"][0]
    assert preview["Cuenta"] == account_label
    assert preview["Centro de costo"] == center_label
    assert body["referencia"] == "factura-demo.txt"
    assert len(body["uniqueid"]) == 36
    assert body["imputaciones"][0]["imputa"] == [
        {"i": "neto", "a": 21.0, "v": 100.0},
        {"i": "neto", "a": 10.5, "v": 200.0},
        {"i": "percepcioniibb", "a": 0.0, "v": 15.0},
    ]


@pytest.mark.parametrize("zero", [0, 0.0, "0.00"])
def test_compra_structured_zero_is_an_amount_not_a_missing_value(sos_api, zero):
    source = {"lines": sos_api.clean_text_lines(mixed_rate_text())}
    fields, issues = sos_api.build_compra_source_fields(
        source, work_cuit="30000000000", overrides={"otros": zero}
    )

    assert issues == []
    assert fields["amounts"]["otros"] == sos_api.Decimal("0.00")
    assert fields["amounts"]["total"] == sos_api.Decimal("357.00")


@pytest.mark.parametrize("missing", [None, "", " "])
def test_missing_amount_is_not_silently_replaced_with_zero(sos_api, missing):
    with pytest.raises(sos_api.CLIError, match="Monto vacio"):
        sos_api.smart_decimal_from_text(missing)


def test_compra_duplicate_distinguishes_exact_and_conflicting_amounts(sos_api, monkeypatch):
    fields = {
        "fecha": "2026-02-03",
        "proveedor_cuit": "30000000015",
        "fcncnd": "F",
        "letra": "A",
        "puntoventa": 2,
        "numero": 77,
        "amounts": {
            "neto_21": "100.00",
            "neto_10_5": "200.00",
            "iva_21": "21.00",
            "iva_10_5": "21.00",
            "percepcion_iibb": "15.00",
            "total": "357.00",
        },
    }
    row = {
        "id": 900,
        "factura": "FA-0002-00000077",
        "clipro": {"cuit": "30000000015"},
        "eliminado": "0",
        "archivado": 0,
        "cancelado": "0",
    }
    monkeypatch.setattr(sos_api, "fetch_compra_items_complete", lambda *args, **kwargs: ([row], False))
    client = SimpleNamespace(request=lambda *args, **kwargs: matching_detail())

    exact = sos_api.find_compra_duplicate(client, fields=fields)
    assert exact["kind"] == "exact"

    conflicting = deepcopy(fields)
    conflicting["amounts"]["total"] = "358.00"
    mismatch = sos_api.find_compra_duplicate(client, fields=conflicting)
    assert mismatch["kind"] == "identity_conflict"

    annulled_row = {**row, "cancelado": "1"}
    monkeypatch.setattr(sos_api, "fetch_compra_items_complete", lambda *args, **kwargs: ([annulled_row], False))
    inactive = sos_api.find_compra_duplicate(client, fields=fields)
    assert inactive["kind"] == "identity_conflict"
    assert inactive["active"] is False


def test_compra_create_reuses_frozen_body_and_verifies_result(tmp_path, sos_api, monkeypatch):
    body = {
        "fecha": "2026-02-03",
        "fechaiva": "2026-02-03",
        "idclipro": 7001,
        "cuitclipro": "30000000015",
        "fcncnd": "F",
        "letra": "A",
        "puntoventa": 2,
        "numero": 77,
        "numerohasta": 77,
        "obtienecae": False,
        "idprovinciaiibb": 19,
        "idcentrocosto": 8200,
        "memo": "",
        "referencia": "factura-demo.txt",
        "descuento": 0,
        "uniqueid": "11111111-2222-4333-8444-555555555555",
        "controlainconsistencia": 0,
        "imputaciones": [
            {
                "imputa": [
                    {"i": "neto", "a": 21.0, "v": 100.0},
                    {"i": "neto", "a": 10.5, "v": 200.0},
                    {"i": "percepcioniibb", "a": 0.0, "v": 15.0},
                ],
                "cuid": 8100,
            }
        ],
        "productos": [],
    }
    draft = {
        "draft_id": "compra123",
        "draft_kind": sos_api.COMPRA_DOCUMENT_DRAFT_KIND,
        "contexto": {
            "cuit_trabajo": {
                "cuit": "30000000000",
                "cuit_id": "1001",
                "nombre": "Empresa Demo S.R.L.",
            }
        },
        "rows": [
            {
                "status": "pendiente",
                "documento": "FA-0002-00000077",
                "fields": {
                    "fecha": "2026-02-03",
                    "proveedor_cuit": "30000000015",
                    "proveedor_nombre": "ACME Demo S.A.",
                    "fcncnd": "F",
                    "letra": "A",
                    "puntoventa": 2,
                    "numero": 77,
                    "idcuenta": "8100",
                    "idcentrocosto": "8200",
                    "idprovinciaiibb": "19",
                },
                "expected_amounts": {
                    "neto_21": "100.00",
                    "neto_10_5": "200.00",
                    "iva_21": "21.00",
                    "iva_10_5": "21.00",
                    "percepcion_iibb": "15.00",
                    "total": "357.00",
                },
                "body": body,
                "body_sha256": sos_api.compra_payload_hash(body),
            }
        ],
        "stats": {"pendiente": 1, "ya_cargado": 0, "verificar": 0},
        "validacion": {"warnings": []},
    }
    sos_api.save_draft_payload(draft)
    captured = []

    class FakeClient:
        def request(self, method, path, **kwargs):
            if (method, path) == ("PUT", "compra/0"):
                captured.append(deepcopy(kwargs["body"]))
                return {"id": 900}
            if (method, path) == ("GET", "compra/detalle/900"):
                return matching_detail()
            raise AssertionError((method, path, kwargs))

    bound_client = FakeClient()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda *args, **kwargs: bound_client)
    monkeypatch.setattr(
        sos_api,
        "resolve_cliente_match",
        lambda *args, **kwargs: {"id": 7001, "clipro": "ACME Demo S.A.", "cuit": "30000000015"},
    )
    monkeypatch.setattr(sos_api, "find_compra_duplicate", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sos_api,
        "fetch_compra_items_complete",
        lambda *args, **kwargs: (
            [
                {
                    "id": 900,
                    "factura": "FA-0002-00000077",
                    "clipro": {"cuit": "30000000015"},
                    "eliminado": False,
                    "archivado": False,
                }
            ],
            False,
        ),
    )
    monkeypatch.setattr(
        sos_api,
        "fetch_web_comprobante_status_index",
        lambda *args, **kwargs: {"900": {"annulled": False}},
    )

    result = sos_api.command_compra_create(
        make_args(draft_id="compra123", confirm=True),
        sos_api.SOSContadorClient(),
    )

    assert captured == [body]
    assert result["created_compras"][0]["id"] == 900
    assert result["created_compras"][0]["public_active"] is True
    assert result["created_compras"][0]["internal_active"] is True
    assert result["warnings"] == []
