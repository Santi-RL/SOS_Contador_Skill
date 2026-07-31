# SOS Contador API Manual Terminal Notes

This note records the manual terminal workflow for using the public SOS Contador API without the local project scripts.

Use this when the user explicitly asks to operate "manually", "via terminal", "without scripts", or "based only on the Postman documentation".

## Scope

- Use direct HTTP requests from the terminal.
- Do not use `scripts/sos_contador_api.py`.
- Do not load `.env.local` automatically.
- Do not resolve aliases through local cache files.
- The user types credentials, CUIT, and selected IDs manually.
- Prefer one command per step, so PowerShell does not show the multi-line paste warning.

## Public API Base URL

The public API base URL used from the Postman documentation flow is:

```powershell
$BaseUrl = "https://api.sos-contador.com/api-comunidad"
```

Expected result: no output, just a return to the prompt.

## Login Flow

Set the JSON body manually:

```powershell
$Body = '{"usuario":"TU_USUARIO","password":"TU_PASSWORD"}'
```

Expected result: no output.

Login with PowerShell native HTTP handling:

```powershell
$Login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/login" -ContentType "application/json" -Body $Body
```

Expected result: no output if successful.

Inspect the login object:

```powershell
$Login
```

Expected result: an object containing `jwt`.

Inspect accessible CUITs:

```powershell
$Login.cuits | Format-Table id, cuit, razon_social
```

Expected result: a table with the accessible CUIT `id`, `cuit`, and sometimes `razon_social`.

Important finding: in a real terminal test, `razon_social` was blank for the accessible CUIT rows. The user must identify the target CUIT manually from the `cuit` column or other known account context.

## Selecting A Working CUIT

After the user identifies the target CUIT row, store its `id` manually:

```powershell
$IdCuit = 124265
```

Expected result: no output.

Verify it:

```powershell
$IdCuit
```

Expected result: the selected numeric CUIT id.

Do not guess this value when guiding the user. If the user says "Empresa Demo" during a manual-only session, ask them to choose the row from the table or provide the CUIT/id.

## Methods Tried

### Correct: `Invoke-RestMethod`

This worked for `POST /login` using a JSON string stored in `$Body`:

```powershell
$Login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/login" -ContentType "application/json" -Body $Body
```

PowerShell parsed the JSON response into an object, allowing:

```powershell
$Login.cuits | Format-Table id, cuit, razon_social
```

### Incorrect Or Fragile: Multi-Line Paste

Pasting a multi-line PowerShell block triggered the terminal warning:

```text
Va a pegar texto que contiene varias lineas...
```

This is not an API error, but it interrupts the guided workflow. For this manual mode, provide one line at a time unless the user explicitly asks for a complete block.

### Incorrect Or Fragile: `curl.exe -s` With Default TLS Revocation Check

This command produced no useful response in the first attempt:

```powershell
$LoginRaw = curl.exe -s -X POST "$BaseUrl/login" -H "Content-Type: application/json" -d $Body
```

When run without `-s`, Windows curl showed:

```text
curl: (35) schannel: next InitializeSecurityContext failed: CRYPT_E_NO_REVOCATION_CHECK
```

Finding: on Windows, `curl.exe` may fail certificate revocation checks. `--ssl-no-revoke` can work around that specific issue, but `Invoke-RestMethod` is simpler for this manual workflow.

### Incorrect Or Fragile: `curl.exe --ssl-no-revoke -d $Body`

After bypassing the revocation issue, `curl.exe` returned:

```text
Expected property name or '}' in JSON at position 1
```

Finding: PowerShell plus `curl.exe -d $Body` can mangle JSON quoting or send a body shape that the API rejects. Prefer `Invoke-RestMethod` for JSON requests in PowerShell.

## Current State Of The Guided Session

Validated as of this note:

1. `$BaseUrl` was set manually.
2. `$Body` was set manually by the user.
3. `Invoke-RestMethod` login succeeded.
4. `$Login` contained `jwt`.
5. `$Login.cuits | Format-Table id, cuit, razon_social` showed accessible CUIT rows.
6. `$IdCuit` was selected manually from the CUIT table.
7. `$UserJwt = $Login.jwt` worked.
8. `GET /cuit/credentials/:idcuit` with bearer `$UserJwt` worked and returned a CUIT-scoped `jwt`.
9. `GET /venta/listado/todas/mes/todas?pagina=1&registros=20` with bearer `$CuitJwt` worked and returned an object with `items`.
10. `POST /venta/consulta?pagina=1&registros=100` with body `{"fecha_desde":"2026-03-01","fecha_hasta":"2026-03-31"}` worked for exact March 2026 sales listing.
11. `GET /venta/pdf/:id` with bearer `$CuitJwt` and `Invoke-WebRequest -OutFile` downloaded a PDF with non-zero size.

