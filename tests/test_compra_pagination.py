from copy import deepcopy
from types import SimpleNamespace

import pytest


DATE = "2026-02-03"


def purchase(index, **overrides):
    return {
        "id": index,
        "fecha": DATE + "T03:00:00.000Z",
        "factura": f"FA-0001-{index:08d}",
        "clipro": {"cuit": "30000000034"},
        **overrides,
    }


class OffsetServer:
    """Fictitious API: pagina is a 1-based starting position, not a page number."""

    def __init__(self, rows, *, cap=50):
        self.rows = rows
        self.cap = cap
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, deepcopy(kwargs)))
        assert (method, path) == ("POST", "compra/consulta")
        query = dict(kwargs["query"])
        start = int(query["pagina"]) - 1
        size = min(int(query["registros"]), self.cap)
        return {"items": deepcopy(self.rows[start:start + size])}


@pytest.mark.parametrize("count,positions", [
    (0, [1]),
    (1, [1, 2]),
    (50, [1, 51]),
    (123, [1, 51, 101, 124]),
])
def test_offset_walk_covers_same_day_and_checks_empty_tail(sos_api, count, positions):
    rows = [purchase(i) for i in range(1, count + 1)]
    server = OffsetServer(rows)

    assert sos_api.fetch_compra_consulta_items(server, desde=DATE, hasta=DATE) == rows
    assert [int(dict(call[2]["query"])["pagina"]) for call in server.calls] == positions
    assert all(call[2]["body"] == {"fecha_desde": DATE, "fecha_hasta": DATE}
               for call in server.calls)


def test_short_pages_do_not_hide_rows_when_server_caps_page_size(sos_api):
    rows = [purchase(i) for i in range(1, 8)]
    server = OffsetServer(rows, cap=2)

    assert sos_api.fetch_compra_consulta_items(server, desde=DATE, hasta=DATE) == rows
    assert [dict(call[2]["query"])["pagina"] for call in server.calls] == ["1", "3", "5", "7", "8"]


@pytest.mark.parametrize("payload", [
    None, {}, {"items": None}, {"items": {}},
    {"items": [None]}, {"items": [{}]},
    {"items": [purchase(True)]}, {"items": [purchase(0)]},
    {"items": [purchase(1, fecha=None)]},
    {"items": [purchase(1, fecha="2026-02-30")]},
    {"items": [purchase(1, fecha="2026-02-04T03:00:00Z")]},
    {"items": [purchase(1), purchase(1)]},
])
def test_bad_response_cannot_be_interpreted_as_no_duplicates(sos_api, payload):
    client = SimpleNamespace(request=lambda *args, **kwargs: payload)
    with pytest.raises(sos_api.CLIError, match="Cobertura de compras incompleta"):
        sos_api.fetch_compra_consulta_items(client, desde=DATE, hasta=DATE)


def test_repeated_page_stops_instead_of_returning_deduplicated_partial_data(sos_api):
    calls = []

    def ignored_position(*args, **kwargs):
        calls.append(kwargs)
        return {"items": [purchase(1), purchase(2)]}

    with pytest.raises(sos_api.CLIError, match="repetidos"):
        sos_api.fetch_compra_consulta_items(
            SimpleNamespace(request=ignored_position), desde=DATE, hasta=DATE, batch_size=2,
        )
    assert len(calls) == 2


def test_oversized_page_and_request_budget_are_not_reported_complete(sos_api):
    oversized = SimpleNamespace(request=lambda *a, **k: {"items": [purchase(1), purchase(2)]})
    with pytest.raises(sos_api.CLIError, match="tamaño solicitado"):
        sos_api.fetch_compra_consulta_items(oversized, desde=DATE, hasta=DATE, batch_size=1)

    server = OffsetServer([purchase(i) for i in range(1, 51)])
    with pytest.raises(sos_api.CLIError, match="límite de 1 consultas"):
        sos_api.fetch_compra_consulta_items(server, desde=DATE, hasta=DATE, max_pages=1)
    assert len(server.calls) == 1


