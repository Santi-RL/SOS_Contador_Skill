# Capacidades comprobadas y verificación

Leer para adaptar el plan de cuentas, configurar conceptos, reclasificar comprobantes o registrar pagos y asientos. Complementa el catálogo; no agrega endpoints ni convierte una función web en capacidad de la API pública.

## Alcance de la evidencia

Comportamientos contrastados en operaciones autorizadas y lecturas independientes, revisados en agosto de 2026. Se describe el alcance probado, no una garantía para toda instalación o variante. Una respuesta exitosa, un ID o un `--dry-run` no prueban que un campo se haya persistido. Los ejemplos son genéricos; la evidencia concreta permanece en el hogar privado.

## Matriz de decisión

| Necesidad | API y alcance comprobado | Límite y siguiente paso |
|---|---|---|
| Consultar el plan de cuentas | `cuentacontable.list`: IDs, nombres, códigos `arbol` y rubros. | El catálogo público no ofrece alta o edición de cuentas. La distribución entre costo, administración y otras funciones y la categoría fiscal requieren consultar la configuración web; no se deducen del nombre. |
| Crear un tercero para compras | `cliente.create` crea el maestro y `cliente get --cuit` permite comprobar su identidad. | El body básico documentado creó un tercero con rol **cliente**, no proveedor. Si no aparece en el selector de compras, no repetir el alta: localizar el mismo maestro en Clientes y cambiar su rol a proveedor por la web autorizada. Verificar luego el listado de Proveedores. Esto no valida un parámetro API para cambiar el rol. |
| Actualizar la condición fiscal de un tercero | `cliente.update` persistió `idtipocondicioniva`; la condición actual también pasó a verse en cabeceras y libros de compras anteriores, sin cambiar sus importes ni asientos en el caso verificado. | **El body mínimo no es un PATCH seguro:** reemplazó rol, domicilio, observaciones, lista de precios y vendedor omitidos; también cambió la provincia predeterminada visible para importaciones. `cliente get` no expone toda esa configuración. Antes de escribir, conservar la ficha completa; si la ruta API no permite preservar sus campos con un body validado, usar la edición web puntual autorizada. No repetir el body mínimo para reparar sus efectos. |
| Auditar compras y su clasificación fiscal | `libroiva.compras`, con `ejercicio`, `anio` y `mes`, devolvió `libro` y `total`; se contrastaron sus identidades y fechas con `compra.search` y `compra.get`. Expone categoría `creditofiscal`, IVA computable/no computable y percepciones por jurisdicción. | Verificar el período efectivo y la cobertura. `neto` puede incluir importes no gravados: usar `gravado_total` y los campos por alícuota para comparar bases. Los totales internos pueden diferir un centavo de la suma de comprobantes redondeados. El libro informa el tratamiento registrado, no su procedencia fiscal ni la existencia del original. |
| Consultar el asiento automático de una compra | `asiento.get` usando el ID de compra devolvió cabecera e imputaciones, incluidas las cuentas efectivas de IVA y Proveedores. | Es una lectura, no una autorización para editar el asiento automático. Una nota de crédito recibida puede acreditar IVA Débito Fiscal; comprobar el efecto fiscal conjunto, no exigir que revierta la misma cuenta de IVA de la factura. |
| Consultar actividades | `actividad.list` busca en el catálogo general. | No prueba cuáles están incorporadas al contribuyente. El catálogo no contiene una operación para agregar actividades a su configuración general. El alta en SOS tampoco acredita inscripción en ARCA. |
| Corregir una compra existente | `compra.save` con su ID permitió modificar cuenta e imputaciones, corregir netos y retirar una percepción no respaldada. | No es un PATCH mínimo. Conservar la identidad y los campos ajenos al cambio. Se observó que `codactividad` enviado no se persistía; comprobarlo y completar solo ese campo por la ruta autorizada. |
| Registrar percepciones de distintas jurisdicciones | `compra.get`, `asiento.get` y `libroiva.compras` permiten contrastar cuenta, importe y jurisdicción efectiva. | El helper básico no representa varias jurisdicciones. Se verificó la carga web mediante **Cargar datos avanzados → Imp y Perc**, eligiendo cuenta e importe para la percepción adicional. No sumar ambas en el campo provincial único ni inferir de esta prueba un body API nuevo. |
| Separar percepción IVA de un tributo no recuperable | Las lecturas de compra y asiento distinguen `percepcioniva` y la cuenta efectiva de un importe avanzado `percepcionotra`. | Se verificó el campo web **Percepción IVA** junto con **Imp y Perc**, seleccionando **Egresos - Otros Impuestos** para el gasto no recuperable. El asiento reconoció el gasto, pero el Libro IVA lo agregó a `no_gravado`, no a `imp_otr`: revisar la presentación fiscal antes de dar por correcta una exportación. Esto no valida un nuevo body de escritura API. |
| Reclasificar ventas existentes | `venta.get` y `venta.search` permiten verificar el resultado. | Las acciones web de cambio de cuenta, actividad y centro se comprobaron; esto no valida `venta.save`. Su escritura pública sigue pendiente de validación específica. |
| Crear un centro de costo | `centrocosto.list` permite comprobar su existencia. | `centrocosto.create` con el body publicado devolvió `id: 0` sin alta comprobada. Tratar como resultado no confirmado, volver a listar y no repetir el alta a ciegas. La creación web fue efectiva. La edición y la baja públicas no quedan validadas por esa prueba. |
| Crear un concepto de servicio | `producto.create` permitió guardar código, descripción, tipo, unidad, IVA, precios y centro; `producto.list` los devuelve. | La cuenta de venta/compra y la actividad del concepto no están cubiertas por ese body ni por el listado. Se configuraron en la web. Una edición web posterior dejó el centro en `null`; verificar nuevamente y seleccionarlo en cada comprobante cuando no exista persistencia comprobada. No asumir que `memo` se conservó. |
| Cambiar la actividad de un punto de venta | `puntoventa.update` permitió persistir `codactividad`, comprobado con `puntoventa.list`. | No trasladar esa conclusión al alta, baja o todos los campos. Comparar también `ticket`, sucursal, CBU y domicilio: se observó normalización de `ticket` al guardar. No cambiar un punto de venta compartido sin delimitar las operaciones afectadas. |
| Registrar un pago bancario sencillo | `pago create` / `pago.save` permitió una salida bancaria; verificar con `pago.get`, listado y asiento. | `idcuenta` de cabecera puede persistir aunque el asiento automático use Proveedores. `imputaciones[].cuid` identifica la cuenta del medio de pago; `fv`, su importe. No prueba aplicación a facturas ni una contrapartida contable distinta. |
| Asociar un pago a una compra | El detalle/listado sirve para verificar el pago. | El body público básico no demostró esa asociación y no hay helper de asociación de pagos equivalente al de cobranzas. Se completó por la web y se verificó al recargar. Un memo no crea una asociación. |
| Crear un asiento de reclasificación | `asiento.save` sin ID permitió crear un asiento manual con `cuid`, `fd`, `fh` y memo; `asiento.get` y `asiento.list` lo verifican. | La modificación y la baja no se validan por haber probado un alta. Una reclasificación no modifica por sí sola la cuenta corriente comercial ni debe generar otra salida bancaria. |
| Consultar mayor y sumas y saldos | Se obtuvieron reportes con JWTC y se contrastaron movimientos y saldos. | En `mayor.list` se observaron filas de todo el ejercicio pese a pedir fechas más estrechas y errores en determinadas cuentas. Filtrar las filas recibidas por fecha y cuenta, comprobar paginación/completitud y no interpretar un error como saldo cero. No presumir que otros reportes respetan todos sus filtros sin verificarlo. |

