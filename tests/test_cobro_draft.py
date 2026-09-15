from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import fitz
from openpyxl import Workbook
from PIL import Image
import pytest
import xlwt


def make_args(**overrides):
    data = {
        "source": [],
        "cuit_trabajo": None,
        "cuit_trabajo_id": None,
        "cuit_trabajo_nombre": None,
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
        "confirm": False,
        "dry_run": False,
        "auth_mode": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def create_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_extract_pdf_text_source(tmp_path, sos_api):
    pdf_path = tmp_path / "recibo.pdf"
    create_pdf(pdf_path, "Fecha 15/03/2026\nCheque Galicia 26031621 1800,00")
    result = sos_api.extract_source_document(pdf_path)
    assert result["kind"] == "pdf"
    assert any("15/03/2026" in line for line in result["lines"])


def test_extract_xlsx_and_xls_sources(tmp_path, sos_api):
    xlsx_path = tmp_path / "recibo.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["tipo", "cuenta", "banco", "fecha", "numero", "monto"])
    sheet.append(["cheque", "Valores A Depositar", "GALICIA Y BS AS", "2026-03-15", "26031621", "1800.00"])
    workbook.save(xlsx_path)

    xls_path = tmp_path / "recibo.xls"
    xls_book = xlwt.Workbook()
    xls_sheet = xls_book.add_sheet("Hoja1")
    headers = ["tipo", "cuenta", "fecha", "numero", "regimen", "monto"]
    values = ["retencion", "Retencion Ganancias Sufrida", "2026-03-15", "26031623", "830", "500.00"]
    for index, value in enumerate(headers):
        xls_sheet.write(0, index, value)
    for index, value in enumerate(values):
        xls_sheet.write(1, index, value)
    xls_book.save(str(xls_path))

    xlsx_result = sos_api.extract_source_document(xlsx_path)
    xls_result = sos_api.extract_source_document(xls_path)

    assert xlsx_result["kind"] == "xlsx"
    assert xls_result["kind"] == "xls"
    assert any("GALICIA Y BS AS" in line for line in xlsx_result["lines"])
    assert any("830" in line for line in xls_result["lines"])


def test_extract_image_without_ocr_reports_capability(tmp_path, sos_api, monkeypatch):
    image_path = tmp_path / "recibo.png"
    Image.new("RGB", (200, 60), color="white").save(image_path)
    monkeypatch.setattr(sos_api, "ocr_is_available", lambda: False)
    result = sos_api.extract_source_document(image_path)
    assert result["kind"] == "image"
    assert result["capabilities"]


def test_ocr_language_prefers_spanish_over_english(sos_api):
    assert sos_api.select_ocr_language(["eng", "spa", "osd"]) == "spa"


def test_ocr_language_uses_english_only_when_spanish_is_unavailable(sos_api):
    assert sos_api.select_ocr_language(["eng", "osd"]) == "eng"


def test_get_ocr_language_queries_installed_languages(sos_api, monkeypatch):
    monkeypatch.setattr(sos_api, "ocr_is_available", lambda: True)
    monkeypatch.setattr(sos_api.pytesseract, "get_languages", lambda config: ["eng", "spa"])

    assert sos_api.get_ocr_language() == "spa"


def test_ocr_language_rejects_installation_without_supported_language(sos_api):
    try:
        sos_api.select_ocr_language(["osd"])
    except sos_api.CLIError as exc:
        assert "Instale 'spa'" in str(exc)
        assert "'eng' se admite únicamente como fallback" in str(exc)
    else:
        raise AssertionError("Se esperaba CLIError sin datos OCR compatibles")


def test_read_image_uses_selected_spanish_language(tmp_path, sos_api, monkeypatch):
    image_path = tmp_path / "comprobante-demo.png"
    Image.new("RGB", (200, 60), color="white").save(image_path)
    calls = []
    monkeypatch.setattr(sos_api, "get_ocr_language", lambda: "spa")
    monkeypatch.setattr(
        sos_api.pytesseract,
        "image_to_string",
        lambda image, lang: calls.append(lang) or "Factura demo",
    )

    assert sos_api.read_image_via_ocr(image_path) == "Factura demo"
    assert calls == ["spa"]


def test_build_cobro_draft_without_work_cuit_does_not_assume_context(tmp_path, sos_api):
    txt_path = tmp_path / "recibo.txt"
    txt_path.write_text(
        "\n".join(
            [
                "Fecha: 15/03/2026",
                "Cliente CUIT 20-00000000-0",
                "Banco Galicia 28/03/2026 26031621 1.800,00",
                "Retencion ganancias RG 830 26031623 500,00",
                "Factura C-0002-00000005 2.300,00",
            ]
        ),
        encoding="utf-8",
    )
    draft = sos_api.build_cobro_draft(make_args(source=[str(txt_path)]), sos_api.SOSContadorClient())
    missing = {(item["section"], item["field"]) for item in draft["validacion"]["missing_fields"]}
    assert ("contexto", "cuit_trabajo") in missing
    assert draft["contexto"]["cuit_trabajo"]["estado"] == "falta"
    assert draft["recibo"]["movimientos"]


def test_build_cobro_draft_from_structured_csv_with_resolution(tmp_path, sos_api, monkeypatch):
    csv_path = tmp_path / "recibo.csv"
    csv_path.write_text(
        "\n".join(
            [
                "tipo,cuenta,banco,fecha,numero,monto,regimen",
                "cheque,Valores A Depositar,GALICIA Y BS AS,2026-03-15,26031621,1800.00,",
                "retencion,Retencion Ganancias Sufrida,,2026-03-15,26031623,500.00,830",
            ]
        ),
        encoding="utf-8",
    )

    class DummyClient:
        base_url = "https://example.test"
        explicit_cuit = "20000000000"

        def get_session(self):
            return SimpleNamespace(cuit="20000000000")

    dummy_client = DummyClient()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1003", "nombre": "Sandbox"})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "2002",
                "clipro": "Sandbox Cliente",
                "cuit": "20000000000",
                "cuit_digits": "20000000000",
                "normalized_name": "sandbox cliente",
            }
        ],
    )
    monkeypatch.setattr(
        sos_api,
        "resolve_account_match",
        lambda client, name: {"id": "3002", "cuenta": name} if "depositar" in (name or "").lower() else {"id": "3003", "cuenta": name},
    )
    monkeypatch.setattr(sos_api, "resolve_bank_match", lambda client, name: {"id": "6001", "bancos": name})
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5002", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="20000000000")),
    )

    draft = sos_api.build_cobro_draft(
        make_args(source=[str(csv_path)], cuit_trabajo="20000000000", cliente_cuit="20000000000"),
        sos_api.SOSContadorClient(),
    )

    assert not draft["validacion"]["missing_fields"]
    assert draft["recibo"]["movimientos"][0]["banco_id"] == "6001"
    assert draft["recibo"]["movimientos"][1]["regimen"] == "830"


