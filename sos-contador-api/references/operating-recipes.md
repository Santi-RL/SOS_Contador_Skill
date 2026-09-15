# Recetas operativas

Leer solo la sección de la tarea. Los comandos se ejecutan desde la raíz de la skill; `<...>` indica un dato a resolver, no un valor literal. Reemplazar fechas de ejemplo por el período solicitado. Aplicar siempre CUIT explícita, vista previa, aprobación y verificación de `SKILL.md`.

## Rutas habilitadas

| Resultado | Ruta predeterminada | Alcance y frontera |
|---|---|---|
| Maestros y configuración: consultar | `cliente list/get`, `producto list`, `puntoventa list`, lecturas de catálogo `validated` o `limited` | API. Comprobar paginación y límites de `api describe`. No diseñar configuraciones nuevas. |
| Alta básica de cliente o producto | `cliente create`, `producto create` | API; body publicado completo, IDs resueltos y campos básicos. El rol proveedor y la configuración contable del producto no están cubiertos. |
| Ventas: consultar y descargar | `venta search`, `venta get`, `venta pdf` | API. PDF HTTP alternativo solo con permiso y `--allow-web-session-fallback`. |
| Ventas: registrar sin CAE | `venta create` con campos y productos del helper | HTTP directo histórico, no navegador. Solo la variante básica documentada; no actualizar ni solicitar CAE por defecto. |
| Compras: consultar | `api invoke` con `compra.search/get/list`, `libroiva.compras`, `asiento.get` | API. Libro, asiento y original comprueban aspectos distintos. |
| Compras documentales: registrar | `compra draft/create` | Alta por API; verificación activa complementaria por HTTP directo incorporado. |
| Cobranzas: consultar período relativo | `cobro list/get --id` | API; detalle HTTP alternativo solo autorizado y con flag. |
| Cobranzas: rango exacto o número visible | `cobro list-range/resolve-id`, `cobro get` sin ID | HTTP directo validado. La API publicada solo define períodos relativos; no inventar filtros. |
| Cobranza simple | `cobro create --imputaciones-json` | API, sin detalle de cheque, retención ni asociación. |
| Cobranza documental o detallada | `cobro draft/create`, `--movimientos-json`, `cobro asociar` | HTTP directo validado para detalle y asociaciones. Un grupo documental por recibo. |
| Pago bancario básico | `pago create` | API; no aplica a compras ni garantiza una cuenta de anticipo. |
| Analizar planilla ARCA/AFIP | `afip draft` | Análisis local y consultas. `afip import` real está suspendido en todos los modos hasta congelar el lote aprobado; solo se permite preview de desarrollo. Ver D15. |

`api invoke` en operativo permite lecturas comprobadas; las escrituras genéricas quedan en desarrollo/validación controlada. Los helpers no prueban todas las variantes que sus flags aceptan. Altas/ediciones de cuentas, actividades, centros, reclasificaciones, edición de maestros, emisión con CAE y asociación de pagos requieren desarrollo mientras no tengan receta suficiente. No resolver esa falta con navegador.

## Ventas

