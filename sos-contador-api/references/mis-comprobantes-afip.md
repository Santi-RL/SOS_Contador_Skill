# Mis Comprobantes AFIP

This guide defines the analysis-first workflow for AFIP exports such as:

- `Mis Comprobantes Recibidos - CUIT <cuit_trabajo>`
- `Mis Comprobantes Emitidos - CUIT <cuit_trabajo>`

The goal is to normalize the spreadsheet, deduplicate against SOS safely, and build future-ready drafts without writing anything until the business defaults are explicit.

## What Row 1 Means

Always inspect row 1 before reading the data rows.

- If row 1 contains `Comprobantes Recibidos`, treat the file as purchases.
- If row 1 contains `Comprobantes Emitidos`, treat the file as sales.
- Extract the `CUIT de trabajo` from the same row.
- If the user also gave an explicit work CUIT and it conflicts with row 1, stop and ask.

Example:

- `Mis Comprobantes Recibidos - CUIT <cuit_trabajo>`
  - operation kind: `compra`
  - work CUIT: `<cuit_trabajo>`

## Expected Header Row

The second row should contain the AFIP columns, including at least:

- `Fecha`
- `Tipo`
- `Punto de Venta`
- `Numero Desde`
- `Numero Hasta`
- `Cod. Autorizacion`
- `Nro. Doc. Emisor`
- `Denominacion Emisor`
- `Nro. Doc. Receptor`
- `Tipo Cambio`
- `Moneda`
- the tax and total columns through `Imp. Total`

If the header is materially different, stop and treat the file as a new format to map explicitly.

## Row Validation

Every row must pass these checks before dedupe or draft generation:

1. `Numero Desde` and `Numero Hasta` must both exist.
2. `Numero Desde` and `Numero Hasta` must be equal.
3. `Fecha` must parse cleanly.
4. `Tipo` must map to a known document rule.
5. `Imp. Total` must parse cleanly.

If `Numero Desde != Numero Hasta`, mark the row as `verificar` and never auto-create it.

## Counterparty Side

For `Comprobantes Recibidos`:

- `Nro. Doc. Emisor` is the provider CUIT.
- `Denominacion Emisor` is the provider name.
- `Nro. Doc. Receptor` should match the work CUIT from row 1.

For `Comprobantes Emitidos`:

- invert the business meaning accordingly
- the work CUIT is still row 1
- the counterparty is the receptor side

## Document Identity

Normalize the visible identity from:

- `Tipo`
- `Punto de Venta`
- `Numero Desde`

Example:

- `Tipo = 1 - Factura A`
- `Punto de Venta = 5`
- `Numero Desde = 157`

Normalized identity:

- visible: `A 00005-00000157`
- machine-friendly: `A-0005-00000157`

Do not use `Numero Hasta` for identity after the equality check; it is validation-only.

## Observed Type Mapping

These mappings were observed against real SOS purchase records for AFIP imports. Extend the table only after validating the new type against a real detail payload.

| AFIP `Tipo` | `fcncnd` | `Letra` | `tipocomprobante` | Importe operativo en SOS | Notes |
| --- | --- | --- | --- | --- | --- |
| `1 - Factura A` | `F` | `A` | `1` | `+1` | Standard invoice |
| `81 - Tique Factura A` | `F` | `A` | `1` | `+1` | Observed to persist like `Factura A` in SOS |
| `201 - Factura de Crédito Electrónica MiPyMEs (FCE) A` | `F` | `A` | `201` | `+1` | Distinct fiscal subtype; do not normalize it to Factura A `1/001` merely because the letter is A |
| `11 - Factura C` | `F` | `C` | `11` | `+1` | No VAT buckets, usually non-taxed |
| `3 - Nota de Credito A` | `C` | `A` | `3` | `+1` | Keep amounts positive in SOS purchases; the document nature stays identified by `fcncnd=C` and `tipocomprobante=3` |

If the file contains an unknown type, mark the row as `verificar` and do not create it automatically.

