# Mis Comprobantes ARCA/AFIP

## Alcance vigente

En operativo usar únicamente `afip draft` para **Mis Comprobantes Recibidos**. El parser identifica también archivos de emitidos, pero el flujo de borrador actual los rechaza: no hay receta de análisis o importación de ventas por esta vía. No cambiar el título, la CUIT ni el sentido del archivo para forzar su aceptación.

La importación real está suspendida **en todos los modos**, incluida validación controlada. El código histórico de `afip import` reconstruye el lote al confirmar y normaliza residuales sin demostrar su naturaleza. El análisis sigue disponible; guardar un borrador local no congela todavía un lote ejecutable aprobado. El trabajo pendiente está en D15 del [roadmap](development-roadmap.md).

```powershell
python scripts/sos_contador_api.py afip draft --source <planilla_privada.xlsx>
python scripts/sos_contador_api.py --work-mode development afip import --source <planilla_privada.xlsx> --dry-run
```

No ejecutar una importación real ni invocar directamente las funciones Python para eludir el bloqueo. Para documentos individuales con receta disponible, usar [compra-from-pdf-folder.md](compra-from-pdf-folder.md); esto no convierte la planilla en un lote autorizado.

## Reconocer archivo, CUIT y columnas

1. Inspeccionar la primera fila. `Comprobantes Recibidos` corresponde a compras; `Comprobantes Emitidos`, a ventas. La CUIT de trabajo proviene de esa misma fila y se resuelve contra el catálogo accesible. Si contradice una CUIT explícita del usuario, detenerse y aclarar el destino.
2. La segunda fila contiene las columnas: fecha, tipo, punto de venta, números desde/hasta, autorización, documentos y denominaciones de emisor/receptor, moneda, tipo de cambio, bases, IVA, tributos y total. Si el formato cambió materialmente, tratarlo como un formato pendiente de desarrollo; no reconstruir otro parser durante la operación.
3. En recibidos, el emisor es el proveedor y el receptor debe corresponder a la CUIT de trabajo. Conservar ambas identidades separadas.
4. Validar fecha, tipo, importes y numeración. `Número Desde` y `Número Hasta` deben existir y ser iguales; un rango, una fecha inválida o un tipo desconocido deja la fila en `verificar`.

## Tipos fiscales y límites del mapeo actual

| Tipo del archivo | Interpretación y soporte actual |
|---|---|
| `1 - Factura A` | El parser usa `F`, letra `A`, `tipocomprobante=1`. Contrastar original, detalle y Libro IVA. |
| `81 - Tique Factura A` | El mapeo histórico usa también `F/A/1`; eso **no demuestra** que la importación conserve `081`. La configuración del proveedor y el código efectivo del libro requieren su propia validación. |
| `201 - Factura de Crédito Electrónica MiPyMEs (FCE) A` | Es un subtipo distinto de `001`. No está implementado en `afip_type_rule`; debe permanecer para verificar, sin sustituirlo por Factura A. |
| `11 - Factura C` | El parser usa `F/C/11`. Revisar los importes no gravados/exentos contra la fuente; no inventar IVA ni decidir su clasificación por diferencia. |
| `3 - Nota de Crédito A` | El parser usa `C/A/3`. En compras SOS conserva magnitudes positivas y expresa la naturaleza con el tipo; no transformar una nota en factura ni negar los importes indiscriminadamente. |

La letra y `fcncnd` no distinguen todos los subtipos. Conservar el código de origen y comparar `compra.get.cabecera.tipocomprobante` con `libroiva.compras.codigocomprobanteafip`. Si original y libro indican `001` y la cabecera devuelve `201`, registrar la discrepancia según [capabilities-and-verification.md](capabilities-and-verification.md); no regrabar la compra solo para normalizar un campo limitado.

## Importes y residuales

Conservar el desglose del archivo: bases e IVA de 0 %, 2,5 %, 5 %, 10,5 %, 21 % y 27 % cuando existan, no gravado, exento, otros tributos, IVA total, total, moneda y tipo de cambio. Los valores no soportados deben quedar visibles para revisión, sin fusionarlos con otra alícuota. El parser actual detecta bases o IVA al 2,5 % y 5 % y agrega un error de variante no admitida; no prometer su importación porque esas columnas existan.

El código histórico normaliza diferencias entre total y suma de partidas como `nogravado` en Factura C y `percepcionotra` en otras compras. Esa normalización es una limitación del análisis, **no evidencia de un impuesto**. Contrastar residuales con el original y no aceptar el importe clasificado automáticamente, crear una percepción ni alterar una base para hacer cerrar la fila. No confundir una diferencia subcentavo del cálculo de SOS con un tributo documentado.