def test_command_cobro_create_from_draft_uses_cached_payload(tmp_path, sos_api, monkeypatch):
    draft_path = tmp_path / "draft.json"
    sos_api.save_json_file(
        draft_path,
        {
            "draft_id": "abc123",
            "created_at": sos_api.utc_now_iso(),
            "contexto": {"cuit_trabajo": {"cuit": "20000000000"}},
            "cliente": {"idclipro": "2002"},
            "recibo": {"fecha": "15/03/2026", "comentarios": "prueba", "movimientos": [], "centro_costo_id": "5002"},
            "asociacion": {"facturas": [{"comprobante": "C-0002-00000005"}]},
            "validacion": {"missing_fields": [], "timings": {}},
        },
    )

    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="20000000000"))
    monkeypatch.setattr(sos_api, "build_cobro_detail_body_from_draft", lambda draft, client: (dummy_client, {"fecha": "15/03/2026", "numero": "31599", "idclipro": "2002", "movimientos": []}))
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(save_comprobante=lambda body: {"id": "999"}, get_session=lambda: SimpleNamespace(cuit="20000000000")),
    )
    monkeypatch.setattr(sos_api, "resolve_saved_cobro_identity", lambda **kwargs: {"id": "999", "idclipro": "2002", "comprobante": "R-0000-00031599"})
    monkeypatch.setattr(sos_api, "associate_cobro_documents", lambda **kwargs: {"grupo_objetivo": [{"comprobante": "R-0000-00031599"}, {"comprobante": "C-0002-00000005"}]})

    args = make_args(draft_file=str(draft_path), confirm=True)
    result = sos_api.command_cobro_create(args, sos_api.SOSContadorClient())
    assert result["draft_id"] == "abc123"
    assert result["association"]["grupo_objetivo"][0]["comprobante"] == "R-0000-00031599"