## Next Expected API Step

After `$IdCuit` is selected, store the login token:

```powershell
$UserJwt = $Login.jwt
```

Then:

```powershell
$CuitCredentials = Invoke-RestMethod -Method Get -Uri "$BaseUrl/cuit/credentials/$IdCuit" -Headers @{ Authorization = "Bearer $UserJwt" }
```

Expected result: no output if successful.

Then inspect:

```powershell
$CuitCredentials
```

Expected result: an object containing a CUIT-scoped `jwt`. That token is the one to use for business endpoints such as sales listings and PDF retrieval.

Store the CUIT-scoped token:

```powershell
$CuitJwt = $CuitCredentials.jwt
```

Expected result: no output.

## Sales Listing

Use the CUIT-scoped token for sales endpoints:

```powershell
$VentasRaw = Invoke-RestMethod -Method Get -Uri "$BaseUrl/venta/listado/todas/mes/todas?pagina=1&registros=20" -Headers @{ Authorization = "Bearer $CuitJwt" }
```

Expected result: no output.

Inspect:

```powershell
$VentasRaw
```

Expected result: an object with an `items` collection.

Observed item fields include `id`, `cae`, `fecha`, `factura`, `montototal`, `idcentrocosto`, `modificado`, `obteniendocae`, and other sale metadata.

### Incorrect Or Incomplete: Date Query On `venta/listado/.../mes/...`

This request returned `items`, but it still returned current-month records even though March 2026 was requested:

```powershell
$VentasMarzo = Invoke-RestMethod -Method Get -Uri "$BaseUrl/venta/listado/todas/mes/todas?pagina=1&registros=100&fecha_desde=2026-03-01&fecha_hasta=2026-03-31" -Headers @{ Authorization = "Bearer $CuitJwt" }
```

Observed result: April 2026 rows such as `FA-0002-00000002`.

Finding: `venta/listado/todas/mes/todas` appears to prioritize `periodo=mes`; do not rely on `fecha_desde` / `fecha_hasta` query parameters there for exact historical month filtering. Use `POST /venta/consulta` for exact date-range reads.

### Correct: Exact Date Range With `POST /venta/consulta`

Create the date-range body:

```powershell
$ConsultaMarzoBody = '{"fecha_desde":"2026-03-01","fecha_hasta":"2026-03-31"}'
```

Then request:

```powershell
$VentasMarzo = Invoke-RestMethod -Method Post -Uri "$BaseUrl/venta/consulta?pagina=1&registros=100" -ContentType "application/json" -Headers @{ Authorization = "Bearer $CuitJwt" } -Body $ConsultaMarzoBody
```

Expected result: no output.

Inspect:

```powershell
$VentasMarzo.items | Format-Table id, fecha, factura, montototal, cae
```

Observed March 2026 result included:

- `785214498` / `FA-0003-00000001`
- `<id_venta_comparacion>` / `FA-0003-00000003`
- `785214500` / `FA-0003-00000002`
- `<id_venta>` / `FA-0002-00000001`

## Sale PDF Download

Select a sale id from the listing:

```powershell
$VentaId = <id_venta>
```

Prepare an output path:

```powershell
$OutDir = "$HOME\Desktop\sos-pdfs"
```

```powershell
New-Item -ItemType Directory -Force -Path $OutDir
```

```powershell
$PdfPath = Join-Path $OutDir "$VentaId.pdf"
```

Download:

```powershell
Invoke-WebRequest -Method Get -Uri "$BaseUrl/venta/pdf/$VentaId" -Headers @{ Authorization = "Bearer $CuitJwt" } -OutFile $PdfPath
```

Verify size:

```powershell
Get-Item $PdfPath | Select-Object FullName, Length
```

Observed result for sale `<id_venta>`: file length `154901` bytes.

### Incorrect Or Version-Specific: `Format-Hex -Count`

This verification command failed on the user's PowerShell:

```powershell
Format-Hex -Path $PdfPath -Count 8
```

Error:

```text
No se encuentra ningun parametro que coincida con el nombre del parametro 'Count'.
```

Finding: not every installed PowerShell version supports `Format-Hex -Count`. Use a byte read instead when checking the PDF signature.

Correct compatible PDF signature check:

```powershell
$Bytes = [System.IO.File]::ReadAllBytes($PdfPath)[0..3]
```

```powershell
$Bytes
```

Expected decimal bytes:

```text
37
80
68
70
```

Text check:

```powershell
[System.Text.Encoding]::ASCII.GetString($Bytes)
```

Expected result:

```text
%PDF
```

## PDF Content Validation Finding

The downloaded sale PDF for `<id_venta>` was not only present on disk; it was rendered and text-extracted locally.

