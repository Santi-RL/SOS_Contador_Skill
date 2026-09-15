#!/usr/bin/env python3
"""Diagnóstico local de desarrollo; no genera TXT ni modifica fuentes o SOS."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

CBTE_LEN = 325


ALI_LEN = 84


TYPE_CATEGORY_BY_CODE = {
    "001": ("F", "A"),
    "003": ("C", "A"),
    "011": ("F", "C"),
    "081": ("F", "A"),
}


VAT_BUCKETS = (
    ("gravado_0", "iva_0", "0003"),
    ("gravado_10_5", "iva_10_5", "0004"),
    ("gravado_21", "iva_21", "0005"),
    ("gravado_27", "iva_27", "0006"),
)


Q2 = Decimal("0.01")


ZERO = Decimal("0.00")


def parse_decimal(raw: str | None) -> Decimal:
    text = (raw or "").strip().replace(",", ".")
    value = Decimal(text) if text else ZERO
    if not value.is_finite() or value != quantize_money(value):
        raise ValueError("Importe no finito o con más de dos decimales")
    return quantize_money(value)


def parse_identifier(raw: str | None, width: int) -> int:
    if not re.fullmatch(r"[0-9]{1," + str(width) + "}", (raw or "").strip()):
        raise ValueError("Identificador vacío, no entero o demasiado largo")
    return int(raw)


def normalize_cuit(raw: str) -> str:
    digits = raw.strip().replace("-", "").replace(" ", "")
    if len(digits) == 20 and digits.startswith("0" * 9):
        digits = digits[9:]
    if not re.fullmatch(r"[0-9]{11}", digits):
        raise ValueError("CUIT con formato no soportado")
    return digits


def parse_money_field(raw: str) -> Decimal:
    if not re.fullmatch(r"[0-9]{15}", raw):
        raise ValueError("Campo monetario TXT inválido; se esperan 15 dígitos")
    return Decimal(int(raw)) / Decimal("100")


@dataclass
class CsvRow:
    row_number: int
    key: tuple[str, str, int, int, str]
    fecha: str
    tipo_documento: str
    letra: str
    punto_venta: int
    numero: int
    proveedor: str
    cuit: str
    values: dict[str, Decimal]
    total: Decimal


@dataclass
class CbteRecord:
    index: int
    raw: str
    tipo_code: str
    point_of_sale: int
    number: int
    cuit: str
    key: tuple[str, str, int, int, str]
    current_values: dict[str, Decimal]
    current_cant_alicuotas: int
    current_cod_operacion: str


@dataclass
class AliRecord:
    index: int
    raw: str
    tipo_code: str
    point_of_sale: int
    number: int
    cuit: str
    key: tuple[str, str, int, int, str]
    current_neto: Decimal
    current_code: str
    current_iva: Decimal


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Q2, rounding=ROUND_HALF_UP)


def parse_csv_rows(path: Path) -> list[CsvRow]:
    rows: list[CsvRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"tipo_documento", "letra", "punto_venta", "numero", "cuit_emisor", "fecha", "total", "exento", "no_gravado", "otros_impuestos"}
        required.update(name for net, vat, _ in VAT_BUCKETS for name in (net, vat))
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Faltan columnas CSV: {sorted(missing)}")
        for idx, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Fila CSV {idx} con columnas sobrantes")
            tipo_documento = (row.get("tipo_documento") or "").strip()
            letra = (row.get("letra") or "").strip()
            point_of_sale = parse_identifier(row.get("punto_venta"), 5)
            number = parse_identifier(row.get("numero"), 20)
            cuit = normalize_cuit(row.get("cuit_emisor") or "")
            values = {
                "gravado_21": parse_decimal(row.get("gravado_21")),
                "iva_21": parse_decimal(row.get("iva_21")),
                "gravado_10_5": parse_decimal(row.get("gravado_10_5")),
                "iva_10_5": parse_decimal(row.get("iva_10_5")),
                "gravado_27": parse_decimal(row.get("gravado_27")),
                "iva_27": parse_decimal(row.get("iva_27")),
                "gravado_0": parse_decimal(row.get("gravado_0")),
                "iva_0": parse_decimal(row.get("iva_0")),
                "exento": parse_decimal(row.get("exento")),
                "no_gravado": parse_decimal(row.get("no_gravado")),
                "otros_impuestos": parse_decimal(row.get("otros_impuestos")),
            }
            rows.append(
                CsvRow(
                    row_number=idx,
                    key=(tipo_documento, letra, point_of_sale, number, cuit),
                    fecha=(row.get("fecha") or "").replace("-", ""),
                    tipo_documento=tipo_documento,
                    letra=letra,
                    punto_venta=point_of_sale,
                    numero=number,
                    proveedor=(row.get("proveedor") or "").strip(),
                    cuit=cuit,
                    values=values,
                    total=parse_decimal(row.get("total")),
                )
            )
    return rows


def parse_cbte_records(path: Path) -> list[CbteRecord]:
    records: list[CbteRecord] = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if len(raw) != CBTE_LEN:
            raise ValueError(f"Línea {index} de comprobantes con longitud inválida: {len(raw)}")
        tipo_code = raw[8:11]
        category = TYPE_CATEGORY_BY_CODE.get(tipo_code)
        if category is None:
            raise ValueError(f"Código de tipo no soportado en línea {index}: {tipo_code}")
        point_of_sale = int(raw[11:16])
        number = int(raw[16:36])
        cuit = normalize_cuit(raw[54:74])
        current_values = {
            "importe_total": parse_money_field(raw[104:119]),
            "no_gravado": parse_money_field(raw[119:134]),
            "exento": parse_money_field(raw[134:149]),
            "perc_iva": parse_money_field(raw[149:164]),
            "perc_otros_nac": parse_money_field(raw[164:179]),
            "perc_iibb": parse_money_field(raw[179:194]),
            "perc_muni": parse_money_field(raw[194:209]),
            "imp_internos": parse_money_field(raw[209:224]),
            "credito_fiscal": parse_money_field(raw[239:254]),
            "otros_tributos": parse_money_field(raw[254:269]),
        }
        records.append(
            CbteRecord(
                index=index,
                raw=raw,
                tipo_code=tipo_code,
                point_of_sale=point_of_sale,
                number=number,
                cuit=cuit,
                key=(category[0], category[1], point_of_sale, number, cuit),
                current_values=current_values,
                current_cant_alicuotas=int(raw[237:238]),
                current_cod_operacion=raw[238:239],
            )
        )
    return records


def parse_ali_records(path: Path) -> list[AliRecord]:
    records: list[AliRecord] = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if len(raw) != ALI_LEN:
            raise ValueError(f"Línea {index} de alicuotas con longitud inválida: {len(raw)}")
        tipo_code = raw[0:3]
        category = TYPE_CATEGORY_BY_CODE.get(tipo_code)
        if category is None:
            raise ValueError(f"Código de tipo no soportado en alicuotas línea {index}: {tipo_code}")
        point_of_sale = int(raw[3:8])
        number = int(raw[8:28])
        cuit = normalize_cuit(raw[30:50])
        records.append(
            AliRecord(
                index=index,
                raw=raw,
                tipo_code=tipo_code,
                point_of_sale=point_of_sale,
                number=number,
                cuit=cuit,
                key=(category[0], category[1], point_of_sale, number, cuit),
                current_neto=parse_money_field(raw[50:65]),
                current_code=raw[65:69],
                current_iva=parse_money_field(raw[69:84]),
            )
        )
    return records


def index_unique_csv(rows: Iterable[CsvRow]) -> dict[tuple[str, str, int, int, str], CsvRow]:
    indexed: dict[tuple[str, str, int, int, str], list[CsvRow]] = defaultdict(list)
    for row in rows:
        indexed[row.key].append(row)
    duplicates = {key: values for key, values in indexed.items() if len(values) > 1}
    if duplicates:
        details = ", ".join(f"{key} x{len(values)}" for key, values in duplicates.items())
        raise ValueError(f"Claves duplicadas en CSV: {details}")
    return {key: values[0] for key, values in indexed.items()}


def group_ali_by_key(records: Iterable[AliRecord]) -> dict[tuple[str, str, int, int, str], list[AliRecord]]:
    grouped: dict[tuple[str, str, int, int, str], list[AliRecord]] = defaultdict(list)
    for record in records:
        grouped[record.key].append(record)
    return grouped


def diagnose(csv_rows: list[CsvRow], cbtes: list[CbteRecord],
             alis: list[AliRecord]) -> dict:
    """Comparar importes sin inventar tributos ni absorber diferencias."""
    csv_index = index_unique_csv(csv_rows)
    cbte_index = {item.key: item for item in cbtes}
    if len(cbte_index) != len(cbtes):
        raise ValueError("Claves duplicadas en CBTE")
    if not cbtes or set(csv_index) != set(cbte_index):
        raise ValueError("CSV y CBTE deben tener el mismo conjunto no vacío de comprobantes")
    groups = group_ali_by_key(alis)
    if set(groups) - set(cbte_index):
        raise ValueError("Hay alícuotas sin comprobante CBTE")
    documents = []
    for key, cbte in cbte_index.items():
        row = csv_index[key]
        group = groups.get(key, [])
        if any(ali.tipo_code != cbte.tipo_code for ali in group):
            raise ValueError("CBTE y ALICUOTAS difieren en el código fiscal")
        if len({ali.current_code for ali in group}) != len(group):
            raise ValueError("Alícuotas repetidas; este diagnóstico no agrega renglones")
        if any(ali.current_code not in {code for _, _, code in VAT_BUCKETS} for ali in group):
            raise ValueError("Alícuota fuera del conjunto soportado")
        differences = []

        def compare(field, csv_value, txt_value):
            if csv_value != txt_value:
                differences.append({"campo": field, "csv": str(csv_value), "txt": str(txt_value)})

        # Las NC se comparan por magnitud, sin modificar su signo en las fuentes.
        values = {name: abs(value) if row.tipo_documento == "C" else value
                  for name, value in row.values.items()}
        total = abs(row.total) if row.tipo_documento == "C" else row.total
        alerts = []
        if total < ZERO or any(value < ZERO for value in values.values()):
            alerts.append("Importes negativos fuera de NC: revisar el original; no se redistribuyen")
        residual = total - sum(values.values(), ZERO)
        if residual:
            alerts.append(f"Diferencia entre total CSV y sus componentes: {residual}; no se absorbe")
        compare("fecha", row.fecha, cbte.raw[:8])
        compare("importe_total", total, cbte.current_values["importe_total"])
        for name in ("no_gravado", "exento"):
            compare(name, values[name], cbte.current_values[name])
        compare("credito_fiscal", sum((values[vat] for _, vat, _ in VAT_BUCKETS), ZERO),
                cbte.current_values["credito_fiscal"])
        tax_fields = ("perc_iva", "perc_otros_nac", "perc_iibb", "perc_muni", "imp_internos", "otros_tributos")
        compare("otros_impuestos_agregados", values["otros_impuestos"],
                sum((cbte.current_values[name] for name in tax_fields), ZERO))
        if cbte.current_cant_alicuotas != len(group):
            alerts.append("Cantidad declarada de alícuotas distinta de las líneas ALICUOTAS")
        by_code = {ali.current_code: ali for ali in group}
        for net, vat, code in VAT_BUCKETS:
            ali = by_code.get(code)
            if ali is None and (values[net] or values[vat]):
                alerts.append(f"Falta la línea de alícuota {code}")
            compare(net, values[net], ali.current_neto if ali else ZERO)
            compare(vat, values[vat], ali.current_iva if ali else ZERO)
        documents.append({"linea_cbte": cbte.index, "clave": list(key),
                          "codigo_fiscal": cbte.tipo_code, "diferencias": differences,
                          "advertencias": alerts})
    return {"modo": "development", "solo_lectura": True, "validacion_fiscal": False,
            "comprobantes": len(documents),
            "con_discrepancias": sum(bool(d["diferencias"] or d["advertencias"]) for d in documents),
            "limites": ["Comparación parcial de importes; no valida tratamiento fiscal ni integridad completa del formato",
                        "Otros impuestos se comparan agregados; no valida su distribución por tributo o jurisdicción",
                        "No genera correcciones ni archivos aptos para presentar o importar"],
            "documentos": documents}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-mode", required=True, choices=["development"])
    parser.add_argument("--csv", required=True)
    parser.add_argument("--cbte", required=True)
    parser.add_argument("--alicuotas", required=True)
    args = parser.parse_args(argv)
    try:
        report = diagnose(parse_csv_rows(Path(args.csv)), parse_cbte_records(Path(args.cbte)),
                          parse_ali_records(Path(args.alicuotas)))
    except (OSError, ValueError, InvalidOperation, csv.Error) as exc:
        print(f"Diagnóstico detenido: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["con_discrepancias"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