def test_build_association_body_preserves_existing_cobro_group(sos_api):
    groups = [
        [{"id": "cobro"}, {"id": "venta-anterior"}],
        [{"id": "venta-nueva"}],
        [{"id": "otro-cobro"}, {"id": "otra-venta"}],
    ]

    body = sos_api.build_association_save_body(
        idclipro="cliente",
        groups=groups,
        target_document_ids=["cobro", "venta-nueva"],
    )

    assert {tuple(item["c"]) for item in body["a"]} == {
        ("cobro", "venta-anterior", "venta-nueva"),
        ("otro-cobro", "otra-venta"),
    }
    assert body["d"] == []


def test_build_association_body_rejects_sale_from_another_group(sos_api):
    groups = [
        [{"id": "cobro"}],
        [{"id": "otro-cobro"}, {"id": "venta-ocupada"}],
    ]

    with pytest.raises(sos_api.CLIError, match="otro grupo"):
        sos_api.build_association_save_body(
            idclipro="cliente",
            groups=groups,
            target_document_ids=["cobro", "venta-ocupada"],
        )


def test_command_cobro_create_resumes_after_association_failure(tmp_path, sos_api, monkeypatch):
    draft_path = tmp_path / "draft.json"
    sos_api.save_json_file(
        draft_path,
        {
            "draft_id": "resume123",
            "created_at": sos_api.utc_now_iso(),
            "contexto": {"cuit_trabajo": {"cuit": "20000000000"}},
            "cliente": {"idclipro": "2002"},
            "recibo": {"fecha": "15/03/2026", "comentarios": "prueba", "movimientos": [], "centro_costo_id": "5002"},
            "asociacion": {"facturas": [{"comprobante": "C-0002-00000005"}]},
            "validacion": {"missing_fields": [], "timings": {}},
        },
    )

    dummy_client = SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="20000000000"))
    body = {"fecha": "15/03/2026", "numero": "31599", "idclipro": "2002", "movimientos": []}
    counters = {"save": 0, "resolve": 0, "associate": 0}

    class FakeWebClient:
        def save_comprobante(self, payload):
            counters["save"] += 1
            return {"id": "999"}

    def resolve_identity(**kwargs):
        counters["resolve"] += 1
        return {"id": "999", "idclipro": "2002", "comprobante": "R-0000-00031599"}

    def associate(**kwargs):
        counters["associate"] += 1
        if counters["associate"] == 1:
            raise sos_api.CLIError("fallo posterior simulado")
        return {"grupo_objetivo": [{"id": "999"}, {"id": "venta"}]}

    monkeypatch.setattr(sos_api, "build_cobro_detail_body_from_draft", lambda draft, client: (dummy_client, body))
    monkeypatch.setattr(sos_api, "SOSContadorWebClient", lambda *args, **kwargs: FakeWebClient())
    monkeypatch.setattr(sos_api, "resolve_saved_cobro_identity", resolve_identity)
    monkeypatch.setattr(sos_api, "associate_cobro_documents", associate)

    args = make_args(draft_file=str(draft_path), confirm=True)
    with pytest.raises(sos_api.CLIError, match="fallo posterior"):
        sos_api.command_cobro_create(args, sos_api.SOSContadorClient())

    result = sos_api.command_cobro_create(args, sos_api.SOSContadorClient())

    assert result["id"] == "999"
    assert counters == {"save": 1, "resolve": 1, "associate": 2}
    persisted = sos_api.load_json_file(draft_path, {})
    assert persisted["execution"]["save_payload"] == {"id": "999"}
    assert persisted["execution"]["cobro_identity"]["id"] == "999"