Observed visible invoice data:

- Issuer: `Emisor Demo S.R.L.`
- Issuer CUIT: `<cuit_emisor>`
- Voucher type: `FCE MiPyMEs A`
- Voucher type code: `201`
- Number: `A-00002-00000001`
- Date: `04/03/2026`
- Recipient: `Receptor Demo S.A.`
- Recipient CUIT: `<cuit_receptor>`
- Currency: `ARS`
- Payment due date: `18/04/2026`
- Net 21%: `8,427,419.33`
- IVA 21%: `1,769,758.06`
- Other taxes/perceptions: `0.02`
- Total: `10,197,177.41`
- CAE: `<cae>`
- QR: visually present

Important issue found:

- The label `Fecha Vto. CAE:` is present, but the value is blank in both extracted text and the rendered PDF image.

Practical conclusion:

- `GET /venta/pdf/:id` returned a PDF file with invoice-looking content and a CAE.
- The blank `Fecha Vto. CAE` does not make the download invalid by itself. It is a voucher-rendering or source-data issue to investigate separately from the API PDF download path.
- The QR was visually present, but local OpenCV decoding did not decode it in this test, so QR validity was not confirmed.

Comparison PDF:

- Sale id: `<id_venta_comparacion>`
- File: `<id_venta_comparacion>.pdf`
- Size: `156108` bytes
- Voucher: `Factura de Venta`
- Type/letter/code: `A`, code `001`
- Number: `A-00003-00000003`
- Date: `01/03/2026`
- Issuer CUIT: `<cuit_emisor>`
- Recipient: `EMPRESA DEMO S.R.L.`
- Recipient CUIT: `<cuit_trabajo>`
- Total: `1,449,144.40`
- CAE: `<cae_comparacion>`
- Fecha Vto. CAE: `11/03/2026`

Finding from comparison:

- The same public API PDF download method returned a complete PDF for `<id_venta_comparacion>`.
- Therefore the blank `Fecha Vto. CAE` in `<id_venta>` is not proven to be a general failure of `GET /venta/pdf/:id`.
- The defect may be specific to that sale, to that voucher type (`FCE MiPyMEs A`, code `201`), or to how SOS renders FCE MiPyME PDFs.

## Finding IDs From Visible Sale Numbers

When switching working CUIT manually, reuse the login JWT and request credentials for the new `idcuit`:

```powershell
$IdCuit = <idcuit>
```

```powershell
$CuitCredentials = Invoke-RestMethod -Method Get -Uri "$BaseUrl/cuit/credentials/$IdCuit" -Headers @{ Authorization = "Bearer $UserJwt" }
```

```powershell
$CuitJwt = $CuitCredentials.jwt
```

Validated target:

- Work CUIT: `<cuit_trabajo>`
- `idcuit`: `<idcuit>`

Incorrect or unsupported search attempt:

```powershell
$BuscarComprobanteBody = '{"factura":"A-00001-00000001"}'
```

```powershell
$BusquedaComprobante = Invoke-RestMethod -Method Post -Uri "$BaseUrl/venta/consulta?pagina=1&registros=20" -ContentType "application/json" -Headers @{ Authorization = "Bearer $CuitJwt" } -Body $BuscarComprobanteBody
```

Observed result:

- `$BusquedaComprobante.items` was empty.

Finding:

- `POST /venta/consulta` did not match visible invoice number through a `factura` body field in this test.
- `POST /venta/consulta` also did not match with body `{"letra":"A","puntoventa":3,"numero":205}` in this test.
- `POST /venta/consulta` also did not match with body `{"search":"A-00001-00000001"}` in this test.
- In list outputs, SOS formats Factura A as `FA-...` rather than plain `A-...`; try that representation too.
- If direct filters do not work, query by date/range or pages and filter client-side by the returned `factura` field.

Validated fallback method:

```powershell
$VentasPagina = Invoke-RestMethod -Method Get -Uri "$BaseUrl/venta/listado/todas/mes/todas?pagina=1&registros=500" -Headers @{ Authorization = "Bearer $CuitJwt" }
```

```powershell
$Match = $VentasPagina.items | Where-Object { $_.factura -eq "FA-0001-00000001" }
```

```powershell
$Match | Format-Table id, fecha, factura, montototal, cae
```

Observed match:

- Visible user number: `A-00001-00000001`
- SOS listing number: `FA-0001-00000001`
- ID: `<id_venta>`
- Date: `2026-04-21T03:00:00.000Z`
- CAE: `<cae>`

Finding:

- For currently visible/current-month sales, `GET /venta/listado/todas/mes/todas` plus local PowerShell filtering by `factura` can recover the internal sale `id`.
- User-facing `A-00001-00000001` may appear as `FA-0001-00000001` in API listings.