## Deduplicación y cobertura

El borrador actual combina consulta API de compras, detalles y un índice HTTP directo de estado activo. HTTP no es obligatorio por ser intrínsecamente más seguro: es la implementación actual. La auditoría de lecturas ya comprobó consultas API por rango; completar su recorrido corresponde a D05.1 antes de sustituir consumidores.

La consulta API usada por el análisis aún no recorre todas las posiciones. Si alcanza el límite observado de 50 filas, no demuestra que la deduplicación del lote sea exhaustiva. Una ausencia en ese conjunto no prueba que falte la compra. Conservar la advertencia de cobertura en el resultado; no presentar las filas `pendiente` como un lote listo para registrar. Consultar [api-read-audit.md](api-read-audit.md) y las recetas vigentes sin diseñar una ruta alternativa en operativo.

Comparar la identidad fiscal —CUIT del proveedor, tipo o naturaleza, letra, PV y número— además de fecha y partidas. El CAE puede aportar una coincidencia cuando ambas fuentes lo exponen, pero su ausencia no justifica duplicar un documento. Ante identidad coincidente con importes distintos, abrir el detalle y mantener `verificar`; nunca tratarlo como compra nueva. El origen de importación informado por SOS no determina si es un duplicado.

Excluir de los activos `cancelado=1`, `fechabaja` no vacía y secciones `ANULADOS`, salvo consulta expresa sobre anulados. Bajas y reemplazos de comprobantes permanecen bloqueados.

## Proveedor y clasificación contable

Buscar el tercero por CUIT; la denominación es un dato de apoyo. Si falta o es ambiguo, conservar el faltante sin adivinar `idclipro`. El alta API básica comprobada creó un tercero con rol cliente: no presentarla como una receta de alta de proveedor ni repetir el alta para obtener ese rol. D06 debe validar rol y preservación de ficha antes de habilitar altas automáticas en este flujo.

La planilla no demuestra la naturaleza y el destino de cada gasto. Resolver cuenta, centro y jurisdicción con el original y las instrucciones vigentes de la empresa. Una provincia del proveedor no demuestra la jurisdicción de todas las percepciones. Si la clasificación no está definida, mantenerla pendiente.

La API aceptó históricamente compras sin `idcuenta` y SOS asignó una cuenta predeterminada, incluso una de ventas en un caso. Eso demuestra aceptación técnica, no una imputación correcta. No recomendar omitir la cuenta por velocidad ni adoptar una cuenta o un centro sin aprobación. Cualquier futura variante que delegue valores al sistema debe mostrar ese efecto en el preview y verificar su resultado.

## Borrador y presentación al usuario

El análisis clasifica las filas como `ya_cargado`, `pendiente` o `verificar`. Esos estados deben acompañarse de sus límites: cobertura, diferencias de identidad/importes, proveedor, subtipo y clasificación sin resolver. Ningún estado habilita la importación real suspendida.

Conservar fuente y fila, CUIT y sentido, contraparte, fecha e identidad, código fiscal original, CAE informado, moneda, partidas, clasificación propuesta y motivos de revisión. Guardar el borrador y la evidencia en el hogar privado. Mostrar tablas con faltantes concretos; una planilla de análisis no sustituye los comprobantes originales ni acredita su archivo.

Para estructuras de escritura consultar [public-api-payloads.md](public-api-payloads.md#compras). No mantener otro ejemplo de body de importación ni reutilizar un detalle de SOS sin transformar. El body de una compra individual comprobada no valida la reconstrucción de un lote.

## Condiciones para rehabilitar la importación

D15 debe resolver conjuntamente:

- lote congelado con fuente, CUIT, bodies, `uniqueid`, proveedores y efectos adicionales identificados;
- rechazo de cambios entre vista previa y confirmación, sin reconstrucción silenciosa del lote;
- deduplicación completa y repetida antes de cada escritura, con tratamiento de estados parciales y respuestas ambiguas;
- rol proveedor, cuentas y valores predeterminados aceptados expresamente;
- subtipos y alícuotas por variante, incluida la diferencia entre `001`, `081` y `201`;
- residuales resueltos contra fuentes, sin inventar tributos, y verificación posterior de identidad, estado, asiento y Libro IVA.

Validar primero con datos ficticios y alcance de escritura propio. Emitidos requiere un desarrollo separado. Resolver solo la paginación o disponer de un dry-run correcto no rehabilita la importación.