def test_api_failure_after_a_page_is_not_swallowed(sos_api):
    calls = []

    def request(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {"items": [purchase(1)]}
        raise sos_api.APIError(503, "Fictitious unavailable service", None)

    with pytest.raises(sos_api.APIError):
        sos_api.fetch_compra_consulta_items(SimpleNamespace(request=request), desde=DATE, hasta=DATE)
    assert len(calls) == 2


@pytest.mark.parametrize("kwargs", [
    {"desde": "03/02/2026"}, {"desde": "2026-02-30"},
    {"hasta": "2026-02-02"}, {"desde": None},
    {"batch_size": 0}, {"batch_size": 51}, {"batch_size": True},
    {"max_pages": 0}, {"max_pages": 101},
])
def test_invalid_query_is_rejected_before_request(sos_api, kwargs):
    options = {"desde": DATE, "hasta": DATE, **kwargs}
    client = SimpleNamespace(request=lambda *a, **k: pytest.fail("Must not query"))
    with pytest.raises(sos_api.CLIError):
        sos_api.fetch_compra_consulta_items(client, **options)


def test_duplicate_after_first_fifty_prevents_a_new_purchase(sos_api, monkeypatch):
    target = purchase(9001, factura="FA-0002-00000077", clipro={"cuit": "30000000015"})
    server = OffsetServer([purchase(i) for i in range(1, 71)] + [target])
    original_request = server.request

    def request(method, path, **kwargs):
        if (method, path) == ("GET", "compra/detalle/9001"):
            return {"cabecera": {"id": 9001}}
        return original_request(method, path, **kwargs)

    server.request = request
    monkeypatch.setattr(sos_api, "summarize_compra_detail_for_afip", lambda detail: {})
    monkeypatch.setattr(sos_api, "compra_summary_matches_expected", lambda *a, **k: True)
    result = sos_api.find_compra_duplicate(server, fields={
        "fecha": DATE, "proveedor_cuit": "30000000015", "fcncnd": "F", "letra": "A",
        "puntoventa": 2, "numero": 77, "amounts": {},
    })
    assert result["kind"] == "exact"
    assert result["id"] == 9001
    assert len(server.calls) == 3


@pytest.mark.parametrize("include_inactive,expected", [(False, [1]), (True, [1, 2, 3])])
def test_range_command_is_bound_read_only_and_filters_inactive(
    sos_api, monkeypatch, include_inactive, expected,
):
    client = OffsetServer([purchase(1), purchase(2, cancelado=1), purchase(3, archivado=True)])
    target = {"cuit": "30000000000", "cuit_id": "1001"}
    args = sos_api.build_parser().parse_args([
        "compra", "list-range", "--cuit-trabajo", target["cuit"], "--desde", DATE, "--hasta", DATE,
        *(["--incluir-inactivos"] if include_inactive else []),
    ])
    sos_api.ensure_work_mode_allowed(args)

    def bind(original, received, *, required):
        assert received.cuit_trabajo == target["cuit"] and required
        return client, target

    monkeypatch.setattr(sos_api, "bind_business_client", bind)
    result = sos_api.command_compra_list_range(args, object())
    assert [row["id"] for row in result["items"]] == expected
    assert result["contexto"] == target
    assert result["pagination_finished"] is True
    assert result["excluded_inactive"] == 3 - len(expected)


def test_range_command_rejects_bad_dates_before_binding(sos_api, monkeypatch):
    monkeypatch.setattr(sos_api, "bind_business_client", lambda *a, **k: pytest.fail("Must not bind"))
    args = SimpleNamespace(desde="invalid", hasta=DATE, registros=50, max_pages=100)
    with pytest.raises(sos_api.CLIError):
        sos_api.command_compra_list_range(args, object())


def test_incomplete_post_create_read_reports_saved_purchase_and_stops(sos_api, monkeypatch):
    client = SimpleNamespace(request=lambda *a, **k: {"cabecera": {}})
    monkeypatch.setattr(sos_api, "compra_summary_matches_expected", lambda *a, **k: True)

    def incomplete(*args, **kwargs):
        raise sos_api.CLIError("Cobertura de compras incompleta")

    monkeypatch.setattr(sos_api, "fetch_compra_items_complete", incomplete)
    with pytest.raises(sos_api.CLIError, match="compra 9001 fue creada.*no repita"):
        sos_api.verify_created_compra(client, compra_id=9001, row={"fields": {}})
