# Auditoría de contratos y lecturas API — septiembre de 2026

Referencia de desarrollo. Fuente: [colección oficial de Postman](https://documenter.getpostman.com/view/1566360/SWTD6vnC?version=latest), descargada completa el 05/09/2026 desde el enlace estructurado `prefetch` de su HTML público. No requiere navegador, API key de Postman ni credenciales SOS. La descarga contiene ejemplos y valores de entorno: conservarla en desarrollo privado, sin copiarla al repositorio.

## Catálogo completo, contratos incompletos

La colección contiene **71 solicitudes y 70 combinaciones únicas de método/ruta**: `cuit/credentials/:idcuit` aparece en dos grupos. Todas están representadas en el catálogo local. No se encontraron endpoints adicionales publicados para crear cuentas contables, incorporar actividades al contribuyente, asociar pagos o detallar cheques/retenciones en el body básico de cobros. Esto significa «no documentado en esta colección», no «imposible en la API».

Se compararon métodos, rutas, multiplicidad y queries; se inspeccionaron los campos de los ejemplos de body. Cuatro rutas de escritura locales admiten omitir `:id` (`asiento`, `cobro`, `pago`, `venta`), mientras el URL publicado lo muestra. Mantenerlas como variantes explícitas con su evidencia previa; esta auditoría no ejecutó escrituras ni amplía su validación. En `mayor` la colección omite autenticación explícita, pero el uso de JWTC tiene evidencia anterior: no convertir esa omisión en permiso de acceso anónimo.

La documentación llama `pagina` a un «número de página» y usa la descripción de compras también en cobros, recibos y pagos. Los ejemplos no sustituyen la comprobación del comportamiento real.

## Hallazgos comprobados en compras

En un mismo período se contrastaron `compra.search`, `compra.list`, listado HTTP interno y Libro IVA Compras. Coincidieron los conjuntos de comprobantes, sus identidades y los importes de los listados; también se obtuvo detalle y asiento de un caso. La evidencia concreta permanece en el expediente del contribuyente.

**Paginación:** `compra/consulta` acepta `pagina` y `registros`, aunque sus queries están ausentes en Postman. Se incorporaron al catálogo como parámetros observados. En `compra/consulta` y `compra/listado`, `pagina` se comportó como **posición inicial desde 1**, no como número de página: con tamaño 2, las posiciones 1 y 2 comparten una fila. En la consulta por rango, posiciones 1, 11, 21 y 31 con tamaño 10 recuperaron todo el conjunto, sin duplicados; una consulta posterior quedó vacía. No extrapolar a otros módulos.

La respuesta no incluye un total ni metadatos de paginación. Una página corta no basta para demostrar la cobertura en una variante nueva: contrastar contra un conteo independiente, vigilar IDs repetidos, orden y registros ajenos al período. No cambiar los helpers operativos de recorrido hasta incorporar estas comprobaciones y tests. La subdivisión temporal vigente sigue siendo conservadora, pero puede sustituirse por un recorrido de posiciones comprobado en D05.

**Identidad:** en el listado HTTP de compras observado, `cuitemisor` correspondía al contribuyente y `cuitreceptor` al proveedor. No inferir el rol por esos nombres internos: contrastar con `clipro.cuit` de la API y `cuit` del Libro IVA. El libro no usa el ID de compra como clave; comparar CUIT del proveedor, F/NC/ND, letra, PV y número.

**Coste:** una consulta API de rango recibió aproximadamente 14 kB de JSON frente a 118 kB del listado XML expresado en UTF-8, con tiempos observados de 0,77 y 1,37 segundos, respectivamente, sin contar autenticación. Es una muestra, no un benchmark general ni una medición de tokens. El XML incluye muchos campos adicionales; escoger la respuesta más pequeña que conserve la información necesaria. Para análisis fiscal, detalle, asiento y Libro IVA aportan datos que el listado no contiene.

## Transporte que corresponde investigar

| Trabajo | Estado tras la auditoría | Siguiente acción |
|---|---|---|
| Listar y cruzar compras por rango | API suficiente en el caso contrastado; queries y desplazamiento observados. | D05: reemplazar subdivisión por recorrido acotado de posiciones, con deduplicación, parada y cobertura comprobada. |
| Obtener clasificación, impuestos y asiento de una compra | API de detalle + asiento + Libro IVA disponibles. | Usar cada lectura para sus campos; no cargar HTML por defecto ni asumir que el listado contiene todo. |
| Cobranzas por rango e identidad visible | API pública solo publica períodos relativos; el helper actual usa HTTP directo. | D02/D03: hace falta un caso positivo para comparar numeración, medios, asociaciones y cobertura. Los períodos vacíos contrastados no validan esa equivalencia. |
| Registro de venta por API frente al helper HTTP | Endpoint publicado; variante de escritura pendiente. | D01: body y simulación; prueba real propia antes de sustituir el transporte. |
| Cheques, retenciones y asociaciones | No hay un contrato público completo en los ejemplos inspeccionados. | Conservar las rutas HTTP validadas; investigar contratos en desarrollo, sin inferir bodies desde controles UI. |
| Roles de terceros y configuración compartida | Los ejemplos publicados no agregan los campos faltantes ya identificados. | D06–D10: delimitar un campo y preservar el resto antes de una prueba controlada. |

`web-session` es HTTP sin navegador. Sustituirlo por API pública es una decisión por variante y campos necesarios; el uso histórico del navegador no acredita una limitación de la API.

## Repetir la comparación documental

Usar [audit_api_contracts.py](../scripts/development/audit_api_contracts.py) con la colección descargada en un directorio privado:

```powershell
python scripts/development/audit_api_contracts.py --work-mode development --collection <coleccion_privada.json>
```

Solo lee archivos; no conecta con SOS ni cambia catálogo o estados. Devuelve JSON por stdout y enumera nombres de campos, sin valores de ejemplo ni tokens. Código 1 señala diferencias de rutas, multiplicidad o queries que requieren interpretación; 0 significa coincidencia en esas dimensiones, no validación operativa. La ampliación observada de queries de `compra.search` aparece deliberadamente como diferencia respecto de Postman. Revisar también `body_parse` y las variantes opcionales; el comparador no demuestra obligatoriedad, semántica ni autenticación.
