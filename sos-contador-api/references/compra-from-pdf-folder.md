# Compras desde PDF o imagen

Este flujo registra comprobantes de compra provenientes de PDF, imagen o texto. Es análisis primero: el borrador se revisa antes de cualquier escritura y la creación usa exactamente el payload aprobado.

## Flujo recomendado

1. Resolver explícitamente el CUIT de trabajo.
2. Tratar cada archivo como un comprobante independiente.
3. Extraer identidad, proveedor e importes por alícuota.
4. Resolver el proveedor existente y consultar antecedentes activos comparables.
5. Deduplicar contra SOS Contador.
6. Mostrar el borrador y esperar aprobación explícita.
7. Crear desde el borrador congelado.
8. Verificar el detalle, la aparición en el período y el estado activo.

Crear el borrador:

```powershell
python scripts/sos_contador_api.py compra draft `
  --source <comprobante.pdf> `
  --cuit-trabajo <cuit_trabajo> `
  --preview-format markdown
```

Después de la aprobación:

```powershell
python scripts/sos_contador_api.py compra create `
  --draft-id <id_borrador> `
  --cuit-trabajo <cuit_trabajo> `
  --confirm
```

Se pueden pasar varios `--source`, pero cada uno produce un candidato independiente. No unir archivos salvo que sean páginas o vistas complementarias del mismo comprobante. Si representan comprobantes diferentes, crear y confirmar cada compra por separado.

## Extracción mínima

Aplicar esta jerarquía:

1. Extraer primero el texto digital embebido cuando el PDF lo contenga.
2. Para imágenes o escaneos, si el agente dispone de visión, producir una lectura estructurada y pasarla mediante `--document-json` o `--document-file`.
3. Ejecutar OCR local como contraste independiente cuando esté disponible. Tesseract prioriza español (`spa`) y utiliza inglés (`eng`) únicamente como fallback cuando español no está instalado.
4. Aplicar validaciones determinísticas de CUIT, identidad, alícuotas, sumas y total antes de construir el payload.

Si el agente no dispone de visión, el OCR puede ser la fuente primaria, pero no reemplaza las validaciones ni la revisión del borrador. Si no existe ninguna extracción confiable, detenerse y corregir la configuración; no completar campos fiscales por inferencia a partir de una lectura incompleta.

Cuando la extracción automática y la lectura estructurada difieren en un campo fiscal, el borrador queda en `verificar` y conserva ambos valores. Revisar el comprobante original y volver a preparar el borrador declarando únicamente los campos resueltos:

```json
{
  "numero": 78,
  "total": 357.00,
  "_reviewed_conflicts": ["numero"]
}
```

`_reviewed_conflicts` no acepta una confirmación global ni campos desconocidos. Incluir un campo solo después de haber decidido su valor contra la fuente original. Las discrepancias revisadas permanecen como advertencia trazable en el borrador.

Por comprobante, extraer:

- fecha
- tipo, letra, punto de venta y número
- nombre y CUIT del proveedor
- neto e IVA por cada alícuota presente
- no gravado, exento y otros conceptos cuando estén identificados
- percepción de IIBB y jurisdicción, si corresponde
- total
- archivo de origen

La fecha extraída de una línea rotulada como `Fecha` tiene prioridad sobre fechas accesorias como inicio de actividades. El body de la API siempre usa `YYYY-MM-DD` en `fecha` y `fechaiva`.

Conservar el código fiscal de origen además de `fcncnd` y letra. Para tique factura A (`081`), verificar primero la configuración del proveedor por PV según [capabilities-and-verification.md](capabilities-and-verification.md). Con esa configuración se comprobó una carga mediante el helper que conserva `081` en el Libro IVA, aunque su body no transporte un campo de subtipo. Un total correcto y un ID creado no bastan para validar su tipo fiscal; el importador de planillas requiere su propia verificación.

## Correcciones estructuradas

Cuando la lectura automática no sea suficiente, aportar una corrección JSON por cada `--source` mediante `--document-json` o `--document-file`. No combinar ambas opciones. La cantidad de correcciones debe coincidir con la cantidad de fuentes.

Los importes admiten cero numérico explícito o una cadena como `"0.00"`; un valor vacío sigue siendo un dato faltante, no un cero. Si se reemplaza `idcuenta` o `idcentrocosto`, la vista previa solo reutiliza el nombre histórico cuando corresponde al mismo ID. En otro caso muestra el ID seleccionado: resolver su nombre en el catálogo antes de presentar la propuesta comercial. No interpretar el nombre de un antecedente como prueba de la cuenta del body congelado ni reutilizar sin revisión una vista previa generada por una versión anterior.

Ejemplo genérico:

```json
{
  "fecha": "2026-02-03",
  "proveedor_cuit": "<cuit_proveedor>",
  "fcncnd": "F",
  "letra": "A",
  "puntoventa": 2,
  "numero": 77,
  "neto_21": 100.00,
  "iva_21": 21.00,
  "neto_10_5": 200.00,
  "iva_10_5": 21.00,
  "percepcion_iibb": 15.00,
  "total": 357.00
}
```

Campos monetarios admitidos: `neto_0`, `neto_10_5`, `neto_21`, `neto_27`, `iva_0`, `iva_10_5`, `iva_21`, `iva_27`, `nogravado`, `exento`, `percepcion_iibb`, `otros` y `total`.

