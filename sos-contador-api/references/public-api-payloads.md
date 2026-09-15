# Cuerpos documentados de la API pública

## Índice

- [Reglas](#reglas)
- [Cuenta y configuración](#cuenta-y-configuración)
- [Maestros](#maestros)
- [Consultas](#consultas)
- [Asientos](#asientos)
- [Cobros y pagos](#cobros-y-pagos)
- [Compras](#compras)
- [Ventas](#ventas)

## Reglas

Tomar estas estructuras como punto de partida documental de desarrollo, no como garantía de aceptación ni permiso operativo. Las escrituras genéricas requieren preview en desarrollo y ejecución en validación controlada autorizada; en operativo usar la receta del helper exacto. Reemplazar todos los marcadores, ejecutar `--dry-run` y validar IDs contra la CUIT de trabajo.

No copiar estos ejemplos con valores reales a archivos públicos. Generar `uniqueid` nuevos para cada comprobante que lo requiera.

## Cuenta y configuración

`auth.register`:

```json
{"usuario":"usuario@example.com","password":"<contraseña>"}
```

`cuit.create`:

```json
{
  "cuit": "30000000000",
  "razonsocial": "Empresa Demo S.R.L.",
  "idperfil": "<id_perfil>",
  "idcondicioniva": "<id_condicion_iva>",
  "idprovincia": "<id_provincia>",
  "categoria": "D",
  "codactividad": "<codigo_actividad>"
}
```

`cuit.mobile.update`:

```json
{
  "configurado": false,
  "idcuenta": null,
  "idcentro": null,
  "puntoventa": null,
  "codigoimpresora": null,
  "idimpresora": null,
  "nombreimpresora": null,
  "alicuota": null,
  "etiquetareferencia": null
}
```

## Maestros

`centrocosto.create` y `centrocosto.update`:

```json
{"centro":"Centro de costo Demo"}
```

Este body es documental: el alta observada devolvió `id: 0` sin persistencia comprobada. Volver a consultar `centrocosto.list` antes de repetir o completar por otra vía. Esto no valida la edición.

`cliente.create` (body mínimo de alta):

```json
{
  "cuit": "30000000001",
  "clipro": "Cliente Demo S.A.",
  "idprovincia": "<id_provincia>",
  "idtipocondicioniva": "<id_condicion_iva>",
  "email": "usuario@example.com"
}
```

Usar exactamente `idtipocondicioniva`; las variantes `idcondicioniva` e `idtipo_condicioniva` fueron rechazadas en pruebas reales de clientes.

Este body básico no garantiza el rol de proveedor: se verificó un alta con rol cliente. Antes de volver a crear un tercero ausente del selector de compras, buscarlo por CUIT y comprobar su rol en la web. Seguir el alcance y la corrección puntual documentados en [capabilities-and-verification.md](capabilities-and-verification.md).

No reutilizarlo como actualización parcial de `cliente.update`: se comprobó que los campos omitidos pueden reemplazarse por valores vacíos o predeterminados. La respuesta del listado no alcanza para reconstruir la ficha completa. Para modificar solo la condición fiscal sin perder otros datos, aplicar la ruta de preservación y verificación de la matriz de capacidades; no inventar parámetros de escritura a partir de nombres de controles web.

`grupomodificador.create` y `grupomodificador.update`:

```json
{"grupomodificador":"Grupo Demo","productos":["<id_producto_1>","<id_producto_2>"]}
```

`producto.create` y `producto.update`:

```json
{
  "codigo": "DEMO-001",
  "producto": "Producto Demo",
  "idproductoservicio": "<id_tipo>",
  "idunidad": "<id_unidad>",
  "idcentrocosto": "<id_centro_costo>",
  "idgrupomodi": null,
  "tasaiva": 21.0,
  "precio1": 100.0,
  "precio2": 0.0,
  "precio3": 0.0,
  "precio4": 0.0,
  "precio5": 0.0,
  "costo": 50.0,
  "excluirIIBB": false,
  "memo": "",
  "visible": true
}
```

En productos se comprobó el alta de campos básicos y centro; el listado no expone cuenta de venta/compra ni actividad. Esos valores requirieron configuración web, tras la cual el centro quedó en `null`. Comprobar el resultado final en ambos transportes cuando corresponda; no prometer valores automáticos solo por haberlos enviado. Verificar también la persistencia de `memo`.

`puntoventa.create` y `puntoventa.update`:

```json
{
  "puntoventa": 1,
  "codactividad": "<codigo_actividad>",
  "nombre": "Punto de Venta Demo",
  "domicilio": "Domicilio Demo 123",
  "cbu": ""
}
```

En puntos de venta se comprobó la actualización de `codactividad`, no todos los modos. Preservar los demás valores y comparar la respuesta completa: se observó normalización de `ticket`. No usar un body parcial como si fuera un PATCH garantizado.

## Consultas

`compra.search`:

```json
{"fecha_desde":"2026-01-01","fecha_hasta":"2026-01-31"}
```

`venta.search`:

```json
{
  "fecha_desde": "2026-01-01",
  "fecha_hasta": "2026-01-31",
  "numero_desde": 1,
  "numero_hasta": 100,
  "sucursal": [1],
  "tipo_factura": ["F"],
  "idclipro": ["<id_cliente>"]
}
```

`cuentacorriente.list` publica un body sobre un `GET`, pero declara la operación no implementada:

```json
{
  "CP": "C",
  "fechadesde": "2026-01-01",
  "fechahasta": "2026-01-31",
  "tipo": "T",
  "idclipro": "<id_cliente>"
}
```

`email.send`:

```json
{
  "comprobantes": ["<id_comprobante>"],
  "idcliente": "<id_cliente>",
  "email": "usuario@example.com"
}
```

## Asientos

`asiento.save`:

```json
{
  "fecha": "2026-01-31",
  "memo": "Asiento Demo",
  "idcentrocosto": "<id_centro_costo>",
  "idprovinciaiibb": "<id_provincia>",
  "imputaciones": [
    {"cuid":"<id_cuenta_debe>","fd":"100.00","fh":"0","memo":"Debe"},
    {"cuid":"<id_cuenta_haber>","fd":"0","fh":"100.00","memo":"Haber"}
  ]
}
```

Comprobar antes del envío que la suma de `fd` sea igual a la suma de `fh`. El alta sin `--param id` fue comprobada. Consultar después `asiento.get`, `asiento.list` y los mayores afectados. Un asiento manual no aplica pagos a facturas ni habilita editar un asiento automático. La modificación de un asiento existente no queda validada por el alta.

## Cobros y pagos

`cobro.save` y `pago.save` comparten la forma pública básica:

```json
{
  "fecha": "2026-01-31",
  "idclipro": "<id_cliente_o_proveedor>",
  "idcuenta": "<id_cuenta>",
  "idprovinciaiibb": "<id_provincia>",
  "idcentrocosto": "<id_centro_costo>",
  "memo": "",
  "referencia": "Referencia Demo",
  "imputaciones": [{"fv":"100.00","cuid":"<id_cuenta>"}]
}
```

La forma pública no representa el detalle completo de cheques y retenciones. Para esos casos usar los helpers especializados y su flujo `web-session` validado.

En pagos sencillos, `imputaciones[].cuid` corresponde a la cuenta del medio de pago y `fv` al importe; no colocar allí el ID de una factura. La cabecera puede conservar `idcuenta` aunque el asiento generado debite Proveedores. Verificar la contrapartida en el asiento o mayor, además del detalle del pago. La forma básica no crea una asociación a compras ni garantiza que un anticipo quede contabilizado en su cuenta definitiva; ver [capabilities-and-verification.md](capabilities-and-verification.md).

## Compras

`compra.save` usa `--param id=0` para crear:

```json
{
  "fecha": "2026-01-31",
  "fechaiva": "2026-01-31",
  "idclipro": "<id_proveedor>",
  "cuitclipro": "30000000015",
  "fcncnd": "F",
  "letra": "A",
  "puntoventa": 1,
  "numero": 1,
  "numerohasta": 1,
  "obtienecae": false,
  "idprovinciaiibb": "<id_provincia>",
  "idcentrocosto": "<id_centro_costo>",
  "memo": "Compra Demo",
  "referencia": "archivo-origen.pdf",
  "descuento": 0,
  "uniqueid": "<uuid_nuevo>",
  "controlainconsistencia": 0,
  "imputaciones": [
    {
      "cuid":"<id_cuenta>",
      "imputa":[
        {"i":"neto","a":21.0,"v":100.0},
        {"i":"neto","a":10.5,"v":200.0},
        {"i":"percepcioniibb","a":0,"v":15.0}
      ]
    }
  ],
  "productos": [
    {"id":"<id_producto>","u":7,"fc":1,"fu":100.0,"fa":21.0,"cuid":"<id_cuenta>"}
  ]
}
```

Mantener cada base en una imputación separada según su alícuota. Registrar la percepción provincial identificada como IIBB con `i="percepcioniibb"` y conservar `idprovinciaiibb`; no convertir automáticamente otros tributos genéricos en IIBB. Si el neto ya refleja descuentos, mantener `descuento=0` para no duplicarlos.

El ejemplo con una jurisdicción no cubre percepciones simultáneas de provincias diferentes. No agruparlas bajo `idprovinciaiibb` ni reutilizar un detalle de lectura como body. Consultar la alternativa web y su verificación en [capabilities-and-verification.md](capabilities-and-verification.md).

Omitir `idcuenta` solo cuando se acepte que SOS asigne su valor predeterminado. Para documentos usar preferentemente `compra draft` y `compra create`, que congelan el payload aprobado, repiten la deduplicación antes de escribir y verifican el resultado. Verificar siempre la fecha persistida, todas las alícuotas y que el comprobante permanezca activo.

Para corregir una compra existente, usar su ID comprobado, no `id=0`. Reconstruir el body completo conservando identidad, fecha, tipo, numeración, CAE, jurisdicción, centro y otros campos ajenos al cambio; no enviar el objeto de detalle sin transformar. En el detalle, `imputaciones[].cuid` puede ser el identificador de una línea; el `cuid` de escritura de esta estructura debe contener el **ID de la cuenta**, resuelto desde `idcuenta` y el catálogo.

Se comprobó el cambio de cuenta y netos y la eliminación de una percepción no respaldada. No usar percepciones para compensar redondeos. No tratar `codactividad` como un cambio garantizado: el servidor aceptó una solicitud sin persistirlo. Verificar cuenta de cabecera, cuentas de líneas, actividad, centro e importes después de guardar, con las condiciones de [capabilities-and-verification.md](capabilities-and-verification.md).

## Ventas

`venta.save` está documentada pero aún no fue validada mediante una escritura controlada en este proyecto. Para crear, omitir `--param id`; para modificar, usar `--param id=<id_venta>`.

```json
{
  "idtipo_operacion": 2,
  "fecha": "2026-01-31",
  "idclipro": "<id_cliente>",
  "cuitclipro": "30000000001",
  "idcuenta": "<id_cuenta>",
  "fcncnd": "F",
  "letra": "C",
  "puntoventa": 1,
  "numero": 1,
  "numerohasta": 1,
  "obtienecae": false,
  "fechaiva": "2026-01-31",
  "idprovinciaiibb": "<id_provincia>",
  "idcentrocosto": "<id_centro_costo>",
  "memo": "Venta Demo",
  "referencia": "Referencia Demo",
  "descuento": 0,
  "uniqueid": "<uuid_nuevo>",
  "imputaciones": [{"i":"neto","a":0,"v":100.0}],
  "productos": [{"id":"<id_producto>","u":7,"fc":1,"fu":100.0,"fa":21.0}]
}
```

No solicitar CAE durante la primera validación. Usar `obtienecae=false`, confirmar el borrador o comprobante resultante mediante lectura y recién después evaluar el flujo fiscal.
