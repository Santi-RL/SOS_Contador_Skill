# Endpoints V1

Historical technical reference for development. Operational agents use [operating-recipes.md](operating-recipes.md), not these low-level examples. A published endpoint or observed UI result does not enable a new variant. Raw `call` and generic writes require an explicit development/controlled-validation mode.

Source references:

- [SOS Contador API - Postman Documenter](https://documenter.getpostman.com/view/1566360/SWTD6vnC?version=latest)
- [SOS Contador tiene API](https://ayuda.sos-contador.com.ar/mas-funcionalidades-de-sos/SOS-Contador-tiene-API)
- [sabado/sos-contador-api](https://github.com/sabado/sos-contador-api) as a community reference for sales and sales-point workflows
- [abustosp/sos-api](https://github.com/abustosp/sos-api) as a community reference for multi-CUIT login flows and batch IVA workflows

## Wrapped By The CLI

### Auth

- `POST /login`
- `GET /cuit/credentials/:idcuit`

Real response note:

- both endpoints return the token under `jwt`
- `/login` also exposes the accessible `cuits` list, which the CLI now surfaces through `auth list-cuits`
- `auth resolve-cuit --name ...` is a local helper built on top of that list plus private aliases and a local cache
- `auth info`, `auth list-cuits`, and `auth resolve-cuit` are discovery-only and can run without a selected work CUIT
- every business helper must receive the work target explicitly with `--cuit-trabajo`, `--cuit-trabajo-id`, or `--cuit-trabajo-nombre`

### Cliente

- `GET /cliente/listado`
- `POST /cliente`
- `PUT /cliente/:id`
- `DELETE /cliente/:id`

Observed minimal create shape in real tests (not a safe partial-update body):

```json
{
  "cuit": "<cuit_cliente>",
  "clipro": "Cliente Demo S.A.",
  "idprovincia": 19,
  "idtipocondicioniva": 5,
  "email": "usuario@example.com"
}
```

Field-name note:

- the documented and validated key is `idtipocondicioniva`
- attempts with `idcondicioniva`, `idtipo_condicioniva`, or `idtipo_condicioniva` were rejected by the live API for create

`PUT /cliente/:id` can replace omitted fields with empty/default values, including the supplier role. The list response does not expose the whole record. Read [capabilities-and-verification.md](capabilities-and-verification.md) before updating an existing third party; do not reuse this minimal create example as a PATCH.

### Producto

- `GET /producto/listado`
- `POST /producto`
- `PUT /producto/:id`

### Cobro

- `GET /cobro/listado/:periodo`
- `GET /cobro/detalle/:id`
- `PUT /cobro/:id` for create when `:id` is omitted

Required shape for create:

```json
{
  "fecha": "2021-01-01",
  "idclipro": "1",
  "idcuenta": "1",
  "idprovinciaiibb": "1",
  "idcentrocosto": "1",
  "memo": "",
  "referencia": "1234",
  "imputaciones": [
    {
      "fv": "100.00",
      "cuid": "1"
    }
  ]
}
```

Public API limit observed in production:

- `cobro/listado/:periodo` accepts relative periods such as `hoy`, `ayer`, `semana`, `mes`, `mes_anterior`
- arbitrary date ranges are not exposed by the public API
- the public API create shape does not expose cheque detail or retenciones sufridas detail

### Pago

- `GET /pago/listado/:periodo`
- `GET /pago/detalle/:id`
- `PUT /pago/:id` for create when `:id` is omitted

Payload shape matches the documented cobro example, replacing the endpoint only.

### Compra

Observed in real reads for work-CUIT-scoped purchases:

- `GET /compra/listado/:periodo`
- `GET /compra/detalle/:id`

Observed behavior:

- `compra/listado/:periodo` returns purchase summaries such as nested `clipro`, `factura`, `fecha`, `montototal`, and `cae`
- `compra/detalle/:id` returns a `cabecera` plus `imputaciones`
- `PUT /compra/:id` is usable for create with `:id = 0` when the payload follows the documented purchase shape
- `POST /compra/consulta` is usable for exact period reads when the request body uses ISO dates `YYYY-MM-DD`
- the purchase detail `cabecera` exposes the fields that matter for AFIP-import normalization:
  - `fcncnd`
  - `letra`
  - `puntoventa`
  - `numero`
  - `tipocomprobante`
  - `cae`
- observed mappings from real AFIP imports:
  - `Factura A` => `fcncnd=F`, `tipocomprobante=1`
  - `Tique Factura A` => `fcncnd=F`, `tipocomprobante=1`
  - `Factura C` => `fcncnd=F`, `tipocomprobante=11`
  - `Nota de Credito A` => `fcncnd=C`, `tipocomprobante=3`, keep purchase amounts positive in SOS and distinguish the note through the document type fields
- observed create behavior in real tests:
  - the documented `compra/0` payload with `uniqueid`, `controlainconsistencia`, and `imputaciones[].imputa[]` works
  - omitting `idcuenta` still allows the create to succeed
  - when `idcuenta` is omitted, SOS may assign a default account automatically
  - sending the older cobro-like `imputaciones` shape fails with `TypeError: Cannot read properties of undefined (reading 'split')`
  - `memo` persisted but the structured `CAE` field remained empty in the validated tests
  - sending `fecha` as `DD/MM/YYYY` can create the purchase with the creation timestamp instead of the intended invoice date
  - sending `fecha` and `fechaiva` as ISO `YYYY-MM-DD` positioned the purchase correctly in the target month
  - after create, `cabecera.fecha` was the operative stored date used by `compra/consulta`
  - `fechaiva` and `fechacbte` could remain `null` in `compra/detalle/:id` even when the purchase was correctly queryable by month

Current scope limit:

- `compra draft` and `compra create` wrap the analysis-first document workflow, freeze the approved payload and verify the resulting purchase
- use the cataloged `compra.save` operation with `api describe` and `api invoke` only for low-level or non-document cases; use `--param id=0` for create and never guess from `cobro` / `pago` symmetry
- for the full analysis-first workflow, read [mis-comprobantes-afip.md](mis-comprobantes-afip.md)
- for purchase folders with one invoice PDF per file, also read [compra-from-pdf-folder.md](compra-from-pdf-folder.md)

### Venta

- `GET /venta/listado/:modo/:periodo/:cae`
- `GET /venta/detalle/:id`
- `GET /venta/pdf/:id`
- `POST /venta/consulta`
- `PUT /venta/archivar/:id`
- `PUT /venta/:id` for create or update; omit the optional ID when creating
- `DELETE /venta/:id`, kept blocked by the CLI's comprobante safety policy

CLI helpers:

- `venta list` keeps the explicit `--modo` filter and defaults to `facturas`
- `venta list-all` is a convenience helper that calls `venta/listado/todas/...` for a broader commercial listing
- `venta pdf` uses the public API `GET /venta/pdf/:id` first
  - when the user gives a visible invoice number instead of an `id`, resolve the `id` first with `venta list-all` over the narrowest known date range and match the returned `factura` field
  - normalize visible invoice numbers to the returned SOS format when matching, for example `A-00001-00000001` corresponds to `FA-0001-00000001`
  - `venta list-all` can return records outside the exact date flags, so still filter the returned rows by invoice number, date, and client when available
  - do not use `venta search --comprobante ...`; that argument is not supported by the current helper
  - if the API path fails, diagnose or repair the API path before using a fallback
  - `web-session` fallback is allowed only with explicit permission and the helper flag `--allow-web-session-fallback`
- `venta create` keeps the validated internal web-session form post for backward compatibility
- `api invoke --operation venta.save` exposes the documented public `PUT /venta/:id?` route
- keep `venta.save` as `documented-unvalidated` until a controlled real write verifies its persisted shape

Local document-ingestion helper:

- `cobro draft` is a local normalization step, not an SOS endpoint
- it reads PDF, image, TXT, CSV, XLSX, or XLS sources
- it caches the normalized draft so `cobro create --draft-id ...` can reuse it without reparsing the source
- it can render the user-facing preview directly with `--preview-format markdown`
- it can infer `cuit_trabajo` from the buyer/receptor section when the document exposes a unique accessible CUIT
- if the document does not identify a unique accessible buyer CUIT, the draft stays incomplete and must ask the user
- before the generic parser it checks private extraction profiles under `<SOS_CONTADOR_HOME>/local/document_profiles/...`
- `cobro profile create` scaffolds a local declarative profile from a validated draft so the same document family can be parsed faster next time

Behavior note for natural-language queries:

- if the user asks for `facturas emitidas`, do not assume that credit notes or debit notes should be excluded when they also exist in the same filtered sales set
- first inspect the broader emitted-sales result for the target period and contribuyente with `venta list-all --cuit-trabajo ...`
- if the period contains only invoices, return them directly
- if the period also contains credit/debit notes, ask whether to show only invoices or include those notes too
- if the user chooses to include them, return one combined table from that same broader result set

Observed minimal web-session body for `venta create`:

```json
{
  "id": "0",
  "fcncnd": "F",
  "idtipo": "2",
  "fecha": "17/03/2026",
  "idclipro": "<id_cliente>",
  "letra": "C",
  "sucursal": "2",
  "numero": "5",
  "numero_hasta": "5",
  "fechaiva": "17/03/2026",
  "fechadesde": "01/03/2026",
  "fechahasta": "31/03/2026",
  "codactividad": "619000",
  "idcuenta": "<id_cuenta>",
  "idprovinciaiibb": "1",
  "idcentrocosto": "<id_centro_costo>",
  "observaciones": "prueba venta e2e 1",
  "moneda": "ARS",
  "tipocambio": "1",
  "nuevocentro": "General",
  "cuentacobropago": "0",
  "obtienecae": "false",
  "imputa": {
    "imputa": []
  },
  "productos": [
    {
      "orden": "0",
      "id": "<id_producto>",
      "u": "7",
      "fc": "1.000",
      "fu": "2800.000",
      "fa": "0.00",
      "fi": "nogravado",
      "cuid": "<id_cuenta>",
      "codact": "619000",
      "idcentro": "<id_centro_costo>"
    }
  ]
}
```

### Punto de venta

- `GET /puntoventa/listado`

## Web-Session Fallbacks

These are internal web endpoints used only when the public API does not cover the capability. Current v1 fallback scope includes cobranza date-range listing, receipt detail fallback, detailed cobro create, receipt association, and sale create.

In this skill, `web-session` means direct HTTP login plus cookies. It does not mean browser automation and it must not trigger a browser automation framework for standard receipt queries.

- `POST /back/login.asp`
- `GET /back/cambiar_cuit.asp?nuevocuit=:idcuit`
- `POST /back/xml.asp` with `object=comprobante_listado`
- `POST /back/xml.asp` with `object=comprobante_historia`
- `POST /back/xml.asp` with `object=comprobante_ultimo_numero`
- `POST /back/xml.asp` with `object=cobropago_compraventa`
- `GET /back/comprobante_listado_xls.asp`
- `POST /back/comprobante_altamodi.asp`
- `POST /back/asociaciones_altamodi.asp`

Current implemented fallback:

- `cobro list-range --cuit-trabajo ... --desde DD/MM/YYYY --hasta DD/MM/YYYY [--cliente-nombre ...] [--cliente-cuit ...] [--recibo ...] [--comprobante ...]`
- `cobro resolve-id --cuit-trabajo ...`
- `cobro get --cuit-trabajo ...` when the public API detail endpoint is broken, or when the user identifies the recibo by visible number and not by internal `id`
- `cobro draft --source ... [--source ...] [--cuit-trabajo ...|--cuit-trabajo-nombre ...]`
- `cobro create --draft-id ... --confirm` after reviewing the preview and reusing the work CUIT already fixed in the draft
- `cobro create --cuit-trabajo ... --movimientos-json ...` for cheques recibidos and retenciones sufridas
- `cobro asociar --cuit-trabajo ... --factura ... [--factura ...]`
- `compra create --draft-id ... --confirm` uses the internal listing with `idtipo_operacion=4` as a complementary status check
- `venta create --cuit-trabajo ... --productos-json ...`

The same internal listing/export endpoints are also usable for purchase status verification by exact date range with `idtipo_operacion=4`.

Observed internal filter used by the web app for cobranza date ranges:

- `idtipo_operacion=12`
- filter on `C.fechaiva` with `gte` / `lte`

Observed internal detail loader used by the web app:

- `object=comprobante_historia`
- `idtipo_operacion=12`
- `idcomprobante=:id`

Observed association flow used by the web app:

- read current state with `object=cobropago_compraventa`, `idclipro`, `idtipo_operacion=12`, and `items=[idrecibo]`
- save the final grouping with `POST /back/asociaciones_altamodi.asp`
- payload shape:

```json
{
  "idclipro": "<id_cliente>",
  "a": [
    {
      "c": ["<id_comprobante_asociado_1>", "<id_comprobante_asociado_2>", "<id_comprobante_asociado_3>"]
    }
  ],
  "d": ["<id_comprobante_suelto>"]
}
```

`a` contains the groups that must remain associated.
`d` contains the comprobantes that must remain sueltos after the rewrite.

Observed plan-de-cuentas IDs that worked in the sandbox `<cuit_cliente>`:

- `<id_cuenta_valores_a_depositar>` = `Valores A Depositar`
- `<id_cuenta_retencion_iva>` = `Retención IVA Sufrida`
- `<id_cuenta>` = `Ventas Generales`
- `<id_cuenta_banco>` = `Banco`
- `<id_centro_costo>` = `General`

Recommended recipes:

- Standard account login for routine tasks:
  - load credentials from `<SOS_CONTADOR_HOME>/.env.local`
  - log in directly with the CLI
  - do not inspect Chrome or browser cookies
- Resolve a contribuyente from informal text:
  - `python scripts/sos_contador_api.py auth resolve-cuit --name "empresa demo"`
- List receipts for a client and month:
  - `python scripts/sos_contador_api.py cobro list-range --cuit-trabajo <cuit_trabajo> --desde 01/11/2025 --hasta 30/11/2025 --cliente-nombre "Cliente Demo S.A."`
- Resolve a visible receipt number to internal ID:
  - `python scripts/sos_contador_api.py cobro resolve-id --cuit-trabajo <cuit_trabajo> --fecha 12/11/2025 --recibo 51 --cliente-nombre "Cliente Demo S.A."`
- Get receipt detail by visible number:
  - `python scripts/sos_contador_api.py cobro get --cuit-trabajo <cuit_trabajo> --recibo 51 --fecha 12/11/2025 --cliente-nombre "Cliente Demo S.A."`

## Useful Auxiliary Reads

These are available through the documented operation catalog even when they do not have dedicated helpers:

- `GET /provincia/listado`
- `GET /cuit/sct`
- `GET /cuentacontable/listado`
- `GET /indiceaniomes/listado`
- `GET /unidad/listado`
- `GET /tipo/listado/:modulo/:busca?`

## Generic Call Examples

```powershell
python scripts/sos_contador_api.py api invoke --operation provincia.list --cuit-trabajo <cuit_trabajo>
python scripts/sos_contador_api.py api invoke --operation cuentacontable.list --cuit-trabajo <cuit_trabajo>
python scripts/sos_contador_api.py api invoke --operation indiceaniomes.list --cuit-trabajo <cuit_trabajo>
python scripts/sos_contador_api.py --work-mode development call --auth-mode jwtc --cuit-trabajo <cuit_trabajo> --method POST --path venta/consulta --query pagina=1 --query registros=50 --body-file .\venta-filtros.json --dry-run
python scripts/sos_contador_api.py --work-mode development call --auth-mode jwtc --cuit-trabajo <cuit_trabajo> --method GET --path cuentacontable/listado --out "$env:SOS_CONTADOR_HOME\local\exports\<cuit_trabajo>\plan_de_cuentas\2026\04\2026-04-10-plan-de-cuentas-<cuit_trabajo>.json"
```

## Mutation Guardrails

For every `POST`, `PUT`, `DELETE`, or `PATCH`:

- resolve the work CUIT first and keep it explicit in the command or the draft
- use `--dry-run` to inspect the business preview and the final request without executing it
- use `--confirm` to execute it
- avoid direct destructive operations unless the user explicitly confirmed them in the conversation
- never treat a normal create/update confirmation as permission to annul a comprobante
- the exact endpoint/body field that annuls a comprobante is not validated in this skill; do not invent it and do not probe it casually
- when reading or verifying comprobantes, treat records with markers such as `cancelado=1`, non-empty `fechabaja`, or CSV/export placement under `ANULADOS` as annulled and exclude them from normal active-record results unless the user explicitly asked for annulled items

## Comprobante Anulacion Safety

This skill must default to non-destructive comprobante handling.

- Never annul purchases, sales, receipts, payments, or similar comprobantes unless the user explicitly asked for that exact cancellation.
- `back/comprobante_altamodi.asp` is a mutating web-session endpoint used by create/update flows. Do not assume it is safe for arbitrary edits and never use it to explore cancellation behavior without explicit user authorization.
- `PUT /compra/0`, `venta create`, `cobro create`, `pago create`, and raw `call` mutations are not allowed to carry guessed cancellation semantics.
- If future work validates the exact cancellation payload, document that payload explicitly before using it in the skill.

## Known Limits

- No helper for undocumented endpoints.
- No auto-resolution for every numeric dependency. In v1, `idcuenta` and `idcentrocosto` should usually be passed explicitly.
- The `abustosp/sos-api` repo suggests IVA batch reads, but it does not document enough of the `iva/listado` path variants to enable a dedicated helper here without first validating them against the real API.
- Internal web endpoints are less stable than the public API and may change without notice.
- The web-session can show intermittent timeouts. The CLI retries only known reads; business writes are sent once. Consult state after an ambiguous write and never retry it automatically.




