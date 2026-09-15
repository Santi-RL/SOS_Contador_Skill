from argparse import Namespace
import importlib.util
from pathlib import Path
import urllib.error

import pytest


@pytest.mark.parametrize("argv", [
    ["call", "--method", "GET", "--path", "unknown"],
    ["cliente", "update", "--id", "1", "--confirm"],
    ["cliente", "delete", "--id", "1", "--confirm"],
    ["api", "invoke", "--operation", "venta.save", "--confirm"],
    ["api", "invoke", "--operation", "cuentacorriente.list"],
    ["api", "invoke", "--operation", "centrocosto.create", "--dry-run"],
    ["cobro", "profile", "create"],
    ["venta", "create", "--obtienecae", "--confirm"],
    ["pago", "create", "--body-json", '{"id":"1"}', "--confirm"],
    ["pago", "create", "--movimientos-json", "[]", "--confirm"],
    ["cliente", "create", "--body-json", '{"rol":"proveedor"}', "--confirm"],
    ["afip", "import", "--source", "demo.xlsx", "--confirm"],
])
def test_operational_boundary_stops_before_client_creation(sos_api, monkeypatch, argv):
    monkeypatch.setattr(sos_api, "SOSContadorClient", lambda: pytest.fail("No debe autenticarse"))
    assert sos_api.main(argv) == 1


@pytest.mark.parametrize("argv", [
    ["api", "invoke", "--operation", "venta.search"],
    ["api", "invoke", "--operation", "mayor.list"],
    ["compra", "create", "--draft-id", "demo", "--confirm"],
    ["cobro", "create", "--draft-id", "demo", "--confirm"],
    ["venta", "create", "--productos-json", "[]"],
    ["pago", "create", "--imputaciones-json", "[]"],
])
def test_known_recipes_remain_available(sos_api, argv):
    sos_api.ensure_work_mode_allowed(sos_api.build_parser().parse_args(argv))


def test_development_cannot_write_even_with_confirm(sos_api):
    with pytest.raises(sos_api.CLIError, match="Modo desarrollo"):
        sos_api.ensure_mutation_allowed("PUT", "venta", None, {},
                                        Namespace(work_mode="development", confirm=True))


def test_development_can_preview_without_writing(sos_api):
    with pytest.raises(SystemExit) as result:
        sos_api.ensure_mutation_allowed("PUT", "venta", None, {},
                                        Namespace(work_mode="development", dry_run=True))
    assert result.value.code == 0


def test_controlled_mode_cannot_run_unfrozen_import(sos_api, monkeypatch):
    monkeypatch.setattr(sos_api, "SOSContadorClient", lambda: pytest.fail("No debe autenticarse"))
    assert sos_api.main(["--work-mode", "controlled-validation", "afip", "import",
                         "--source", "demo.xlsx", "--confirm"]) == 1


def test_controlled_validation_keeps_confirmation_and_cae_separate(sos_api):
    with pytest.raises(sos_api.CLIError, match="--confirm"):
        sos_api.ensure_mutation_allowed("PUT", "venta", None, {}, Namespace(work_mode="controlled-validation"))
    with pytest.raises(sos_api.CLIError, match="CAE bloqueada"):
        sos_api.ensure_mutation_allowed("PUT", "venta", None, {"obtienecae": True},
                                        Namespace(work_mode="controlled-validation", confirm=True))
    sos_api.ensure_mutation_allowed("PUT", "venta", None, {"obtienecae": True},
                                    Namespace(work_mode="controlled-validation", confirm=True, approve_cae=True))


@pytest.mark.parametrize("method,path,expected", [("PUT", "compra/0", 1),
    ("POST", "cliente", 1), ("POST", "venta/consulta", 3), ("GET", "venta/detalle/1", 3)])
