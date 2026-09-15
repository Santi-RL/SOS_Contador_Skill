# API desde una terminal manual

Usar solo cuando el usuario pide trabajar sin scripts o desde la documentación de Postman. Guiar **un comando por vez** y esperar confirmación antes de continuar. No usar helpers, cargar `.env.local` ni resolver aliases automáticamente. El usuario ingresa sus credenciales, CUIT e IDs; no pedir que publique tokens en el chat.

El formato manual no cambia el modo: en operativo, únicamente rutas de lectura y recetas ya comprobadas. Si hace falta investigar, solicitar desarrollo. Una escritura exige vista previa del destinatario, payload y efecto, seguida de aprobación; no usar la terminal para eludir el CLI.

## Acceso

Definir la base:

```powershell
$BaseUrl = "https://api.sos-contador.com/api-comunidad"
```

Pedir al usuario que ingrese su usuario y contraseña en la terminal mediante un diálogo seguro; no mostrar una contraseña escrita como ejemplo:

```powershell
$CredencialSOS = Get-Credential -Message "Credenciales de SOS Contador"
```

Construir el body en memoria (no imprimirlo):

```powershell
$Body = @{ usuario = $CredencialSOS.UserName; password = $CredencialSOS.GetNetworkCredential().Password } | ConvertTo-Json -Compress
```

Autenticar:

```powershell
$Login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/login" -ContentType "application/json" -Body $Body
```

Mostrar solo las CUIT accesibles, no todo `$Login`:

```powershell
$Login.cuits | Format-Table id, cuit, razon_social
```

`razon_social` puede estar vacía. Pedir que identifique la fila por CUIT; no inferir el ID. El usuario escribe el ID seleccionado:

```powershell
$IdCuit = Read-Host "ID de la CUIT de trabajo seleccionada"
```

Obtener credenciales de esa CUIT sin imprimir tokens:

```powershell
$CuitCredentials = Invoke-RestMethod -Method Get -Uri "$BaseUrl/cuit/credentials/$IdCuit" -Headers @{ Authorization = "Bearer $($Login.jwt)" }
```

```powershell
$CuitJwt = $CuitCredentials.jwt
```

Comprobar que hay token mediante una salida booleana, nunca el token completo:

```powershell
-not [string]::IsNullOrWhiteSpace($CuitJwt)
```

## Lecturas

La [documentación pública](public-api.md) identifica método, path, parámetros y estado; los cuerpos de consulta están en [public-api-payloads.md](public-api-payloads.md#consultas). Reemplazar marcadores y fechas con los valores aportados por el usuario antes de guiar el comando.

Ejemplo de consulta de ventas por mes explícito, con fechas ficticias:

```powershell
$Body = '{"fecha_desde":"2026-01-01","fecha_hasta":"2026-01-31"}'
```

```powershell
$Ventas = Invoke-RestMethod -Method Post -Uri "$BaseUrl/venta/consulta?pagina=1&registros=50" -ContentType "application/json" -Headers @{ Authorization = "Bearer $CuitJwt" } -Body $Body
```

```powershell
$Ventas.items | Format-Table id, fecha, factura, montototal
```

Comprobar paginación, filas activas y rango efectivo. Para número visible, normalizar `A-00001-00000001` a `FA-0001-00000001` y filtrar las filas recibidas, verificando fecha y cliente. Sin fecha, aplicar los límites de búsqueda de [operating-recipes.md](operating-recipes.md); no consultar 1900–2099 ni pedir decenas de miles de filas por defecto.

## Descarga de PDF

Resolver el ID por lectura; no adivinarlo. Pedir la ruta privada de salida y comprobar que no existe. Guardar primero la respuesta en una variable con `Invoke-WebRequest`, revisar Content-Type y firma `%PDF`, y solo después escribir mediante un archivo nuevo. Un JSON de error no es un PDF aunque el nombre termine en `.pdf`. Si el usuario quiere guía de guardado, dar el siguiente comando según su versión de PowerShell y esperar confirmación; no reemplazar archivos.

`GET /venta/pdf/<id_venta>` es la ruta pública. Comparar emisor, receptor, tipo, PV, número, fecha e importes con el detalle. Una fecha de vencimiento de CAE vacía se ha observado en ciertos PDFs; es una discrepancia documental a investigar, no prueba de fallo general del endpoint. Un QR visible no demuestra que se haya decodificado ni validado.

## Hallazgos generales conservados

- Login y credenciales devuelven el token en `jwt`; el segundo está acotado a la CUIT seleccionada.
- `Invoke-RestMethod` evita problemas observados al pasar JSON con comillas a `curl.exe` en PowerShell. No desactivar TLS o revocación para resolver un error de certificados; corregir la configuración de confianza.
- Los filtros de fechas en `venta/listado/.../mes/...` no sustituyen a `POST /venta/consulta` por rango exacto.
- `venta/consulta` necesita fechas válidas; se observó un error de `split` sin ellas. Campos improvisados `search`, `factura`, `letra`, `puntoventa` y `numero` no produjeron el filtrado esperado. Usar solamente los campos de consulta publicados y contrastar la respuesta.
- `Format-Hex -Count` no está disponible en todas las versiones de PowerShell; comprobar capacidades locales al guiar inspecciones binarias.
- Si una consulta alcanza el límite de filas, paginar o subdividir el rango; no asumir completitud.

Los resultados concretos y el estado de una sesión pertenecen al expediente privado. En desarrollo actualizar esta guía **en su lugar** con aprendizajes generalizados, sin fechas de ejecución, IDs reales, importes originales ni un relato por turno. Seguir el [roadmap](development-roadmap.md) para convertir un hallazgo en receta comprobada.