def test_extract_invoice_candidates_ignores_retention_like_tokens(sos_api):
    items = sos_api.extract_invoice_candidates(
        [
            "Retencion ganancias RG 830 26031623 500,00",
            "Factura C-0002-00000005 4500,00",
        ],
        [],
    )

    assert [item["comprobante"] for item in items] == ["C-0002-00000005"]


def test_build_cobro_draft_retention_uses_document_date_and_not_invoice(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "retencion.txt"
    txt_path.write_text(
        "\n".join(
            [
                "Fecha: 15/03/2026",
                "Retencion ganancias RG 830 26031623 500,00",
                "Factura C-0002-00000005 4500,00",
            ]
        ),
        encoding="utf-8",
    )

    class DummyClient:
        base_url = "https://example.test"
        explicit_cuit = "20000000000"

        def get_session(self):
            return SimpleNamespace(cuit="20000000000")

    dummy_client = DummyClient()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1003", "nombre": "Sandbox"})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "2002",
                "clipro": "Cliente Persona Demo",
                "cuit": "20000000000",
                "cuit_digits": "20000000000",
                "normalized_name": "cliente persona demo",
            }
        ],
    )
    monkeypatch.setattr(
        sos_api,
        "resolve_account_match",
        lambda client, name: {"id": "3003", "cuenta": name} if "ganancias" in (name or "").lower() else {"id": "3002", "cuenta": name},
    )
    monkeypatch.setattr(sos_api, "resolve_bank_match", lambda client, name: None)
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5002", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="20000000000")),
    )

    draft = sos_api.build_cobro_draft(
        make_args(source=[str(txt_path)], cuit_trabajo="20000000000", cliente_nombre="Cliente Persona Demo"),
        sos_api.SOSContadorClient(),
    )

    assert draft["asociacion"]["facturas"][0]["comprobante"] == "C-0002-00000005"
    assert len(draft["asociacion"]["facturas"]) == 1
    assert draft["recibo"]["movimientos"][0]["fecha"] == "2026-03-15"
    assert not draft["validacion"]["missing_fields"]


def test_extract_document_comment_preserves_order_number(sos_api):
    comment = sos_api.extract_document_comment(["Ref:Orden de pago Nro.  -00000001"])
    assert comment["value"] == "Orden de pago Nro. -00000001"


def test_parse_line_movements_extracts_cheque_after_invoice_segment(sos_api, monkeypatch):
    monkeypatch.setattr(sos_api, "get_bank_catalog", lambda client: [{"id": "6001", "bancos": "GALICIA Y BS AS"}])
    movements = sos_api.parse_line_movements(
        [
            "8.833.000,00 09/01/2025 FC A 00001-00000003 Chp DE GALICIA Y BS.AS. -007 6/03/2025 1.400.000,00 $Nro. 10000010",
        ],
        SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000")),
    )

    assert len(movements) == 1
    assert movements[0]["tipo"] == "cheque"
    assert movements[0]["numero"] == "10000010"
    assert movements[0]["banco_nombre"] == "GALICIA Y BS AS"


def test_parse_line_movements_extracts_rg830_retention(sos_api, monkeypatch):
    monkeypatch.setattr(sos_api, "get_bank_catalog", lambda client: [])
    movements = sos_api.parse_line_movements(
        ["RG.830 ENAJ.BS MBLES Insc 141.520,00 F1"],
        SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000")),
    )

    assert len(movements) == 1
    assert movements[0]["tipo"] == "retencion"
    assert movements[0]["regimen"] == "830"
    assert movements[0]["cuenta_nombre"] == "Retencion Ganancias Sufrida"