## CUIT y resolución del proveedor

Para todo CUIT extraído por OCR:

1. normalizarlo a 11 dígitos;
2. validar el dígito verificador argentino;
3. recién entonces buscarlo en el maestro.

Un CUIT inválido no demuestra que falte el proveedor. No crear proveedores automáticamente desde un OCR dudoso. Si el proveedor no puede resolverse de forma única, el candidato queda para verificar y no se construye un payload ejecutable.

Un maestro creado por API puede existir con rol cliente y no aparecer en el selector web de proveedores. Buscar por CUIT antes de repetir el alta; comprobar y completar el rol del mismo registro según [capabilities-and-verification.md](capabilities-and-verification.md).

## Antecedentes contables

Consultar entre una y tres compras activas recientes del mismo proveedor. Reutilizar `idcuenta`, `idcentrocosto` e `idprovinciaiibb` solo cuando los antecedentes disponibles sean consistentes y comercialmente análogos.

Nunca copiar desde antecedentes:

- fecha
- numeración
- importes
- CAE
- estado de baja o archivo

Si los antecedentes discrepan, el borrador debe requerir verificación en lugar de elegir un ID por mayoría o por orden de aparición.

## Alícuotas, descuentos y tributos

Conservar cada alícuota en una imputación separada. No reducir una compra multialícuota a un único neto o IVA.

Reglas para descuentos:

- si el comprobante informa un descuento asociado a una alícuota, aplicarlo al neto de esa alícuota;
- si el neto gravado impreso ya refleja el descuento, usar ese neto final y mantener `descuento=0` para evitar duplicarlo;
- si existe un descuento global que no puede distribuirse con evidencia entre varias alícuotas, marcar el candidato para verificar.

Una percepción identificada como IIBB se registra con identificador `percepcioniibb` y conserva `idprovinciaiibb`. Un renglón genérico de “otros tributos” no se clasifica automáticamente: el borrador debe quedar para verificar hasta que se indique explícitamente si corresponde a no gravado, exento, percepción de IIBB u otra percepción. Cuando dos renglones repiten el mismo importe agregado, no sumarlos dos veces.

## Deduplicación

Consultar `POST /compra/consulta` con fechas ISO y abrir detalles con `GET /compra/detalle/:id` cuando haga falta. Si una consulta devuelve 50 filas, tratarla como potencialmente truncada y subdividir el período.

Clave de identidad:

- CUIT del proveedor
- `fcncnd`
- letra
- punto de venta
- número

Comparar además fecha, importes por alícuota, tributos y total redondeado a centavos:

- identidad e importes coincidentes: `ya_cargado`;
- identidad coincidente con importes distintos: `verificar`;
- sin coincidencia: `pendiente`.

La deduplicación se ejecuta al preparar el borrador y se repite inmediatamente antes del `PUT`. Así se evita duplicar un comprobante si otro proceso lo registró entre la aprobación y la creación.

## Payload congelado

El borrador almacena el body completo, un `uniqueid` UUID v4 y un hash SHA-256 del JSON normalizado. `compra create` valida el hash y envía ese mismo body, sin recalcular cuentas, importes, fechas ni identificadores después del OK.

Forma ilustrativa:

```json
{
  "fecha": "2026-02-03",
  "fechaiva": "2026-02-03",
  "idclipro": "<id_proveedor>",
  "cuitclipro": "<cuit_proveedor>",
  "fcncnd": "F",
  "letra": "A",
  "puntoventa": 2,
  "numero": 77,
  "numerohasta": 77,
  "obtienecae": false,
  "idprovinciaiibb": "<id_provincia>",
  "idcentrocosto": "<id_centro_costo>",
  "descuento": 0,
  "uniqueid": "<uuid_v4>",
  "controlainconsistencia": 0,
  "imputaciones": [
    {
      "cuid": "<id_cuenta>",
      "imputa": [
        {"i": "neto", "a": 21.0, "v": 100.0},
        {"i": "neto", "a": 10.5, "v": 200.0},
        {"i": "percepcioniibb", "a": 0, "v": 15.0}
      ]
    }
  ],
  "productos": []
}
```

## Verificación posterior

Después de crear:

1. consultar `GET /compra/detalle/:id`;
2. confirmar proveedor, tipo, letra, punto de venta y número;
3. confirmar `cabecera.fecha`, todas las bases e IVA por alícuota y la percepción de IIBB;
4. reconciliar el total redondeando a centavos;
5. confirmar el ID en `POST /compra/consulta` para el período de la fecha persistida;
6. confirmar que no tenga `cancelado=1`, `fechabaja` ni pertenezca a una sección de anulados.

Una respuesta exitosa de creación no reemplaza esta verificación. En particular, la fecha operativa para la consulta del período es `cabecera.fecha`; otros campos de fecha pueden quedar vacíos en el detalle.

Cuando el trabajo incluya impuestos o imputación contable, consultar además `libroiva.compras` para el período y `asiento.get` con el ID de compra. Revisar tipo fiscal, categoría, IVA computable, jurisdicción de percepciones y cuentas efectivas. La cuenta elegida por un antecedente o una importación automática no acredita que la naturaleza y el destino coincidan con la nueva compra.

Este flujo no anula, elimina ni da de baja compras.
