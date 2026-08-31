# Capacidades comprobadas y verificación

Leer para adaptar el plan de cuentas, configurar conceptos, reclasificar comprobantes o registrar pagos y asientos. Complementa el catálogo; no agrega endpoints ni convierte una función web en capacidad de la API pública.

## Alcance de la evidencia

Comportamientos contrastados en operaciones autorizadas y lecturas independientes, revisados en agosto de 2026. Se describe el alcance probado, no una garantía para toda instalación o variante. Una respuesta exitosa, un ID o un `--dry-run` no prueban que un campo se haya persistido. Los ejemplos son genéricos; la evidencia concreta permanece en el hogar privado.

## Matriz de decisión

| Necesidad | API y alcance comprobado | Límite y siguiente paso |
|---|---|---|
| Consultar el plan de cuentas | `cuentacontable.list`: IDs, nombres, códigos `arbol` y rubros. | El catálogo público no ofrece alta o edición de cuentas. La distribución entre costo, administración y otras funciones y la categoría fiscal requieren consultar la configuración web; no se deducen del nombre. |
| Consultar actividades | `actividad.list` busca en el catálogo general. | No prueba cuáles están incorporadas al contribuyente. El catálogo no contiene una operación para agregar actividades a su configuración general. El alta en SOS tampoco acredita inscripción en ARCA. |
| Corregir una compra existente | `compra.save` con su ID permitió modificar cuenta e imputaciones, corregir netos y retirar una percepción no respaldada. | No es un PATCH mínimo. Conservar la identidad y los campos ajenos al cambio. Se observó que `codactividad` enviado no se persistía; comprobarlo y completar solo ese campo por la ruta autorizada. |
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
3. Para alta/configuración de cuentas, actividades del contribuyente, configuración contable del producto y asociación de pagos, la implementación actual no ofrece un helper HTTP validado suficiente. También puede resultar insuficiente para un campo que la API no persiste. En esos casos se permite el navegador visible autorizado o la intervención del usuario, limitado al campo o acción pendiente. No hacer pruebas especulativas de endpoints internos.
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

Ante una respuesta ambigua o una discrepancia: detener las escrituras, consultar el estado real y evitar recrear comprobantes. No repetir una mutación hasta determinar si la anterior tuvo efecto. La reparación debe limitarse al cambio autorizado, con una nueva vista previa si aparece otro efecto material.

## Pagos, anticipos y asientos automáticos

Comprobar el banco de origen con el débito del extracto, no con el banco receptor que figura en el cupón del proveedor. Conservar por separado la fecha del comprobante y la fecha de contabilización bancaria si difieren.

Cuando el objetivo sea registrar un anticipo, revisar el asiento generado por el pago. Si el sistema debita Proveedores, cambiar `idcuenta` en la cabecera no demuestra que cambió esa contrapartida. No volver a registrar la salida bancaria. Si corresponde y está autorizado, preparar un asiento manual compensatorio —por ejemplo, Debe Anticipos / Haber Proveedores— y verificar que el efecto combinado sea el previsto y que Banco no se haya duplicado. No intentar editar directamente un asiento automático.

El registro del pago, su asociación a una factura, la reclasificación del mayor y la conciliación del saldo comercial son resultados distintos. Verificar cada uno solo cuando esté incluido en la tarea; no declararlos resueltos por la mera existencia del pago o asiento.

## Reglas contables reutilizables frente a reglas particulares

Para una operatoria nueva, revisar por separado ingreso, costo directo, gasto interno, activo/anticipo, impuestos, actividad y centro. Vincular el costo al trabajo documentado; el proveedor o una descripción amplia no bastan para generalizar su destino. No descontar automáticamente los costos subcontratados del ingreso ni convertir la calificación contable de un costo en una conclusión sobre el crédito fiscal.

Guardar cuentas concretas, relaciones con clientes/proveedores y criterios aprobados en las [instrucciones privadas del contribuyente](taxpayer-instructions.md). Los hechos de una factura, un plan o una fecha de entrega no deben convertirse en reglas universales de esta skill.