def test_build_cobro_draft_fc_medical_sample_extracts_all_items(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "empresa-demo.txt"
    txt_path.write_text(
        "\n".join(
            [
                "00000010",
                "Fecha:",
                "Cert de reten ganancias",
                "16/01/2025",
                "CLIENTE DEMO S.A.",
                "Nro. de CUIT : 30-00000000-1",
                "000001 EMPRESA DEMO SRL",
                "Nro de C.U.I.T.:30-00000000-0",
                "Ref:Orden de pago Nro.  -00000001",
                "RG.830 ENAJ.BS MBLES Insc 830 - F1 $ 141.520,00",
                "09/01/2025 FC  A 00001-00000003 8.833.000,00 $",
                "8.833.000,00 09/01/2025 FC  A 00001-00000003 Chp DE GALICIA Y BS.AS. -007 6/03/2025 1.400.000,00 $Nro. 10000010",
                "Chp DE GALICIA Y BS.AS. -007 11/03/2025 1.400.000,00 $Nro. 10000011",
                "Chp DE GALICIA Y BS.AS. -007 17/03/2025 1.400.000,00 $Nro. 10000012",
                "Chp DE GALICIA Y BS.AS. -007 20/03/2025 1.400.000,00 $Nro. 10000013",
                "Chp DE GALICIA Y BS.AS. -007 26/03/2025 1.400.000,00 $Nro. 10000014",
                "Chp DE GALICIA Y BS.AS. -007 31/03/2025 1.691.480,00 $Nro. 10000015",
                "RG.830 ENAJ.BS MBLES Insc 141.520,00 F1",
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
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1001", "nombre": "Empresa Demo S.R.L."})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "2001",
                "clipro": "Cliente Demo S.A.",
                "cuit": "30-00000000-1",
                "cuit_digits": "30000000001",
                "normalized_name": "cliente demo s a",
            }
        ],
    )
    monkeypatch.setattr(
        sos_api,
        "resolve_account_match",
        lambda client, name: {"id": "3002", "cuenta": name}
        if "depositar" in (name or "").lower()
        else {"id": "3004", "cuenta": name},
    )
    monkeypatch.setattr(sos_api, "resolve_bank_match", lambda client, name: {"id": "6001", "bancos": "GALICIA Y BS AS"} if name else None)
    monkeypatch.setattr(sos_api, "get_bank_catalog", lambda client: [{"id": "6001", "bancos": "GALICIA Y BS AS"}])
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5001", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000")),
    )

    draft = sos_api.build_cobro_draft(
        make_args(source=[str(txt_path)], cuit_trabajo="30000000000"),
        sos_api.SOSContadorClient(),
    )

    assert draft["cliente"]["idclipro"] == "2001"
    assert draft["cliente"]["nombre"] == "Cliente Demo S.A."
    assert draft["cliente"]["cuit"] == "30000000001"
    assert draft["recibo"]["comentarios"] == "Orden de pago Nro. -00000001"
    assert len(draft["recibo"]["movimientos"]) == 7
    assert any(item["numero"] == "10000010" for item in draft["recibo"]["movimientos"])
    assert any(item["tipo"] == "retencion" and item["regimen"] == "830" for item in draft["recibo"]["movimientos"])
    assert draft["recibo"]["total"] == "8833000.00"
    assert draft["asociacion"]["diferencia"] == "0.00"
    assert not draft["validacion"]["missing_fields"]


def test_search_paginated_uses_total_pages_when_backend_ignores_registros(sos_api):
    class DummyClient:
        def __init__(self):
            self.calls = []

        def request(self, method, path, query=None):
            self.calls.append(query or [])
            page = next(int(value) for key, value in (query or []) if key == "pagina")
            if page == 1:
                return {"items": [{"id": "1", "cuit": "30000000009"}], "paginas": 2}
            return {"items": [{"id": "2", "cuit": "30000000001"}], "paginas": 2}

    client = DummyClient()
    match = sos_api.search_paginated(
        client,
        path="cliente/listado",
        query=[("cliente", "true"), ("proveedor", "true"), ("pagina", "1"), ("registros", "1000")],
        predicate=lambda item: item.get("cuit") == "30000000001",
    )

    assert match["id"] == "2"
    assert len(client.calls) == 2


