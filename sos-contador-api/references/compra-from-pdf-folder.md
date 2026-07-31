# Compra From PDF Or Image

This guide documents the validated workflow for loading purchase invoices from PDFs or images where each source represents one supplier invoice.

Use it when the user says things like:

- "En esta carpeta hay comprobantes de compra pendientes"
- "Cargá esta foto de una factura"
- "Armá los borradores y mostrame qué vas a cargar"
- "Después del OK cargalos"

It is an analysis-first workflow. Do not write anything until the user explicitly approves the draft table.

## Goal

Target flow:

1. resolve the `CUIT de trabajo`
2. inspect the sources and treat each PDF or image as one potential purchase invoice
3. extract the business fields from every file
4. deduplicate against SOS
5. show a compact review table
6. wait for user OK
7. create the pending purchases by API
8. verify each created purchase against SOS using the target period

## What To Extract Per PDF

Minimum normalized fields:

- `Fecha`
- `Letra`
- `Punto de venta`
- `Numero`
- `Proveedor`
- `CUIT proveedor`
- `Neto`
- `IVA`
- `Total`
- `Archivo`

Treat one source as one invoice. Do not merge files unless they are clearly continuation pages or complementary images of the same invoice.

## CUIT Validation Before Supplier Resolution

For every CUIT read from OCR or a low-quality image:

1. normalize it to 11 digits
2. validate the Argentine check digit
3. only then query the supplier master

An invalid OCR candidate is not evidence that the supplier is missing. Do not create a supplier from it.

If the candidate is invalid:

- reread the source at the digit level
- search the master by normalized legal name
- inspect prior purchases for a unique name, address, and document-family match
- accept a corrected CUIT only when the evidence identifies one unique supplier; otherwise ask the user

Surface the correction in the draft so the user can verify it.

## Reusing Historical Purchase Patterns

When the supplier already exists, use `compra.search` and `compra.get` to inspect one to three recent active purchases from the same supplier before choosing accounting defaults.

Reusable fields, when the prior documents are commercially analogous:

- `idcuenta`
- `idcentrocosto`
- `idprovinciaiibb`
- the tax-bucket treatment

Never copy:

- date
- point of sale
- invoice number
- amounts
- CAE
- cancellation or archival state

For fuel tickets, internal fuel taxes and carbon-dioxide tax may be represented as `nogravado` only when a verified analogous purchase for the same supplier uses that treatment. Do not generalize this mapping to unrelated “other taxes.”

## Review Table

Prefer a compact table that fits the app width:

| Fecha | Comp. | Proveedor | Total |
| --- | --- | --- | ---: |
| 03/02/2026 | A 00002-00074746 | CIRUGIA NEDISUR S.R.L | 8.833.000,00 |

Move `CUIT` or `Archivo` to a short supporting list when the full table becomes too wide.

## Deduplication

Before any write, compare every candidate against SOS.

Validated read path:

- `POST /compra/consulta`
- then `GET /compra/detalle/:id` for exact verification when needed

Validated date rule:

- use ISO dates in the body: `YYYY-MM-DD`
- example:

```json
{
  "fecha_desde": "2026-02-01",
  "fecha_hasta": "2026-02-28"
}
```

Do not use `DD/MM/YYYY` in `compra/consulta`. In real tests for this workspace, that returned empty lists even when purchases existed.

The endpoint can return at most 50 rows for a broad range. If a query returns exactly 50 items, treat it as potentially truncated and split the period into quarters or months before concluding that no match exists.

Recommended identity key for one-PDF-per-invoice folders:

- provider CUIT
- invoice date
- `fcncnd`
- `letra`
- point of sale
- number
- `neto_21`
- total

Statuses:

- `ya_cargado`
- `pendiente`
- `verificar`

## Validated Create Shape

Validated write path:

- method: `PUT`
- path: `compra/0`

Validated minimal body pattern for this workflow:

```json
{
  "fecha": "2026-02-03",
  "idclipro": 59650839,
  "cuitclipro": "<cuit_proveedor>",
  "fcncnd": "F",
  "letra": "A",
  "puntoventa": 2,
  "numero": 74746,
  "numerohasta": 74746,
  "obtienecae": false,
  "fechaiva": "2026-02-03",
  "idprovinciaiibb": 19,
  "idcentrocosto": <id_centro_costo>,
  "memo": "",
  "referencia": "EMPRESA DEMO 1 FEBRERO 26.pdf",
  "descuento": 0,
  "uniqueid": "uuid-v4",
  "controlainconsistencia": 0,
  "imputaciones": [
    {
      "imputa": [
        { "i": "neto", "a": 21.0, "v": 7300000.0 }
      ]
    }
  ],
  "productos": []
}
```

Current workspace policy:

- use an exact historical `idcuenta` when an analogous active purchase confirms the intended classification
- otherwise omit `idcuenta` unless the user explicitly wants account mapping
- keep `referencia` with the PDF file name for traceability

## Critical Date Rule

This was the main live issue found in this workflow.

For purchase creates and updates through the public API:

- send `fecha` in ISO format `YYYY-MM-DD`
- send `fechaiva` in ISO format `YYYY-MM-DD`

Do not send purchase dates as `DD/MM/YYYY`.

Observed real behavior when `DD/MM/YYYY` was sent:

- the API created the purchase successfully
- but SOS stored `cabecera.fecha` with the creation timestamp instead of the invoice date
- the purchase then disappeared from `compra/consulta` for the target month

Operational consequence:

- a successful create response is not enough
- always verify the stored date after creation

## Post-Create Verification

After each create:

1. call `GET /compra/detalle/:id`
2. confirm:
   - provider CUIT
   - `letra`
   - point of sale
   - number
   - `neto_21`
   - total
   - stored date
   - account and tax buckets when copied from an analogous purchase
3. call `POST /compra/consulta` for the target ISO date range
4. confirm that the created ID appears in that period listing
5. confirm in the internal listing/export that the purchase is not annulled
   - reject the result if the listing shows `cancelado=1`, non-empty `fechabaja`, or the record under `ANULADOS`

In real tests for this workspace:

- `cabecera.fecha` was the operative date used by `compra/consulta`
- `fechaiva` and `fechacbte` could remain `null` in the detail payload even after the purchase was correctly positioned in the target month

So the practical verification field is:

- `cabecera.fecha`

not:

- `fechaiva`
- `fechacbte`

Some detail responses preserve sub-cent values such as VAT calculated to four decimals. Compare monetary results after rounding to cents, while also confirming that the unrounded components reconcile mathematically.

## Recommended Execution Pattern

1. resolve the work CUIT from alias or explicit CUIT
2. list the PDF folder
3. parse one invoice per PDF
4. build the compact review table
5. wait for explicit user approval
6. create the pending purchases
7. if any purchase was created with a wrong stored date, correct it immediately with `PUT /compra/:id` using the same body but ISO dates
8. re-run the final verification against the target month

Never use this workflow to annul a purchase unless the user explicitly asked for that exact action.

## Current Scope

This workflow is validated operationally for:

- purchase PDFs
- purchase images
- one invoice per file
- standard `Factura A`
- suppliers already present in SOS
- API-first creation and correction

It is not yet wrapped as a dedicated CLI helper. Until then, treat it as a documented manual skill workflow built on top of the same local client and draft cache.