### More Reliable API-Only Method When The Month Is Unknown

Direct `POST /venta/consulta` filters by visible number did not work in the tested bodies, but `venta/consulta` did work as an exact date-range reader. For a month-unknown sale, request a broad date range with a high `registros` value and filter the returned `items` locally by normalized `factura`.

Important observations:

- `POST /venta/consulta` requires valid `fecha_desde` and `fecha_hasta`; without them it returned `TypeError: Cannot read properties of undefined (reading 'split')`.
- Body fields like `search`, `factura`, `letra`, `puntoventa`, and `numero` were ignored or did not narrow results in the tested calls.
- `GET /venta/listado/.../mes/...` is only useful for the current month or relative periods.
- `POST /venta/consulta` with a broad range can cover historical comprobantes without guessing the month.

Normalize a user-facing Factura A number this way:

- User-facing: `A-00001-00000002`
- API listing value: `FA-0001-00000002`

Manual broad-range search:

```powershell
$Body = '{"fecha_desde":"1900-01-01","fecha_hasta":"2099-12-31"}'
```

```powershell
$Ventas = Invoke-RestMethod -Method Post -Uri "$BaseUrl/venta/consulta?pagina=1&registros=10000" -ContentType "application/json" -Headers @{ Authorization = "Bearer $CuitJwt" } -Body $Body
```

```powershell
$Match = $Ventas.items | Where-Object { $_.factura -eq "FA-0001-00000002" }
```

```powershell
$Match | Format-Table id, fecha, factura, montototal, cae
```

Observed match:

- Work CUIT: `<cuit_trabajo>`
- `idcuit`: `<idcuit>`
- User-facing number: `A-00001-00000002`
- API listing number: `FA-0001-00000002`
- ID: `<id_venta>`
- Date: `2025-06-03T03:00:00.000Z`
- CAE: `<cae>`

Confirmed with:

```powershell
Invoke-RestMethod -Method Get -Uri "$BaseUrl/venta/detalle/<id_venta>" -Headers @{ Authorization = "Bearer $CuitJwt" }
```

The detail response confirmed `cabecera.id=<id_venta>`, `letra=A`, `puntoventa=3`, `fcncnd=F`, `numero=142`, `cae=<cae>`, and `caevencimiento=2025-06-13T03:00:00Z`.

Robustness note:

- If the broad-range result count approaches the requested `registros` value, split the search into yearly or monthly ranges and apply the same local exact filter. This avoids silently missing records if the API caps the number of returned rows.

## API PDF Retest 2026-04-24

Goal: retest the public API-only PDF path. At the time of the retest, `venta pdf` still tried `web-session` first, so `call` was used to force the public API path directly. The skill was later changed so `venta pdf` uses API first.

Method used:

```powershell
python .\sos-contador-api\scripts\sos_contador_api.py call --method GET --path venta/pdf/<id_venta> --cuit-trabajo <cuit_emisor> --out "<sos_contador_home>\local\exports\<cuit_emisor>\ventas\2026\04\2026-04-24-factura-api-<id_venta>.pdf"
```

Result for sale `<id_venta>`:

- API response content type: `application/pdf`
- File size: `154332` bytes
- PDF signature: `%PDF`
- Extracted issuer: `Emisor Demo S.R.L.`
- Extracted recipient: `Receptor Demo S.A.`
- Extracted number: `A-00002-00000002`
- Extracted CAE: `<cae>`
- Finding: `Fecha Vto. CAE:` is present but blank, matching the earlier FCE MiPyMEs A rendering/source-data issue. The PDF download is still valid.

Second method check:

```powershell
python .\sos-contador-api\scripts\sos_contador_api.py call --method GET --path venta/pdf/<id_venta> --cuit-trabajo <cuit_emisor> --out "<sos_contador_home>\local\exports\<cuit_emisor>\ventas\2026\04\2026-04-24-factura-api-<id_venta>.pdf"
```

Result for sale `<id_venta>`:

- API response content type: `application/pdf`
- File size: `155951` bytes
- PDF signature: `%PDF`
- Extracted issuer: `Emisor Demo S.R.L.`
- Extracted recipient: `EMPRESA DEMO S.R.L.`
- Extracted number: `A-00003-00000004`
- Extracted total: `1,449,144.40`
- Extracted CAE: `<cae>`
- Extracted `Fecha Vto. CAE`: `11/04/2026`

Conclusion: the public API path `GET /venta/pdf/:id` downloads valid sale PDFs and should be the primary method for invoice PDF retrieval. The blank `Fecha Vto. CAE` issue reproduced for an FCE MiPyMEs A voucher but not for a standard Factura A voucher; that issue does not contaminate or invalidate the PDF download method.




