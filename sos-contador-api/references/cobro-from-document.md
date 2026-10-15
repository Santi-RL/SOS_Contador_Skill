# Cobranza desde documentos

Usar para preparar un recibo desde PDF, imagen, TXT, CSV, XLSX o XLS mediante lenguaje natural. El contrato de campos está en [cobro-create-and-associate.md](cobro-create-and-associate.md); la ruta habilitada y sus transportes están en [operating-recipes.md](operating-recipes.md#cobranzas). Este flujo no habilita ediciones ni bajas.

## Agrupar las fuentes

Cada orden o recibo independiente requiere su propio borrador. Usar varios `--source` en un solo borrador únicamente para páginas, frente/dorso o anexos que completen el mismo documento.

Separar los archivos si difieren la orden, fecha, facturas referidas, total o conjunto de cheques/retenciones. Si una vista previa fusiona órdenes independientes, detenerse y preparar los borradores separados antes de escribir.

## Preparar y revisar

1. Resolver una CUIT de trabajo única por catálogo. La CUIT del cliente no sustituye la del contribuyente. Si el receptor del documento permite resolverla de forma inequívoca, no pedir de nuevo ese dato.
2. Ejecutar un `cobro draft --preview-format markdown` por grupo documental; el borrador no registra un recibo en SOS.
3. Leer el resultado y resolver únicamente faltantes o ambigüedades reales. No completar banco, cuenta, régimen o factura para hacer cuadrar el total.
4. Mostrar la vista previa y obtener aprobación del resultado exacto.
5. Ejecutar `cobro create --draft-id <id_borrador> --confirm` para cada borrador aprobado, uno por vez. Reutilizar el borrador almacenado, sin volver a extraer el documento.
6. Verificar recibo, movimientos y asociaciones conforme a la receta. Si la creación terminó y la asociación falló, informar el estado parcial y detenerse: no repetir la creación; cualquier reparación requiere su propia propuesta.

## Datos mínimos

| Parte | Datos a resolver |
|---|---|
| Contexto | CUIT de trabajo y contribuyente, distintos de la CUIT de la contraparte. |
| Cabecera | Fecha y cliente identificado por ID, CUIT o nombre inequívoco. |
| Movimiento simple | Cuenta de destino e importe. |
| Cheque | Cuenta de destino, banco, fecha, número e importe. |
| Retención | Cuenta de destino, fecha, régimen e importe. |
| Asociación, si se pidió | Al menos una factura por ID o comprobante visible; contrastar fecha y total cuando estén disponibles. |

Comentarios, centro de costo y número de recibo son opcionales según el contrato. Un dato ausente no autoriza a inventarlo.

## Vista previa obligatoria

Mostrar tablas con:

- **Contexto:** CUIT de trabajo, contribuyente, cliente y su CUIT, fecha, centro y comentarios.
- **Movimientos:** tipo, cuenta de destino, banco o régimen, número, fecha, importe y estado de resolución.
- **Asociaciones:** comprobante, fecha, total y estado de resolución.
- **Totales:** suma del recibo, suma de las facturas a asociar y diferencia, indicando si el caso exige cuadre exacto.

Detenerse si falta la fecha, el cliente o un campo obligatorio del movimiento; si varias cuentas, bancos o regímenes coinciden; si el total esperado difiere de los movimientos; o si no se cumple el cuadre exigido para las asociaciones. Pedir solo el dato necesario para resolver ese punto.

Ejemplos de aclaración:

- «Pude extraer el cheque, pero no resolví su banco de forma única. ¿Cuál es el banco exacto?»
- «Pude extraer la retención, pero falta el régimen numérico que acepta SOS.»

## Extracción y aprendizaje

`cobro draft` consulta primero los perfiles privados existentes según [local-document-profiles.md](local-document-profiles.md), antes de recurrir al parser genérico. Operativo solo consume esos perfiles. Crear, editar o probar un perfil requiere desarrollo explícito; una extracción fallida no autoriza a diseñar reglas nuevas.

Los perfiles y formatos particulares permanecen en el hogar privado, fuera del repositorio público. Su ubicación no habilita ejecución ni publicación automática. Si hace falta OCR y no está disponible una extracción confiable, detenerse y resolver esa carencia sin inventar campos.

Después de un borrador normal, continuar con su revisión o aclaraciones. No inspeccionar código ni diseñar un camino alternativo durante la operación. Ante variante sin receta, aplicar la parada y transición de modo definidas en `SKILL.md`.

Las bajas y anulaciones de comprobantes están bloqueadas en todos los modos actuales, incluso ante un pedido de cancelación. Ese pedido requiere un desarrollo y una validación separados; la aprobación de este recibo no habilita ese trabajo.
