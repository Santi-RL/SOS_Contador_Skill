# Cobro Create And Associate

This is the recommended request contract for production-like receipt operations.

## Goal

Use one explicit JSON shape so the assistant can:

- validate the request before attempting any mutation
- separate `cuit_trabajo` from `cliente.cuit` without ambiguity
- detect missing required fields early
- stop and ask before doing anything risky or unclear

## Required vs Optional

Top level:

- Required: `contexto.cuit_trabajo.cuit`
- Required: `operacion.tipo`
- Required: `operacion.fecha`
- Required: `operacion.cliente`
- Required: `operacion.recibo.movimientos`
- Required only for `cobro_create_and_associate`: `operacion.asociacion.facturas`

Client identity:

- Required: one of `operacion.cliente.idclipro`, `operacion.cliente.nombre`, or `operacion.cliente.cuit`
- Recommended: provide both `nombre` and `cuit` when available

Receipt:

- Required for every movement:
  - `simple`: `cuenta_id`, `monto`
  - `cheque`: `cuenta_id`, `banco_id`, `fecha`, `numero`, `monto`
  - `retencion`: `cuenta_id`, `fecha`, `regimen`, `monto`
- Optional: `comentarios`, `memo`, `referencia`, `centro_costo`, `numero_recibo`, `total_esperado`

Association:

- Required: at least one invoice
- Required per invoice: `id` or `comprobante`
- Recommended: include `fecha` and `total` for safer validation

## Mandatory Validation Rules

Before any write, the assistant should stop and ask if any of these is missing or ambiguous:

1. The work CUIT is not explicit.
2. The work CUIT conflicts with the name, alias, or the active workspace context.
3. The client cannot be resolved uniquely.
4. The receipt date is missing.
5. A movement is missing a required field for its type.
6. The invoice list is empty for an association request.
7. `recibo.total_esperado` does not match the sum of movements.
8. `asociacion.exigir_cuadre_total = true` and the receipt total does not match the sum of the invoices.

## Practical Rule About CUITs

`contexto.cuit_trabajo.cuit` is the CUIT where the mutation will be written.

It is never the same concept as:

- `operacion.cliente.cuit`
- `operacion.proveedor.cuit`
- any CUIT visible inside the target comprobante

If the user says something informal such as `empresa demo`, that can be used only as a hint.
For mutations, the assistant should still confirm the intended `cuit_trabajo` whenever there is any doubt.

## Recommended Usage

- For chat requests in natural language, the assistant can internally map the message into this JSON contract.
- If a required field cannot be inferred safely, the assistant should ask only for the missing field.
- For production, prefer sending the request already structured in this JSON shape.

