---
name: sos-contador-api
description: Operar SOS Contador mediante su API pública y, solo cuando sea imprescindible, mediante HTTP web-session sin navegador. Usar para autenticar cuentas, resolver contribuyentes por nombre o CUIT, consultar o gestionar clientes, proveedores, productos, ventas, compras, cobros, pagos, recibos, asientos, libros IVA, mayor, sumas y saldos, CAE, centros de costo, puntos de venta, e-Ventanilla, índices y demás operaciones documentadas; también para importar comprobantes de ARCA/AFIP o crear compras y cobranzas desde documentos.
---

# SOS Contador

Operar con el CLI incluido y mantener explícito el CUIT de trabajo. Preferir helpers especializados para flujos validados y usar el catálogo declarativo para el resto de la API pública.

## Flujo principal

1. Identificar la operación y si es lectura, consulta semántica o escritura.
2. Resolver el contribuyente si el usuario lo nombró informalmente:

```powershell
python scripts/sos_contador_api.py auth resolve-cuit --name "empresa demo"
```

3. Fijar `--cuit-trabajo`, `--cuit-trabajo-id` o `--cuit-trabajo-nombre` en toda operación autenticada con JWTC.
4. Usar primero un helper especializado cuando exista.
5. Para capacidades sin helper, consultar `api catalog` o `api describe` y ejecutar por ID estable con `api invoke`.
6. Ejecutar lecturas directamente. Para escrituras, mostrar primero `--dry-run` y ejecutar con `--confirm` solo después de la confirmación explícita del usuario.
7. Verificar el resultado de toda escritura mediante una lectura independiente.

La configuración estándar se carga desde variables de entorno o `~/.sos-contador/.env.local`. Permitir otra ubicación mediante `SOS_CONTADOR_HOME`. No volver a pedir credenciales si el archivo privado existe.

## Helpers especializados

Usar estos comandos para los flujos ya validados:

- `auth info|list-cuits|resolve-cuit|web-info`
- `cliente list|get|create|update|delete`
- `producto list|create|update`
- `compra draft|create`
- `cobro list|get|list-range|resolve-id|draft|create|asociar|profile`
- `pago list|get|create`
- `puntoventa list`
- `venta list|list-all|get|search|pdf|create`
- `afip draft|import`

Usar el catálogo público para cualquier otra operación:

```powershell
python scripts/sos_contador_api.py api catalog
python scripts/sos_contador_api.py api catalog --module asiento
python scripts/sos_contador_api.py api describe --operation indiceaniomes.list
python scripts/sos_contador_api.py api invoke --operation indiceaniomes.list --cuit-trabajo <cuit_trabajo>
python scripts/sos_contador_api.py api invoke --operation iva.list --cuit-trabajo <cuit_trabajo> --param ejercicio=2026 --query anio=2026 --query mes=07
```

Leer [references/public-api.md](references/public-api.md) antes de usar una operación genérica. Leer [references/public-api-payloads.md](references/public-api-payloads.md) antes de preparar un body de escritura.

## Reglas de seguridad

- No usar automatización de navegador, perfiles de navegador, cookies existentes ni toma de sesión para tareas normales.
- Usar la API pública primero. Tratar `web-session` como fallback HTTP interno y frágil.
- No cambiar automáticamente a `web-session` cuando falle una operación que debería funcionar por API. Diagnosticar primero y pedir permiso antes del fallback.
- No anular, cancelar, eliminar ni dar de baja un comprobante salvo pedido explícito para ese comprobante y mecanismo previamente validado.
- Mantener bloqueados por defecto `compra.delete`, `venta.delete`, `cobro.delete` y `pago.delete`.
- No incluir tokens, contraseñas, CUIT reales ni datos de clientes en archivos públicos, ejemplos, pruebas o documentación.
- No imprimir tokens salvo pedido explícito del usuario mediante una opción diseñada para ello.
- No confiar en IDs recordados. Resolverlos por catálogo o lectura.
- Tratar como anulados los registros con `cancelado=1`, `fechabaja` no vacía o inclusión en una sección `ANULADOS`.

Leer [references/safety-and-storage.md](references/safety-and-storage.md) para mutaciones, exportaciones, redacción de secretos y selección de transporte.

## Ventas

- Consultar por rango exacto con `venta search` o `api invoke --operation venta.search`; este `POST` es una consulta y no una escritura.
- Resolver un comprobante visible con el rango más estrecho disponible y comparar `factura`, fecha y cliente. Normalizar `A-00001-00000001` frente a `FA-0001-00000001`.
- Si no hay fecha, pedirla una vez. Si el usuario no la conoce, buscar hacia atrás: 60 días, luego ventanas de 90 días, con límite inicial de 24 meses.
- Si el usuario pide “facturas emitidas” y el período contiene notas de crédito o débito, preguntar si desea solo facturas o incluir también las notas. Si las incluye, devolver una sola tabla combinada.
- La colección pública documenta `venta.save` (`PUT /venta/:id?`) para crear o modificar ventas. Mantenerla como `documented-unvalidated` hasta completar una prueba controlada; el helper histórico `venta create` sigue usando `web-session` por compatibilidad.