def test_api_timeouts_retry_only_known_reads(sos_api, monkeypatch, method, path, expected):
    calls = []
    def timeout(*args, **kwargs):
        calls.append(args)
        raise urllib.error.URLError(TimeoutError("demo"))
    monkeypatch.setattr(sos_api.urllib.request, "urlopen", timeout)
    monkeypatch.setattr(sos_api.time, "sleep", lambda seconds: None)
    with pytest.raises(sos_api.CLIError):
        sos_api.SOSContadorClient()._send_request_raw(method=method, path=path)
    assert len(calls) == expected


@pytest.mark.parametrize("json_request,path,body,expected", [
    (True, "back/comprobante_altamodi.asp", {}, 1),
    (True, "back/asociaciones_altamodi.asp", {}, 1),
    (False, "back/comprobante_altamodi.asp", {}, 1),
    (False, "back/xml.asp", {"object": "comprobante_historia"}, 3),
    (True, "back/xml.asp", {"object": "unknown_write"}, 1),
])
def test_web_timeouts_never_repeat_business_writes(sos_api, monkeypatch, json_request, path, body, expected):
    calls = []
    class Opener:
        def open(self, *args, **kwargs):
            calls.append(args)
            raise TimeoutError("demo")
    client = object.__new__(sos_api.SOSContadorWebClient)
    client.base_url = "https://example.invalid"
    client.opener = Opener()
    monkeypatch.setattr(sos_api.time, "sleep", lambda seconds: None)
    with pytest.raises(sos_api.CLIError):
        if json_request:
            client._request_json_raw("POST", path, body=body)
        else:
            client._request_raw("POST", path, form=body)
    assert len(calls) == expected


def test_cobro_detail_does_not_silently_open_web(sos_api, monkeypatch):
    class Client:
        def request(self, *args, **kwargs):
            return {"error": "demo"}
    monkeypatch.setattr(sos_api, "bind_business_client", lambda c, a, required: (c, {}))
    monkeypatch.setattr(sos_api, "resolve_cobro_id_from_lookup", lambda a, c: "1")
    monkeypatch.setattr(sos_api, "should_fallback_cobro_detail", lambda p: True)
    monkeypatch.setattr(sos_api, "SOSContadorWebClient", lambda **kw: pytest.fail("Fallback no autorizado"))
    with pytest.raises(sos_api.CLIError, match="No se cambió de transporte"):
        sos_api.command_cobro_get(Namespace(), Client())


def test_outputs_reject_repository_and_existing_files(sos_api, monkeypatch, tmp_path):
    package = tmp_path / "repo" / "skill"
    package.mkdir(parents=True)
    (package.parent / ".git").mkdir()
    monkeypatch.setattr(sos_api, "SKILL_ROOT", package)
    monkeypatch.setattr(sos_api, "RUNTIME_HOME", tmp_path / "private")
    with pytest.raises(sos_api.CLIError, match="repositorio"):
        sos_api.ensure_cli_storage_allowed(Namespace(out=str(package / "export.json")))
    source = tmp_path / "original.pdf"
    source.write_bytes(b"original")
    with pytest.raises(sos_api.CLIError, match="ya existe"):
        sos_api.ensure_cli_storage_allowed(Namespace(out=str(source)))
    assert source.read_bytes() == b"original"
    with pytest.raises(sos_api.CLIError, match="ya existe"):
        sos_api.write_binary_output(str(source), b"replacement")
    assert source.read_bytes() == b"original"


def test_inventory_hashes_preserves_sources_and_does_not_follow_git(tmp_path):
    script = Path(__file__).resolve().parents[1] / "sos-contador-api/scripts/audit_workspace.py"
    spec = importlib.util.spec_from_file_location("audit_workspace", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "original.txt").write_text("documento ficticio", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    result = module.inventory(tmp_path)
    assert len(result["files"]) == 1
    assert len(result["files"][0]["sha256"]) == 64
    assert (tmp_path / "original.txt").read_text(encoding="utf-8") == "documento ficticio"
    assert result["skipped"] == [".git"]