## Elegir el transporte sin perder los límites

1. Buscar el helper y la operación pública apropiados. No inventar un endpoint de escritura por analogía con un listado.
2. Si hay una ruta HTTP `web-session` validada para la necesidad, usarla dentro de la autorización vigente. Un fallo de autenticación no justifica reutilizar cookies del navegador.
3. Para alta/configuración de cuentas, actividades del contribuyente, configuración contable del producto y asociación de pagos, la implementación actual no ofrece un helper HTTP validado suficiente. También puede resultar insuficiente para un campo que la API no persiste o para las variantes de maestro y percepciones indicadas en la matriz. En esos casos se permite el navegador visible autorizado o la intervención del usuario, limitado al campo o acción pendiente. No hacer pruebas especulativas de endpoints internos.
4. Leer el formulario y confirmar contribuyente, registro y selección antes de guardar. No reutilizar índices de filas después de ordenar, filtrar o cambiar de pantalla. Usar las capacidades permitidas por la herramienta de navegador, sin extraer credenciales ni tomar sesiones por fuera de ella.
5. Reabrir el formulario o recargar y consultar por API lo que esta exponga. Si no se dispone de verificación suficiente, informar el alcance pendiente.

El permiso ya concedido para el mismo cambio y transporte no se pide otra vez. Un nuevo efecto contable, un conjunto mayor de documentos o una acción destructiva sí requiere delimitar autorización. Consultar también [safety-and-storage.md](safety-and-storage.md).

