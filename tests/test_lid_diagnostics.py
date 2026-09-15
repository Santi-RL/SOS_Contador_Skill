from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def lid():
    path = Path(__file__).resolve().parents[1] / "sos-contador-api/scripts/development/reconcile_lid_txt.py"
    spec = importlib.util.spec_from_file_location("lid_diagnostic_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    row = dict(tipo_documento="F", letra="A", punto_venta="1", numero="1",
               cuit_emisor="30000000000", fecha="2026-01-01", total="121.00",
               gravado_21="100.00", iva_21="21.00", gravado_10_5="0", iva_10_5="0",
               gravado_27="0", iva_27="0", gravado_0="0", iva_0="0", exento="0",
               no_gravado="0", otros_impuestos="0")
    cbte = list("0" * 325)
    for start, end, text in [(0, 8, "20260101"), (8, 11, "001"), (11, 16, "00001"),
                             (16, 36, f"{1:020d}"), (54, 74, f"{30000000000:020d}"),
                             (104, 119, f"{12100:015d}"), (237, 238, "1"), (239, 254, f"{2100:015d}")]:
        cbte[start:end] = text
    ali = "00100001" + f"{1:020d}" + "80" + f"{30000000000:020d}" + f"{10000:015d}" + "0005" + f"{2100:015d}"
    paths = [tmp_path / name for name in ("demo.csv", "cbte.txt", "ali.txt")]
    with paths[0].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    paths[1].write_text("".join(cbte) + "\n", encoding="utf-8")
    paths[2].write_text(ali + "\n", encoding="utf-8")
    return paths


def args(paths):
    return ["--work-mode", "development", "--csv", str(paths[0]), "--cbte", str(paths[1]), "--alicuotas", str(paths[2])]


def test_diagnosis_leaves_inputs_and_directory_unchanged(lid, inputs, capsys):
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    assert lid.main(args(inputs)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["comprobantes"] == 1 and report["con_discrepancias"] == 0
    assert report["solo_lectura"] and not report["validacion_fiscal"]
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs[0].parent.iterdir()}


def test_residual_is_reported_without_adjustment(lid, inputs, capsys):
    inputs[0].write_text(inputs[0].read_text(encoding="utf-8").replace("121.00", "122.00"), encoding="utf-8")
    assert lid.main(args(inputs)) == 1
    doc = json.loads(capsys.readouterr().out)["documentos"][0]
    assert doc["diferencias"] == [{"campo": "importe_total", "csv": "122.00", "txt": "121"}]
    assert "no se absorbe" in doc["advertencias"][0]


def test_duplicate_cbte_is_rejected(lid, inputs, capsys):
    inputs[1].write_text(inputs[1].read_text(encoding="utf-8") * 2, encoding="utf-8")
    assert lid.main(args(inputs)) == 2
    assert "duplicadas" in capsys.readouterr().err


def test_orphan_ali_is_rejected(lid, inputs, capsys):
    line = inputs[2].read_text(encoding="utf-8")
    inputs[2].write_text(line[:8] + f"{2:020d}" + line[28:], encoding="utf-8")
    assert lid.main(args(inputs)) == 2
    assert "sin comprobante" in capsys.readouterr().err


@pytest.mark.parametrize("options", [["--work-mode", "operational"], ["--work-mode", "development", "--cbte-out", "out.txt"]])
def test_no_operational_mode_or_correction_outputs(lid, inputs, options):
    with pytest.raises(SystemExit) as result:
        lid.main(options + args(inputs)[2:])
    assert result.value.code == 2


def test_missing_csv_columns_are_not_silently_zero(lid, inputs, capsys):
    inputs[0].write_text("total\n121.00\n", encoding="utf-8")
    assert lid.main(args(inputs)) == 2
    assert "Faltan columnas" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["NaN", "1.001", "Infinity"])
def test_no_silent_monetary_rounding(lid, value):
    with pytest.raises(ValueError):
        lid.parse_decimal(value)


def test_malformed_txt_money_is_rejected(lid):
    with pytest.raises(ValueError):
        lid.parse_money_field("-00000000001210")
