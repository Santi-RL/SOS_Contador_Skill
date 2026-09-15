# Cobro From Document

This guide is the human-oriented workflow for creating a receipt from a document without forcing the user to send a full JSON payload.

It is not the default path for every SOS interaction. Use it only for document-driven receipt creation flows. Updates require a separately validated recipe in development.

## Goal

Use natural language plus one or more attached files, while keeping the validation explicit before any write.

Target flow:

1. user asks to create a receipt from a PDF, image, TXT, CSV, XLSX, or XLS
2. assistant groups the attached files by business receipt before drafting
3. assistant runs one `cobro draft --preview-format markdown` per receipt group
4. assistant asks only for real missing fields
5. assistant shows the extracted result in Markdown tables
6. user confirms
7. assistant runs `cobro create --draft-id ... --confirm` for each approved draft
8. if this document family needs a new extraction profile, stop that discovery path and request explicit development mode; operational mode only consumes existing profiles

## When Multiple Files Arrive Together

Do not assume that multiple files belong to the same receipt.

Use multiple `--source` values in one draft only when the files are complementary pieces of one business document, for example:

- front/back scans of the same order
- continuation pages of the same PDF export
- annexes or supporting pages that complete the same receipt

Split the work into separate drafts when the files contain different:

- order numbers
- receipt dates
- invoice references
- totals
- cheque or retention sets

If a preview merges multiple independent orders into one receipt, stop and rerun the workflow with one draft per receipt group before any write.

## Minimum Data Needed

Always explicit:

- `CUIT de trabajo`

Receipt header:

- `Fecha`
- `Cliente` by `idclipro`, `CUIT`, or name

Receipt movements:

- `simple`: `Cuenta destino`, `Monto`
- `cheque`: `Cuenta destino`, `Banco`, `Fecha`, `Número`, `Monto`
- `retencion`: `Cuenta destino`, `Fecha`, `Régimen`, `Monto`

Association, only if requested:

- at least one target invoice by visible `Comprobante` or `venta_id`

Optional:

- `Comentarios`
- `Centro de costo`
- `Número de recibo`
- `Factura fecha`
- `Factura total`

## What The Assistant Must Show Before Writing

### Context

| Campo | Valor |
| --- | --- |
| CUIT de trabajo | ... |
| Contribuyente | ... |
| Cliente | ... |
| CUIT cliente | ... |
| Fecha | ... |
| Centro de costo | ... |
| Comentarios | ... |

### Movimientos

| Tipo | Cuenta destino | Banco/Régimen | Número | Fecha | Monto | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| cheque | Valores a Depositar | GALICIA Y BS AS | 32412952 | 2025-10-28 | 1102000.66 | Inferido |

### Asociación

| Comprobante | Fecha | Total | Estado |
| --- | --- | --- | --- |
| A-0003-00000158 | 2025-08-12 | 6200000.00 | Inferido |

### Totals

- `Total recibo`: ...
- `Total asociación`: ...
- `Diferencia`: ...

## Required Clarifications

The assistant must stop and ask when any of these remains unresolved:

- work CUIT missing or ambiguous
- client unresolved
- document date missing
- a movement has missing required data
- multiple banks/accounts/regimens match the same free text
- receipt total and association total do not match when exact matching is expected

## Standard Follow-Ups

When the work CUIT is missing:

`Necesito que me confirmes el CUIT de trabajo donde se va a cargar el recibo.`

When the client is ambiguous:

`Necesito que me confirmes el cliente del recibo. Puedo buscarlo por CUIT o por nombre exacto.`

When a cheque bank is unresolved:

`Pude extraer el cheque, pero no pude resolver el banco de forma unica. Decime el banco exacto para ese item.`

When a retention regimen is unresolved:

`Pude extraer la retencion, pero me falta el regimen numerico que acepta SOS para ese item.`

## Operational Notes

- `CUIT de trabajo` and `CUIT del cliente/proveedor` are never the same concept.
- `cobro draft` is non-mutating.
- `cobro create --draft-id ...` must reuse the cached draft and must not reparse the source.
- Never annul, cancel, or give baja to an existing receipt as part of this workflow unless the user explicitly asked for that exact cancellation.
- `cobro draft` checks private extraction profiles before the generic parser. The path is `<SOS_CONTADOR_HOME>/local/document_profiles/<cuit_trabajo>/<cuit_contraparte>/<document_kind>/...`.
- Local profiles are intended for per-user optimizations and are ignored by git.
- The public repository should keep only the generic parser; special document families belong in local profiles.
- Multiple `--source` values mean "one receipt across several files", not "batch several independent receipts at once".
- If OCR is required and unavailable locally, stop and ask for a text-readable source or OCR availability.
- After `cobro draft`, the normal path is to validate or ask for missing fields, not to inspect repository code or CLI help.