def test_build_cobro_draft_uses_local_profile_before_generic(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "acme.txt"
    txt_path.write_text(
        "\n".join(
            [
                "ACME Demo S.A.",
                "CUIT 30-00000003-4",
                "Fecha cobro 18/03/2026",
                "Orden de pago OP-7788",
                "CHEQUE ESPECIAL 18/03/2026 99999999 1.250.000,00",
                "Factura A-0001-00001234 18/03/2026 1.250.000,00",
            ]
        ),
        encoding="utf-8",
    )

    profile_dir = tmp_path / "profiles"
    monkeypatch.setattr(sos_api, "DOCUMENT_PROFILE_ROOT", profile_dir)

    manifest = {
        "profile_id": "acme-op",
        "name": "ACME OP",
        "work_cuit": "30000000000",
        "counterparty_cuit": "30000000034",
        "document_kind": "cobro_recibo",
        "priority": 100,
        "required_text": ["acme demo", "orden de pago"],
    }
    rules = {
        "fields": {
            "fecha": [
                {
                    "scope": "line",
                    "pattern": r"Fecha cobro (?P<fecha>\d{1,2}/\d{1,2}/\d{4})",
                    "value_group": "fecha",
                    "transform": "date",
                }
            ],
            "comentarios": [
                {
                    "scope": "line",
                    "pattern": r"(?P<comentarios>Orden de pago OP-\d+)",
                    "value_group": "comentarios",
                    "transform": "normalize-space",
                    "flags": ["ignorecase"],
                }
            ],
            "cliente_cuit": [
                {
                    "scope": "line",
                    "pattern": r"CUIT (?P<cliente_cuit>30-00000003-4)",
                    "value_group": "cliente_cuit",
                    "transform": "digits",
                }
            ],
            "cliente_nombre": [
                {
                    "scope": "line",
                    "pattern": r"(?P<cliente_nombre>ACME Demo S\.A\.)",
                    "value_group": "cliente_nombre",
                    "transform": "normalize-space",
                    "flags": ["ignorecase"],
                }
            ],
        },
        "movimientos": [
            {
                "tipo": "cheque",
                "scope": "line",
                "pattern": r"CHEQUE ESPECIAL (?P<fecha>\d{1,2}/\d{1,2}/\d{4}) (?P<numero>\d{8}) (?P<monto>\d{1,3}(?:\.\d{3})*,\d{2})",
                "groups": {"fecha": "fecha", "numero": "numero", "monto": "monto"},
                "transforms": {"fecha": "date", "numero": "digits", "monto": "decimal"},
                "defaults": {"cuenta_nombre": "Valores A Depositar", "banco_nombre": "GALICIA Y BS AS"},
            }
        ],
        "facturas": [
            {
                "scope": "line",
                "pattern": r"Factura (?P<comprobante>A-0001-00001234) (?P<fecha>\d{1,2}/\d{1,2}/\d{4}) (?P<total>\d{1,3}(?:\.\d{3})*,\d{2})",
                "groups": {"comprobante": "comprobante", "fecha": "fecha", "total": "total"},
                "transforms": {"comprobante": "comprobante", "fecha": "date", "total": "decimal"},
                "flags": ["ignorecase"],
            }
        ],
    }
    profile_path = profile_dir / "30000000000" / "30000000034" / "cobro_recibo" / "acme-op"
    sos_api.save_json_file(profile_path / "manifest.json", manifest)
    sos_api.save_json_file(profile_path / "rules.json", rules)

    class DummyClient:
        base_url = "https://example.test"
        explicit_cuit = "30000000000"

        def get_session(self):
            return SimpleNamespace(cuit="30000000000")

    dummy_client = DummyClient()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1001", "nombre": "Empresa Demo"})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "1002",
                "clipro": "ACME Demo S.A.",
                "cuit": "30-00000003-4",
                "cuit_digits": "30000000034",
                "normalized_name": "acme demo s a",
            }
        ],
    )
    monkeypatch.setattr(sos_api, "parse_structured_movements", lambda rows: [])
    monkeypatch.setattr(sos_api, "parse_line_movements", lambda lines, client: [])
    monkeypatch.setattr(sos_api, "resolve_account_match", lambda client, name: {"id": "1", "cuenta": name})
    monkeypatch.setattr(sos_api, "resolve_bank_match", lambda client, name: {"id": "6001", "bancos": name})
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5002", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="30000000000")),
    )

    draft = sos_api.build_cobro_draft(
        make_args(source=[str(txt_path)], cuit_trabajo="30000000000"),
        sos_api.SOSContadorClient(),
    )

    assert draft["contexto"]["extraccion"]["origen"] == "perfil_local"
    assert draft["cliente"]["idclipro"] == "1002"
    assert draft["recibo"]["comentarios"] == "Orden de pago OP-7788"
    assert draft["recibo"]["movimientos"][0]["numero"] == "99999999"
    assert draft["asociacion"]["facturas"][0]["comprobante"] == "A-0001-00001234"


