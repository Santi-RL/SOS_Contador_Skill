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

Tomar estas estructuras como punto de partida documental, no como garantía de aceptación. Reemplazar todos los marcadores, ejecutar `--dry-run` y validar IDs contra la CUIT de trabajo.

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

`cliente.create` y `cliente.update`:

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

Comprobar antes del envío que la suma de `fd` sea igual a la suma de `fh`.

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

Omitir `idcuenta` solo cuando se acepte que SOS asigne su valor predeterminado. Para documentos usar preferentemente `compra draft` y `compra create`, que congelan el payload aprobado, repiten la deduplicación antes de escribir y verifican el resultado. Verificar siempre la fecha persistida, todas las alícuotas y que el comprobante permanezca activo.

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
