# Local Document Profiles

Creating, editing or testing extraction rules requires explicit development mode. Operational mode only uses the existing profiles through the CLI; an extraction failure is not permission to design a new profile. Keep company facts and explicit user instructions separate from extraction design.

Local document profiles are optional extraction overrides stored outside the public skill logic.

They describe how to extract a recurring format, not how to account for a taxpayer's business. Keep current company instructions in the separate structure documented in [taxpayer-instructions.md](taxpayer-instructions.md); do not move these runtime profiles or merge their executable extraction rules into that guidance.

Use them when:

- the generic parser is not enough for a recurring document family
- the same work CUIT receives the same PDF or image format repeatedly
- you want faster extraction next time without hardcoding that format into the public repo

## Location

```text
<SOS_CONTADOR_HOME>/local/document_profiles/<cuit_trabajo>/<cuit_contraparte>/<document_kind>/<profile_id>/
  manifest.json
  rules.json
```

When the counterparty CUIT is still unknown, `_unknown` is used in that path segment.

## Matching Order

`cobro draft` follows this order:

1. local profile for the explicit `CUIT de trabajo` and detected `CUIT contraparte`
2. local profile for the explicit `CUIT de trabajo` under `_unknown`
3. generic parser

If no local profile matches, the generic parser remains the fallback.

## Files

`manifest.json`

- metadata and matching hints
- work CUIT
- counterparty CUIT
- document kind
- required text anchors
- optional filename hints

`rules.json`

- declarative regex rules for:
  - `fields`
  - `movimientos`
  - `facturas`
- for retentions without their own captured date, use the document date token `__DOCUMENT_DATE__` instead of a fixed calendar date

## Creating A Starter Profile

From a validated draft:

```powershell
python scripts/sos_contador_api.py --work-mode development cobro profile create --draft-id abc123 --name "Cliente Demo OP PDF"
```

This creates a local starter profile using the confirmed draft as a scaffold.

The generated profile is local-only and can be edited manually if the document family needs tighter rules.