## Preparar y comprobar una reclasificación

Conservar una lectura previa privada y definir exactamente qué campos se modificarán. Consultar el original cuando se corrijan importes o tributos. La respuesta de detalle no es por sí sola un payload de escritura: transformar sus campos según [public-api-payloads.md](public-api-payloads.md), sin confundir el ID de una línea con el ID de su cuenta.

Comparar después:

- identidad, proveedor/cliente, fecha, tipo, letra, punto de venta, número, CAE y estado activo;
- cuenta de cabecera y cuenta de cada imputación, actividad y centro;
- netos e IVA por alícuota, tributos efectivamente documentados y total redondeado a centavos;
- jurisdicción de IIBB y demás campos que debían permanecer iguales, aunque se haya usado una acción de cambio de cuenta;
- presencia única en el período y, cuando el cambio afecta el resultado contable, asiento o mayor correspondiente.

SOS puede devolver IVA con más de dos decimales. Usar aritmética decimal y comparar a centavos por comprobante antes de conciliar un agregado. No crear percepciones ficticias, positivas o negativas, para absorber redondeos. Un total mensual coincidente tampoco prueba que todas sus partidas estén bien clasificadas.

También puede persistir un residual de `0,0001` dentro de una percepción para balancear importes internos a cuatro decimales. Si el original informa percepción cero y el neto, el IVA y el total coinciden a centavos, tratar ese residual como una discrepancia técnica, no como un tributo documentado ni un crédito aprovechable. Comprobar `compra.get`, `asiento.get` y `libroiva.compras`; documentar el límite y no regrabar toda la compra únicamente para eliminar una diezmilésima sin efecto contable material.

En la carga resumida web, el botón que muestra el IVA abre **Ingrese valor de IVA**, pero recalcula inversamente el neto: no es una sustitución independiente del impuesto. Si se prueba ese control en un borrador, comprobar también la base y revertir cualquier cambio no buscado antes de guardar. No cambiar la alícuota, el neto o un tributo para ocultar una diferencia del original. Si no hay un mecanismo suficiente validado, separar las correcciones verificadas de la diferencia pendiente.

Para auditorías, cruzar también originales y registros en ambos sentidos: documento sin compra y compra sin documento. Una transferencia acredita un pago, pero no sustituye el detalle fiscal de la factura. Fotografías diferentes del mismo comprobante no son compras adicionales. Si falta el detalle de artículos o el destino, separar «importes verificados» de «imputación validada». Seguir [auditoria-compras.md](auditoria-compras.md) para el inventario, la normalización documental, los estados y el cierre del período.