def test_command_cobro_profile_create_scaffolds_local_profile(tmp_path, sos_api, monkeypatch):
    draft_path = tmp_path / "draft.json"
    sos_api.save_json_file(
        draft_path,
        {
            "draft_id": "draft123",
            "created_at": sos_api.utc_now_iso(),
            "contexto": {
                "cuit_trabajo": {"cuit": "30000000000"},
                "fuentes": [{"path": str(tmp_path / "fuente.pdf"), "kind": "pdf"}],
            },
            "cliente": {
                "nombre": "Cliente Demo S.A.",
                "cuit": "30000000001",
            },
            "recibo": {
                "fecha": "16/01/2025",
                "fecha_source_text": "Fecha 16/01/2025",
                "comentarios": "Orden de pago Nro. -00000001",
                "comentarios_source_text": "Ref:Orden de pago Nro. -00000001",
                "movimientos": [
                    {
                        "tipo": "cheque",
                        "cuenta_nombre": "Valores A Depositar",
                        "banco_nombre": "GALICIA Y BS AS",
                        "fecha": "2025-03-06",
                        "numero": "10000010",
                        "monto": "1400000.00",
                        "source_text": "Chp DE GALICIA Y BS.AS. -007 6/03/2025 1.400.000,00 $Nro. 10000010",
                    },
                    {
                        "tipo": "retencion",
                        "cuenta_nombre": "Retencion Ganancias Sufrida",
                        "fecha": "2025-01-16",
                        "regimen": "830",
                        "monto": "141520.00",
                        "source_text": "RG.830 ENAJ.BS MBLES Insc 141.520,00 F1",
                    },
                ],
            },
            "asociacion": {
                "facturas": [
                    {
                        "comprobante": "A-0001-00000003",
                        "fecha": "2025-01-09",
                        "total": "8833000.00",
                        "source_text": "09/01/2025 FC A 00001-00000003 8.833.000,00 $",
                    }
                ]
            },
            "validacion": {"missing_fields": [], "timings": {}},
        },
    )

    monkeypatch.setattr(sos_api, "DOCUMENT_PROFILE_ROOT", tmp_path / "profiles")
    result = sos_api.command_cobro_profile_create(
        make_args(draft_file=str(draft_path), name="Cliente Demo OP Perfil", document_kind="cobro_recibo", source=[str(tmp_path / "fuente.pdf")]),
        sos_api.SOSContadorClient(),
    )

    manifest = sos_api.load_json_file(Path(result["manifest_file"]), {})
    rules = sos_api.load_json_file(Path(result["rules_file"]), {})

    assert result["profile_id"] == "cliente-demo-op-perfil"
    assert manifest["work_cuit"] == "30000000000"
    assert manifest["counterparty_cuit"] == "30000000001"
    assert rules["movimientos"]
    assert rules["facturas"]
    retention_rules = [item for item in rules["movimientos"] if item.get("tipo") == "retencion"]
    assert retention_rules[0]["defaults"]["fecha"] == "__DOCUMENT_DATE__"