## Cobros desde documentos

Usar el flujo documental únicamente cuando la solicitud parte de PDF, imagen, TXT, CSV, XLSX o XLS:

1. Agrupar archivos por recibo comercial.
2. Crear un borrador por grupo con `cobro draft --preview-format markdown`.
3. No unir archivos con distintos números de orden, fechas, facturas, totales o cheques.
4. Mostrar contexto, movimientos, asociaciones, totales y campos faltantes.
5. Esperar el OK explícito.
6. Ejecutar un recibo por vez con `cobro create --draft-id <id> --confirm`.
7. Verificar el recibo y sus asociaciones.

Leer [references/cobro-from-document.md](references/cobro-from-document.md) para extracción y perfiles locales. Leer [references/cobro-create-and-associate.md](references/cobro-create-and-associate.md) para creación detallada y asociación.

## Compras e importaciones ARCA/AFIP

- Para “Mis Comprobantes Recibidos/Emitidos”, leer [references/mis-comprobantes-afip.md](references/mis-comprobantes-afip.md).
- Para compras desde PDF o imágenes, leer [references/compra-from-pdf-folder.md](references/compra-from-pdf-folder.md).
- Para OCR, usar español (`spa`) por defecto y recurrir a inglés (`eng`) solo cuando español no esté disponible. Si faltan ambos idiomas, detener la extracción y reportar la configuración requerida; no inferir datos fiscales desde una lectura parcial.
- En compras documentales, tratar cada `--source` como un comprobante independiente. No fusionar archivos salvo que sean páginas o vistas complementarias del mismo documento.
- Crear primero `compra draft --source <archivo> --cuit-trabajo <cuit> --preview-format markdown`; mostrar el borrador y esperar el OK explícito.
- Ejecutar después `compra create --draft-id <id> --confirm`. El comando debe usar sin modificaciones el payload y `uniqueid` congelados en el borrador aprobado.
- Deducir el CUIT de trabajo únicamente de una sección inequívoca de comprador/receptor.
- Validar el dígito verificador de todo CUIT extraído por OCR antes de buscar o crear un proveedor. Un CUIT inválido no demuestra que el proveedor falte.
- Antes de crear un proveedor o elegir una imputación, buscar el maestro por CUIT válido y revisar compras activas anteriores del mismo proveedor cuando existan.
- Reutilizar cuenta, centro de costo y tratamiento impositivo solo desde antecedentes comercialmente análogos; no copiar fechas, numeración ni importes.
- Separar neto e IVA por alícuota. Si el comprobante informa descuentos por alícuota, aplicarlos al neto correspondiente antes de armar las imputaciones; no volver a cargarlos en `descuento` cuando el neto impreso ya es final.
- Registrar una percepción provincial identificada como IIBB en `percepcioniibb` y conservar `idprovinciaiibb`; dejar para verificar cualquier total genérico de otros tributos hasta clasificarlo explícitamente como no gravado, exento, percepción de IIBB u otra percepción.
- Deduplicar al preparar el borrador y repetir la comprobación inmediatamente antes de escribir.
- Si `compra.search` devuelve 50 filas, tratar el resultado como potencialmente truncado y subdividir el rango de fechas.
- En compras, usar fechas ISO `YYYY-MM-DD` en `fecha` y `fechaiva`.
- Mantener positivas las notas de crédito de compra y representar su naturaleza con `fcncnd` y `tipocomprobante`.
- Verificar después de crear: identidad del comprobante, proveedor, fecha persistida, todas las alícuotas, percepción de IIBB, total redondeado a centavos, presencia en el período y estado activo.

## Modo terminal manual

Si el usuario pide trabajar manualmente, sin scripts o solo desde Postman:

- No usar `scripts/sos_contador_api.py`.
- No cargar `.env.local` automáticamente.
- Guiar un comando de PowerShell por vez y esperar confirmación.
- Seguir `POST /login`, `GET /cuit/credentials/:idcuit` y luego la operación comercial.
- Registrar hallazgos en [references/manual-terminal-api.md](references/manual-terminal-api.md).

## Salida y almacenamiento

- Presentar conjuntos de registros en tablas Markdown.
- Usar prosa para un solo detalle o una respuesta demasiado ancha.
- No mencionar el transporte en respuestas normales salvo que afecte alcance o confiabilidad.
- Guardar exportaciones durables bajo `<SOS_CONTADOR_HOME>/local/exports/<cuit_trabajo>/<tipo>/<YYYY>/<MM>/` con fecha ISO al comienzo del nombre.
- Mantener capturas, perfiles, PDFs, datos reales y notas de diagnóstico únicamente bajo `<SOS_CONTADOR_HOME>/local/`, fuera de la skill instalada.

## Límites documentales

Tratar como experimentales las operaciones cuyo propio documento es incompleto o contradictorio, especialmente `cuentacorriente.list` y `mayor.list`. No inferir cuerpos, filtros ni semántica destructiva ausente. Validar primero con una lectura o un `--dry-run` y documentar solo reglas generalizables.
