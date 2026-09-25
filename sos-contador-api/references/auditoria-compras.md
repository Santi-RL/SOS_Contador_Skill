# Auditoría de compras por período

Esta auditoría permite las lecturas previstas; las correcciones que no tienen receta operativa requieren desarrollo y validación controlada. No reconstruir cuerpos libres para reclasificar en operativo.

Usar cuando el objetivo sea revisar compras ya registradas en SOS Contador contra una carpeta documental, corregir importes o imputaciones y dejar un cierre verificable. Para crear compras nuevas desde documentos, usar [compra-from-pdf-folder.md](compra-from-pdf-folder.md). Para campos y transportes comprobados, consultar [capabilities-and-verification.md](capabilities-and-verification.md).

## Resultado esperado

Separar cuatro resultados que no son equivalentes:

1. **integridad documental:** qué registros tienen original y qué documentos no tienen registro;
2. **exactitud fiscal:** identidad, código de comprobante, bases, IVA, percepciones y otros tributos;
3. **imputación contable:** cuenta, función, actividad y centro según naturaleza y destino;
4. **cierre:** correcciones verificadas y controles diferidos, sin declarar cerrado el IVA si subsisten decisiones fiscales.

Una compra puede tener importes correctos y una cuenta incorrecta, o estar bien contabilizada y mal presentada en el Libro IVA. Informar cada dimensión por separado.

## Preparar el inventario

1. Resolver el contribuyente y leer sus [instrucciones privadas vigentes](taxpayer-instructions.md).
2. Delimitar período, documentos incluidos, carpeta durable elegida por el usuario y alcance de las correcciones autorizadas.
3. Guardar lecturas previas privadas:
   - `compra.search` para el rango exacto;
   - `libroiva.compras` para el mes;
   - compras anuladas por separado cuando formen parte del control.
4. Si `compra.search` devuelve 50 filas, subdividir el rango antes de concluir que el período está completo.
5. Inventariar los archivos sin moverlos todavía. Distinguir facturas, notas, tiques, transferencias, resúmenes, presupuestos y vistas repetidas del mismo comprobante.

Usar como clave primaria de conciliación:

- CUIT del proveedor;
- código o naturaleza fiscal;
- letra;
- punto de venta;
- número.

Comparar también fecha, netos e IVA por alícuota, no gravado, exento, tributos y total a centavos. Dos fotografías del mismo tique constituyen un original, no dos compras. Una transferencia respalda el pago, pero no reemplaza el detalle fiscal.

## Ordenar y renombrar documentos

