from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "sos-contador-api"
    / "scripts"
    / "sos_contador_api.py"
)


@pytest.fixture(scope="session")
def sos_api(tmp_path_factory):
    runtime_home = tmp_path_factory.mktemp("sos-contador-home")
    previous_home = os.environ.get("SOS_CONTADOR_HOME")
    os.environ["SOS_CONTADOR_HOME"] = str(runtime_home)
    module_name = "sos_contador_api_test_module"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        if previous_home is None:
            os.environ.pop("SOS_CONTADOR_HOME", None)
        else:
            os.environ["SOS_CONTADOR_HOME"] = previous_home


@pytest.fixture(autouse=True)
def fake_cuit_catalog(monkeypatch, sos_api):
    catalog = [
        {"id": "1001", "cuit": "30000000000", "razon_social": "Empresa Demo S.R.L."},
        {"id": "1002", "cuit": "30000000001", "razon_social": "Cliente Demo S.A."},
        {"id": "1003", "cuit": "20000000000", "razon_social": "Sandbox"},
        {"id": "1004", "cuit": "30000000034", "razon_social": "ACME Demo S.A."},
    ]
    monkeypatch.setattr(sos_api, "ensure_cuit_catalog", lambda client, refresh=False: catalog)