**Consultar.** Resolver CUIT y rango. Usar `venta search` con un JSON privado que contenga `fecha_desde` y `fecha_hasta` ISO; ver [consultas](public-api-payloads.md#consultas). Es POST de lectura. Revisar paginación y filtrar el resultado por fecha e identidad, aunque el servidor admita filtros. Resolver la numeración visible comparando fecha, cliente y `factura`; `A-00001-00000001` puede corresponder a `FA-0001-00000001`.

Si falta fecha, pedirla una vez. Si se desconoce, buscar 60 días y luego ventanas de 90 días, con tope inicial de 24 meses; informar cobertura alcanzada. Para «facturas emitidas», comprobar si hay notas y consultar si se incluyen antes de entregar la tabla.

**Descargar.** Con el ID resuelto:

```powershell
python scripts/sos_contador_api.py venta pdf --cuit-trabajo <cuit> --id <id_venta> --out <ruta_privada_nueva.pdf>
```

**Registrar.** Resolver cliente, producto, cuenta, centro, actividad, PV, fecha, tipo, letra y numeración. El alcance histórico es registro básico sin CAE. Leer el contrato de producto de [endpoints-v1.md](endpoints-v1.md#venta); no diseñar un body nuevo ni mandar campos de una respuesta de detalle.

```powershell
python scripts/sos_contador_api.py venta create --cuit-trabajo <cuit> --fecha <fecha> --idclipro <id_cliente> --letra <letra> --sucursal <pv> --numero <numero> --idcuenta <id_cuenta> --idprovinciaiibb <id_provincia> --idcentrocosto <id_centro> --codactividad <actividad> --productos-file <productos_privados.json> --dry-run
```

Mostrar CUIT, cliente, comprobante, fecha, conceptos, neto/IVA/total y **sin solicitud de CAE**. Tras aprobar, repetir exactamente con `--confirm` en lugar de `--dry-run`. Verificar con `venta get` y `venta search` presencia única, identidad, importes y estado. Si se pidió facturación fiscal, detener antes de crear un registro que no satisface ese pedido: el flag disponible no demuestra validación de CAE, ni el PDF prueba su autorización. Seguir D01 del roadmap con el usuario.

## Compras

**Preparar.** Leer [compra-from-pdf-folder.md](compra-from-pdf-folder.md). Cada documento independiente produce una compra. Resolver comprador, CUIT válida del proveedor, fecha y fiscalidad desde el original; resolver alícuotas, descuentos, cuentas y centro con instrucciones vigentes y antecedentes comparables.

```powershell
python scripts/sos_contador_api.py compra draft --source <archivo> --cuit-trabajo <cuit> --preview-format markdown
```

Ante discrepancias de extracción, mantener `verificar` y revisar campo por campo contra el original. No aceptar conflictos en bloque ni inventar tributos. Usar texto embebido, visión si está disponible y OCR español como contraste; inglés solo si falta español. No confiar en un CUIT inválido para dar de alta al proveedor.

**Confirmar.** Mostrar por candidato identidad, proveedor, fechas, cuentas/centro, netos e IVA por alícuota, percepciones y jurisdicción, total, duplicados y faltantes. Un proveedor nuevo es otra escritura incluida expresamente en la vista previa. La falta de rol proveedor no se repara creando otro tercero ni editando su ficha por ensayo.

```powershell
python scripts/sos_contador_api.py compra create --draft-id <id_borrador> --cuit-trabajo <cuit> --confirm
```

El helper reutiliza payload y `uniqueid` congelados y repite la deduplicación. Si el borrador cambió o caducó, volver a presentarlo. Las fechas son ISO; las notas de crédito de compra conservan importes positivos y su tipo fiscal.

**Verificar.** Detalle, período, estado activo, proveedor, identidad, todas las bases/alícuotas, percepciones y total a centavos. Si `compra.search` devuelve 50 filas, subdividir el rango; no declarar cobertura completa sin resolver la truncación. Contrastar código fiscal efectivo con el Libro IVA y original; no normalizar `081`, `001` o `201` por analogía. Para controles contables consultar asiento/mayor. Las [limitaciones comprobadas](capabilities-and-verification.md) no autorizan una corrección fuera de esta receta. Auditoría de una carpeta: [auditoria-compras.md](auditoria-compras.md).

## Cobranzas

**Consultar.** Usar `cobro list` si el período relativo responde al pedido. Para rango exacto, número visible, cheques o asociaciones, usar los helpers HTTP específicos de la tabla. Para detalle por ID, intentar API primero; habilitar el fallback explícito solo si ya fue autorizado para ese detalle.

**Preparar desde documentos.** Leer [cobro-from-document.md](cobro-from-document.md). Separar archivos con diferente orden, fecha, factura, total o cheques. Agrupar solo páginas o anexos del mismo documento.

```powershell
python scripts/sos_contador_api.py cobro draft --source <archivo> --cuit-trabajo <cuit> --preview-format markdown
```

Mostrar contexto y CUIT, cliente, movimientos con cuentas, cheques/retenciones completos, facturas a asociar, sumas y diferencias. Campos exigidos en [cobro-create-and-associate.md](cobro-create-and-associate.md). No elegir una cuenta o asociación para hacer cuadrar el total.

**Ejecutar y verificar.** Tras la aprobación:

```powershell
python scripts/sos_contador_api.py cobro create --draft-id <id_borrador> --confirm
```

Un recibo por vez. Comprobar recibo, movimientos y asociaciones por lectura. Si la creación terminó pero la asociación falló, no repetir `create`: consultar el recibo y las asociaciones, informar estado parcial y detener; una reparación exige su propio preview. Un memo no asocia facturas. No crear o editar perfiles de extracción en operativo.

## Pagos

**Alcance.** Un pago bancario sencillo a un proveedor existente. Verificar fecha, proveedor, banco de origen, cuenta, centro y monto. El banco del receptor no identifica el banco que debitó el dinero. No aceptar como pago aplicado a una factura lo que solo es un movimiento bancario.

Preparar un JSON privado de medios de pago, por ejemplo `[{"fv":"100.00","cuid":"<id_cuenta_banco>"}]`. `cuid` es cuenta contable, no ID de compra. No usar `--movimientos-json` para cheques/retenciones de pagos: esa variante no está validada.

```powershell
python scripts/sos_contador_api.py pago create --cuit-trabajo <cuit> --fecha <fecha> --idclipro <id_proveedor> --idcuenta <id_cuenta> --idprovinciaiibb <id_provincia> --idcentrocosto <id_centro> --imputaciones-file <medios_privados.json> --dry-run
```

Mostrar proveedor, fecha, banco/cuenta, importe y **sin aplicación a compras**. Tras aprobar, repetir sin cambios con `--confirm`. Verificar `pago get`, listado y asiento: banco, importe y contrapartida efectiva. Si SOS debita Proveedores cuando se esperaba Anticipos, no repetir el pago ni crear un asiento compensatorio por iniciativa propia. Informar el límite y pedir desarrollo. Asociación, anticipo y retenciones siguen D04 del roadmap.

## Otros documentos y terceros

Para planillas, seguir [mis-comprobantes-afip.md](mis-comprobantes-afip.md) sin reconstruir su parser. En operativo solo preparar `afip draft`; no ejecutar la importación histórica ni asumir que sus residuales representan tributos identificados. No importar una variante cuyo subtipo fiscal no se conserva. Para comprobante faltante, [percepciones-iibb-sin-comprobante.md](percepciones-iibb-sin-comprobante.md) aporta límites documentales; no autoriza accesos fiscales, presentaciones o nuevas rutas por fuera del alcance de SOS.

Las altas básicas de maestros usan los bodies de [public-api-payloads.md](public-api-payloads.md#maestros), un archivo privado, `--dry-run` y luego `--confirm`. Verificar por CUIT/código y listado. Si hace falta preservar una ficha existente, rol proveedor, actividad o configuración contable no expuesta, detener: las actualizaciones no equivalen a PATCH.