Al cambiar la condición fiscal del maestro, no interpretar la condición devuelta en una cabecera histórica como una copia inmutable de la situación del emisor a esa fecha. Contrastar tipo, letra, neto, IVA, original y asiento: una factura C anterior no adquiere IVA por el cambio actual del proveedor. En el libro, `codigoAFIP` cambió de 6 a 1 junto con MONO a RINS, mientras `codigocomprobanteafip` permaneció en 001: no confundir ambos campos. Si un Libro IVA devuelve vacío pese a compras conocidas, repetir la lectura de ese período de forma aislada y verificar fechas y cobertura antes de concluir que faltan registraciones; una relectura recuperó filas sin modificar comprobantes. No atribuir ese resultado al formato del mes ni a la concurrencia sin una prueba que lo demuestre.

### Tiques factura y configuración por punto de venta

Los códigos de origen `081` (tique factura A) y `001` (factura A) no son equivalentes. La [ayuda oficial de SOS](https://ayuda.sos-contador.com.ar/menu-inicio/Compras/c%C3%B3mo-cargar-compras-con-ticket-u-otros-tipos-de-comprobantes-que-no-sean-f) indica que el tipo de emisión se configura en la ficha del proveedor. Se comprobó la escritura web de **Tickets A y B** (valor `81`) como alternativa para puntos de venta concretos, conservando el tipo genérico y las demás alternativas. No confundir esa opción con **Tique** (`83`).

Para corregir esta configuración compartida:

1. Validar código, proveedor y PV con los originales. Relevar compras del proveedor y libros de los períodos potencialmente afectados; autorizar ese alcance antes de guardar. No inferir que todos sus puntos de venta emiten el mismo tipo.
2. Guardar la ficha completa y las lecturas previas de compras, asientos y libros. Si ni la API ni `web-session` cubren esos campos, editar la ficha web con la herramienta de navegador permitida. Seleccionar la alternativa y su PV en los controles visibles; no reemplazar la configuración genérica sin necesidad. Los controles observados se identifican como `comprobantecompra_alt` y `sucursal_alt`, con variantes numeradas para las alternativas adicionales; volver a inspeccionarlos en cada sesión.
3. Tras guardar, reabrir y comparar todos los campos. Una respuesta API limitada del tercero no verifica sus alternativas de emisión.
4. Volver a leer los libros y comparar por identidad fiscal, ignorando solo el orden de las filas. En el alcance probado, la configuración corrigió `codigocomprobanteafip` de compras anteriores sin reescribir sus importes ni sus asientos; otros documentos del mismo PV ya estaban en `081` y permanecieron iguales. Verificar también los PV no modificados. Este cambio no presenta ni rectifica declaraciones fiscales anteriores.
5. Para una nueva compra autorizada, el helper `compra draft/create` con `F`, letra `A` y el PV configurado produjo `081` en `libroiva.compras`. Verificar allí el código, además del detalle y asiento. Esto no valida un campo público de escritura `tipocomprobante=81`, ni prueba otros subtipos o el importador de planillas.

El detalle `compra.get` puede conservar `cabecera.tipocomprobante=1` aunque el libro devuelva `codigocomprobanteafip=081`. Tampoco basta `tiquet` aislado para inferir el código exportado. No corregir esas cabeceras por mera discrepancia; contrastar original y libro. El importador de planillas conserva su normalización en `afip_type_rule`: no suponer que transporta por sí solo el subtipo. Si el libro pierde el código original, detener nuevas cargas por esa ruta y resolver la configuración sin duplicar compras.

`tipocomprobante=201` no es una variante interna de la Factura A común: corresponde a **Factura de Crédito Electrónica MiPyMEs (FCE) A**. Si el original indica `001`, el listado visible y `libroiva.compras` conservan `001`, pero `compra.get` devuelve `201`, registrar la discrepancia de la cabecera y no interpretar el documento como FCE. No regrabar una compra completa únicamente para normalizar ese campo mientras la ruta de actualización sea `limited` y el código fiscal efectivo del libro sea correcto; una corrección requiere delimitar los demás campos que se volverían a guardar y verificar el libro después.

### Otros controles de comprobantes

El campo resumido rotulado **No Grav** persistió como `nogravado`. **Total Otro** con alícuota cero persistía como `neto` al 0%; no son equivalentes en el Libro IVA. Al trasladar un importe, vaciar efectivamente el campo anterior y comprobar la recalculación antes de guardar: el formulario puede reconstruir controles al perder el foco. Revisar los valores resultantes, no dar por aplicada una modificación por la sola ejecución del comando de entrada.

Una percepción adicional cargada por la web puede aparecer como `percepcionotra` en `compra.get` aunque su cuenta y el Libro IVA la clasifiquen como IIBB de una jurisdicción concreta. Se observó también `montohaber` negativo en esa respuesta de detalle, mientras el asiento automático mostraba el débito correcto y estaba balanceado. No duplicar el importe ni reconstruir el asiento sumando indiscriminadamente ambos campos del detalle; contrastar con `asiento.get` y con las columnas provinciales del libro.

El identificador `percepcionotra` tampoco demuestra por sí solo un crédito impositivo: una cuenta de gasto cargada desde **Imp y Perc** puede usarlo. Verificar cuenta, rubro, asiento y casillero del libro por separado. No elegir una cuenta de activo por su nombre tributario cuando el cargo no sea recuperable; si la cuenta de gasto altera la presentación fiscal, documentar el límite sin declarar concluida esa parte del control.

La ficha web del tercero informa que las modificaciones manuales o masivas de comprobantes actualizan ciertos valores predeterminados para importaciones futuras, con prioridad sobre la configuración general de la CUIT. Al definir reglas por proveedor, revisar la sección de importaciones de su ficha y no prometer automatismos a partir de una cuenta guardada. Esa indicación de la interfaz no demuestra que toda escritura API actualice los mismos valores. Tampoco cambiar globalmente la categoría de crédito fiscal de una cuenta compartida para corregir una sola compra sin revisar su alcance.

Ante una respuesta ambigua o una discrepancia: detener las escrituras, consultar el estado real y evitar recrear comprobantes. No repetir una mutación hasta determinar si la anterior tuvo efecto. La reparación debe limitarse al cambio autorizado, con una nueva vista previa si aparece otro efecto material.

## Pagos, anticipos y asientos automáticos

Comprobar el banco de origen con el débito del extracto, no con el banco receptor que figura en el cupón del proveedor. Conservar por separado la fecha del comprobante y la fecha de contabilización bancaria si difieren.

Cuando el objetivo sea registrar un anticipo, revisar el asiento generado por el pago. Si el sistema debita Proveedores, cambiar `idcuenta` en la cabecera no demuestra que cambió esa contrapartida. No volver a registrar la salida bancaria. Si corresponde y está autorizado, preparar un asiento manual compensatorio —por ejemplo, Debe Anticipos / Haber Proveedores— y verificar que el efecto combinado sea el previsto y que Banco no se haya duplicado. No intentar editar directamente un asiento automático.

El registro del pago, su asociación a una factura, la reclasificación del mayor y la conciliación del saldo comercial son resultados distintos. Verificar cada uno solo cuando esté incluido en la tarea; no declararlos resueltos por la mera existencia del pago o asiento.

## Reglas contables reutilizables frente a reglas particulares

Para una operatoria nueva, revisar por separado ingreso, costo directo, gasto interno, activo/anticipo, impuestos, actividad y centro. Vincular el costo al trabajo documentado; el proveedor o una descripción amplia no bastan para generalizar su destino. No descontar automáticamente los costos subcontratados del ingreso ni convertir la calificación contable de un costo en una conclusión sobre el crédito fiscal.

Guardar cuentas concretas, relaciones con clientes/proveedores y criterios aprobados en las [instrucciones privadas del contribuyente](taxpayer-instructions.md). Los hechos de una factura, un plan o una fecha de entrega no deben convertirse en reglas universales de esta skill.