def test_command_cobro_draft_preview_markdown_returns_tables(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "recibo.txt"
    txt_path.write_text(
        "\n".join(
            [
                "Fecha: 15/03/2026",
                "Cliente CUIT 20-00000000-0",
                "Banco Galicia 28/03/2026 26031621 1.800,00",
                "Factura C-0002-00000005 1.800,00",
            ]
        ),
        encoding="utf-8",
    )

    class DummyClient:
        base_url = "https://example.test"
        explicit_cuit = "20000000000"

        def get_session(self):
            return SimpleNamespace(cuit="20000000000")

    dummy_client = DummyClient()
    monkeypatch.setattr(sos_api, "ensure_bound_client", lambda client, cuit=None, cuit_id=None: dummy_client)
    monkeypatch.setattr(sos_api, "resolve_work_cuit_context", lambda client, cuit: {"cuit": cuit, "cuit_id": "1003", "nombre": "Sandbox"})
    monkeypatch.setattr(
        sos_api,
        "get_client_catalog",
        lambda client: [
            {
                "idclipro": "2002",
                "clipro": "Consumidor Final",
                "cuit": "20000000000",
                "cuit_digits": "20000000000",
                "normalized_name": "consumidor final",
            }
        ],
    )
    monkeypatch.setattr(sos_api, "resolve_account_match", lambda client, name: {"id": "3005", "cuenta": "Banco"})
    monkeypatch.setattr(sos_api, "resolve_bank_match", lambda client, name: {"id": "6001", "bancos": "GALICIA Y BS AS"})
    monkeypatch.setattr(sos_api, "resolve_centrocosto_match", lambda web_client, name: {"id": "5002", "centrocosto": "General"})
    monkeypatch.setattr(sos_api, "save_draft_payload", lambda payload: tmp_path / "draft.json")
    monkeypatch.setattr(
        sos_api,
        "SOSContadorWebClient",
        lambda *args, **kwargs: SimpleNamespace(get_session=lambda: SimpleNamespace(cuit="20000000000")),
    )

    result = sos_api.command_cobro_draft(
        make_args(source=[str(txt_path)], cuit_trabajo="20000000000", cliente_nombre="Consumidor Final", preview_format="markdown"),
        sos_api.SOSContadorClient(),
    )

    assert isinstance(result, str)
    assert "**Contexto**" in result
    assert "| Tipo | Cuenta destino | Banco/Régimen | Número | Fecha | Monto | Estado |" in result
    assert "Total recibo:" in result


def test_legacy_profile_retention_default_date_is_replaced_with_document_date(tmp_path, sos_api, monkeypatch):
    txt_path = tmp_path / "legacy.txt"
    txt_path.write_text(
        "\n".join(
            [
                "Fecha cobro 18/04/2026",
                "ACME Demo S.A.",
                "CUIT 30-00000003-4",
                "RG.830 ENAJ.BS MBLES Insc 125.000,00 F1",
            ]
        ),
        encoding="utf-8",
    )

    profile_dir = tmp_path / "profiles"
    monkeypatch.setattr(sos_api, "DOCUMENT_PROFILE_ROOT", profile_dir)
    profile_path = profile_dir / "30000000000" / "30000000034" / "cobro_recibo" / "legacy-acme"
    sos_api.save_json_file(
        profile_path / "manifest.json",
        {
            "profile_id": "legacy-acme",
            "name": "Legacy ACME",
            "work_cuit": "30000000000",
            "counterparty_cuit": "30000000034",
            "document_kind": "cobro_recibo",
            "required_text": ["acme demo"],
            "priority": 100,
        },
    )
    sos_api.save_json_file(
        profile_path / "rules.json",
        {
            "fields": {
                "fecha": [
                    {
                        "scope": "line",
                        "pattern": r"Fecha cobro (?P<fecha>\d{1,2}/\d{1,2}/\d{4})",
                        "value_group": "fecha",
                        "transform": "date",
                    }
                ],
                "cliente_cuit": [
                    {
                        "scope": "line",
                        "pattern": r"CUIT (?P<cliente_cuit>30-00000003-4)",
                        "value_group": "cliente_cuit",
                        "transform": "digits",
                    }
                ],
            },
            "movimientos": [
                {
                    "tipo": "retencion",
                    "scope": "line",
                    "pattern": r"RG\.(?P<regimen>\d{2,4}).*?(?P<monto>\d{1,3}(?:\.\d{3})*,\d{2})",
                    "groups": {"regimen": "regimen", "monto": "monto"},
                    "transforms": {"regimen": "digits", "monto": "decimal"},
                    "defaults": {"cuenta_nombre": "Retencion Ganancias Sufrida", "fecha": "2025-01-16"},
                    "flags": ["ignorecase"],
                }
            ],
        },
    )

    payload = sos_api.extract_document_profile_payload(
        {
            "manifest": sos_api.load_json_file(profile_path / "manifest.json", {}),
            "rules": sos_api.load_json_file(profile_path / "rules.json", {}),
            "path": profile_path,
        },
        extracted_sources=[sos_api.extract_source_document(txt_path)],
    )

    assert payload["fecha"]["value"] == "2026-04-18"
    assert payload["movimientos"][0]["fecha"] == "2026-04-18"