`Letra=A` and `fcncnd=F` do not distinguish `001` from `201`: the source type code and the original must do so. After loading or auditing a purchase, compare the original code, `compra.get.cabecera.tipocomprobante` and `libroiva.compras.codigocomprobanteafip`. Do not describe `201` as an internal SOS code. If the original and Libro IVA both indicate `001` but the detail returns `201`, preserve the document as a standard invoice for reporting, record the header discrepancy and follow [capabilities-and-verification.md](capabilities-and-verification.md); do not re-save the entire purchase solely to normalize a limited field.

## Amount Normalization

Preserve the AFIP tax buckets losslessly in the analysis draft:

- `Neto Grav. IVA 0%`
- `IVA 2,5%`
- `Neto Grav. IVA 2,5%`
- `IVA 5%`
- `Neto Grav. IVA 5%`
- `IVA 10,5%`
- `Neto Grav. IVA 10,5%`
- `IVA 21%`
- `Neto Grav. IVA 21%`
- `IVA 27%`
- `Neto Grav. IVA 27%`
- `Neto No Gravado`
- `Op. Exentas`
- `Otros Tributos`
- `Total IVA`
- `Imp. Total`

For purchase workflows in this workspace, keep the amount fields positive before dedupe, preview, and create:

- invoices and debit notes stay positive
- credit notes also stay positive

Represent the document nature with `fcncnd` / `tipocomprobante`, not by negating the total or tax buckets.

## Safe Deduplication

This step must be exhaustive. The skill must be sure the row is not already loaded before preparing it for mutation.

Recommended source for purchase dedupe:

- exact-range read through the authenticated web-session listing/export for `idtipo_operacion=4`
- use the file's minimum and maximum `Fecha` as the search range
- exclude annulled purchases from the active dedupe universe unless the user explicitly asked to inspect annulled records
  - markers observed in this workspace: `cancelado=1`, non-empty `fechabaja`, or CSV/export placement under `ANULADOS`

Why:

- the public `compra/listado/:periodo` endpoint is useful for reads
- but exact-range dedupe for a spreadsheet batch is safer when it uses the same internal listing/export that the SOS UI exposes for purchases

Deduplication order:

1. Match by `CAE` when the spreadsheet row has it and SOS also exposes it.
2. If `CAE` is missing, use:
   - counterparty CUIT
   - `Fecha`
   - `Letra`
   - `Punto de Venta`
   - `Numero Desde`
   - total operativo en SOS
   - `fcncnd`
3. If more than one SOS record matches the fallback key, load `compra/detalle/:id` for those candidates and compare:
   - `tipocomprobante`
   - `fcncnd`
   - `puntoventa`
   - `numero`
   - `cae`
   - summarized tax buckets
4. If the match is still ambiguous, mark the row as `verificar`.

Origins like `MC Mis Comprobantes AutoImpo` are informative only. A row is a duplicate even if the existing SOS record came from another origin.

## Draft Statuses

Each normalized row should end in exactly one status:

- `ya_cargado`
- `pendiente`
- `verificar`

Suggested user-facing output tables:

- already loaded
- pending
- verify

## Counterparty Resolution

Resolve the counterparty against SOS by CUIT first.

For purchases:

- look up the provider with `cliente/listado` using `proveedor=true`
- use the CUIT as the primary identity
- use the denomination only as a support field

If the CUIT does not exist in SOS, keep the row as `pendiente` or `verificar` depending on the intended future mutation policy, but do not guess an `idclipro`.

Validated API fallback for this workspace:

- if the provider is missing, it can be created first through `POST /cliente`
- the live API requires `cuit`, `clipro`, `idprovincia`, and `idtipocondicioniva`
- for this file family, the practical default used in real imports was:
  - `idtipocondicioniva = 1` for `Factura A` / `Tique Factura A`
  - `idtipocondicioniva = 3` for `Factura C`

## Accounting Defaults

This file family still does not include a reliable semantic expense account, but the public API proved to accept purchase creates without `idcuenta` when the rest of the payload follows the documented `compra/0` shape.

Current temporary policy for this workspace:

1. omit `idcuenta` for AFIP purchase imports unless the user explicitly asks for account mapping
2. keep `idcentrocosto = General` only when that default is confirmed for the work CUIT
3. derive `idprovinciaiibb` from the resolved counterparty province when the mapping is unique
4. keep account-mapping as a future optimization layer, not a blocker for import

Observed side effect in real tests:

- when `idcuenta` is omitted, SOS can assign a default account automatically
- in the validated test for `<cuit_trabajo>`, the created purchase landed in `Ventas Generales`

So the rule is:

- omit `idcuenta` when speed is preferred
- send `idcuenta` only when the user wants strict accounting classification from the start

## Normalized Draft Shape

The analysis draft should preserve enough data to create later without reparsing the spreadsheet.

Suggested shape:

```json
{
  "source_row": 3,
  "operation_kind": "compra",
  "status": "pendiente",
  "work_cuit": "<cuit_trabajo>",
  "counterparty": {
    "idclipro": "58984230",
    "cuit": "<cuit_emisor>",
    "nombre": "Emisor Demo S.R.L."
  },
  "document": {
    "fecha": "2026-02-01",
    "fcncnd": "F",
    "letra": "A",
    "tipocomprobante": 1,
    "puntoventa": 5,
    "numero": 157,
    "cae": "<cae>",
    "moneda": "ARS",
    "tipo_cambio": "1"
  },
  "amounts": {
    "neto_21": "1136242.00",
    "iva_21": "238610.82",
    "otros_tributos": "0.00",
    "total_operativo": "1374852.82"
  },
  "accounting_defaults": {
    "idcuenta": null,
    "idcentrocosto": null,
    "idprovinciaiibb": 19
  }
}
```

The future create wrapper should reuse this normalized draft and must not reparse the original file.

## Validated Purchase Create Shape

For the current workspace, the following public API pattern is validated for purchases:

- method: `PUT`
- path: `compra/0`
- auth: `jwtc`

Minimal validated body pattern:

```json
{
  "fecha": "2026-02-18",
  "idclipro": 59650537,
  "cuitclipro": "<cuit_proveedor>",
  "fcncnd": "F",
  "letra": "A",
  "puntoventa": 4,
  "numero": 1139,
  "numerohasta": 1139,
  "obtienecae": false,
  "fechaiva": "2026-02-18",
  "idprovinciaiibb": 19,
  "idcentrocosto": <id_centro_costo>,
  "memo": "CAE: <cae> - ",
  "referencia": "",
  "descuento": 0,
  "uniqueid": "uuid-v4",
  "controlainconsistencia": 0,
  "imputaciones": [
    {
      "imputa": [
        { "i": "neto", "a": 21.0, "v": 1200000.0 }
      ]
    }
  ],
  "productos": []
}
```

Notes from real tests:

- using the wrong legacy shape can fail with `TypeError: Cannot read properties of undefined (reading 'split')`
- adding `idcuenta` is accepted, but it is not required for the create to succeed
- when `idcuenta` is omitted, SOS may assign a default account automatically
- `memo` persists
- the structured `CAE` field did not persist in the validated tests even though the `memo` kept the CAE text

## Mutation Boundary

This guide is intentionally analysis-first.

For this workflow:

- parse
- validate
- dedupe
- resolve counterparty
- build drafts
- show tables

Never use this workflow to annul or replace an existing purchase unless the user explicitly asked for that cancellation path and the exact mechanism was validated first.

Only after that, and only when the mutation path has been explicitly validated for the workspace, should the skill create the pending rows.

## Local CLI Workflow

The workspace now includes a dedicated helper for this file family:

```powershell
python scripts/sos_contador_api.py afip draft --source "C:\ruta\Mis Comprobantes Recibidos - CUIT <cuit_trabajo>.xlsx"
python scripts/sos_contador_api.py afip import --source "C:\ruta\Mis Comprobantes Recibidos - CUIT <cuit_trabajo>.xlsx" --dry-run
python scripts/sos_contador_api.py afip import --source "C:\ruta\Mis Comprobantes Recibidos - CUIT <cuit_trabajo>.xlsx" --confirm
```

Observed behavior of that helper in this workspace:

- row 1 drives both operation kind and work CUIT
- `afip draft` saves a reusable draft under `<SOS_CONTADOR_HOME>/.draft_cache/`
- `afip import` rebuilds the draft, blocks on `--confirm`, and only creates rows that still remain `pendiente`
- if the spreadsheet total does not match the visible bucket sum, the helper normalizes the residual into:
  - `nogravado` for `Factura C`
  - `percepcionotra` for purchase invoices and tickets