Seguir la [regla de propuesta y consentimiento](safety-and-storage.md#instrucciones-vigentes-y-expedientes): un nombre genérico justifica ofrecer una alternativa, no cambiarlo por cuenta propia. Cuando el usuario pida normalizar nombres, preparar primero un mapa `origen → destino` y revisarlo antes de cambiar archivos. Una forma legible es:

```text
<PROVEEDOR>_<CUIT>_<TIPO>_<PV>_<NUMERO>.<ext>
```

Ejemplo ficticio:

```text
EMPRESA DEMO SRL_30000000007_FC A_00003_00000125.pdf
```

- Derivar el tipo del código del original o de una fuente fiscal confiable; la letra por sí sola no distingue todos los subtipos.
- Conservar ceros iniciales y extensión. Sanitizar únicamente caracteres inválidos para la plataforma.
- No sobrescribir, fusionar ni agregar sufijos arbitrarios cuando existe una colisión: resolver primero si son duplicados, páginas complementarias o documentos distintos.
- Mantener transferencias y otros respaldos identificados como tales; no renombrarlos como facturas.
- Respetar la carpeta durable indicada por el usuario. No crear otra copia privada solo para imponer la estructura predeterminada.

## Conciliar en ambos sentidos

Construir una fila por identidad y clasificarla, como mínimo, en uno de estos estados:

| Estado | Significado y acción |
|---|---|
| `correcto` | Original, SOS, asiento y Libro IVA coinciden dentro del alcance revisado. |
| `documento_sin_registro` | Preparar alta con el flujo documental; deduplicar otra vez antes de escribir. |
| `registro_sin_original` | No inventar detalle. Buscar respaldo alternativo y mantener separado el control documental del fiscal. |
| `diferencia_importes` | Resolver contra el original antes de proponer una corrección. |
| `imputacion_pendiente` | Los importes pueden estar verificados aunque falte confirmar naturaleza o destino. |
| `corregido_verificado` | La escritura fue autorizada y comprobada con una lectura independiente. |
| `control_fiscal_diferido` | Falta una fuente, período completo o decisión profesional; indicar qué hecho permitirá resolverlo. |
| `diferencia_tecnica` | Redondeo o precisión interna sin tributo real; documentar y evitar regrabar si no tiene efecto material. |

Para un original extraviado, una exportación de percepciones puede respaldar un tributo, pero no reconstruye artículos, bases ni IVA. Seguir [percepciones-iibb-sin-comprobante.md](percepciones-iibb-sin-comprobante.md) y no interpretar una consulta temprana sin coincidencias como importe cero.

Cuando varios pendientes dependan del usuario, investigar primero todo lo disponible y plantear **un caso por vez**: proveedor, fecha, comprobante, importe, tratamiento actual y una única decisión concreta. Incorporar la respuesta al estado vigente antes de pasar al siguiente caso; no repetir preguntas ya resueltas ni trasladar al usuario búsquedas que puedan hacerse con el original, las lecturas o los antecedentes.

## Revisar cada compra

Aplicar esta secuencia solo a los registros con diferencias o cambios propuestos; las lecturas generales del período sirven como control de cobertura:

1. Abrir el original completo y `compra.get`.
2. Confirmar código fiscal. Contrastar el original, `cabecera.tipocomprobante` y `libroiva.compras.codigocomprobanteafip`; resolver discrepancias según [capabilities-and-verification.md](capabilities-and-verification.md).
3. Comparar bases e IVA por alícuota, no gravado, exento, percepciones por jurisdicción y otros tributos. No validar una distribución solo porque coincide el total.
4. Determinar la cuenta por naturaleza y destino documentados. El antecedente del proveedor es una pista; no reemplaza el análisis de la operación.
5. Revisar por separado categoría de crédito fiscal, cuenta, distribución funcional, actividad y centro. Una cuenta compartida no debe cambiarse globalmente para resolver un solo comprobante sin medir el alcance.
6. Consultar `asiento.get` cuando la corrección tenga efecto contable. El detalle de la compra no siempre identifica por sí solo la cuenta efectiva de cada tributo.

Si un comprobante combina servicios, bienes o destinos, separar únicamente con un desglose documentado. No inventar porcentajes. Que un concepto sea costo contable tampoco demuestra por sí solo que su IVA o tributo sea recuperable.

Una categoría fiscal puede cambiar la presentación en el Libro IVA sin modificar el asiento contable. A la inversa, una cuenta de gasto puede producir un asiento correcto y quedar expuesta en una columna fiscal inadecuada. Verificar ambos resultados y, si todavía no está determinado qué salida fiscal utiliza el contador, conservar la decisión como pendiente explícito en lugar de modificar comprobantes por prevención.

## Corregir con alcance controlado

1. Conservar la lectura previa y describir el cambio por comprobante.
2. Mostrar vista previa o `--dry-run`; obtener autorización explícita para el conjunto delimitado.
3. Usar la API pública cuando el campo esté cubierto. `compra.save` no es un PATCH: preservar identidad y todos los campos que no deben cambiar.
4. Si la API no persiste el campo o falta una receta para la variante, detener las escrituras y solicitar desarrollo. No completar por navegador en operativo. Las observaciones históricas de UI requieren desarrollo explícito y sus escrituras, una prueba controlada autorizada.
5. Ante timeout o respuesta ambigua, leer el estado antes de repetir. No recrear una compra para reparar una actualización incierta.

Para avanzar con rapidez sin perder control, agrupar lecturas independientes y reutilizar sus salidas privadas. Ejecutar mutaciones en secuencia. Tras una tanda pequeña, verificar cada registro modificado y volver a leer una sola vez el período completo para detectar efectos laterales.

## Verificación posterior

Para cada compra modificada, comprobar:

- identidad, fecha, CAE y estado activo;
- cuenta de cabecera y líneas, actividad y centro;
- bases e IVA por alícuota, no gravado, exento, tributos y total a centavos;
- asiento balanceado y cuentas efectivas cuando corresponda;
- categoría, código fiscal, IVA computable y jurisdicciones en `libroiva.compras`;
- presencia única en el período.

Comparar conteo e identidades del período antes y después. Si una corrección debía afectar un solo comprobante, cualquier otra diferencia exige detener el cierre y explicar el alcance.

## Cerrar sin convertir las instrucciones en un log

El expediente privado conserva inventario, importes, lecturas, vistas previas y verificaciones. Las instrucciones vigentes de la empresa conservan solo reglas reutilizables: condiciones de aplicación, cuentas, destinos, excepciones y pendientes actuales.

- Actualizar una regla existente en lugar de agregar una narración por acción.
- Retirar de `pendientes.md` lo resuelto; conservar el criterio resultante en el tema correspondiente.
- Si el usuario informa que un original no existe, registrar ese estado y no volver a pedirlo salvo nueva evidencia.
- Distinguir «auditoría contable cerrada» de «IVA listo para presentar». Enumerar las decisiones fiscales, listados futuros o verificaciones externas que sigan pendientes.

No publicar nombres, CUIT, rutas, facturas, capturas ni relaciones comerciales reales. Transferir a la skill únicamente el procedimiento generalizado.
