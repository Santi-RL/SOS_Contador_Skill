# Percepciones de IIBB cuando falta el comprobante

Usar en auditorías de compras con originales extraviados o tributos sin identificar. Es una consulta complementaria en portales fiscales; el CLI de SOS no implementa la descarga de estos listados. Las rutas siguientes están documentadas por los organismos y se verificaron hasta el acceso público; no constituyen una validación de descarga autenticada.

## Fuentes y alcance

| Jurisdicción | Consulta pertinente | Acceso y salida |
|---|---|---|
| Provincia de Buenos Aires | ARBA → Ingresos Brutos → DDJJ y deducciones → Deducciones informadas por los Agentes de Recaudación → Consulta y descarga. Luego Deducciones → Descarga para importar o Consulta detallada. | CUIT y CIT. Elegir período `AAAA-MM`, tipo de contribuyente y Percepciones. El instructivo contempla TXT y búsqueda por período o CUIT del agente. |
| CABA | Portal del Contribuyente de AGIP → Gestión AR – Agentes de Recaudación → Consulta de Retenciones / Percepciones. | El acceso vigente ofrece cuenta miBA; comprobar representación y servicio habilitado para la CUIT consultada. Conservar el formato original ofrecido por la consulta. No dar de alta servicios ni modificar relaciones solo para descargar. |

Fuentes: [ARBA: DDJJ y deducciones](https://web.arba.gov.ar/ingresos-brutos-ddjj-web), [instructivo de consulta y descarga](https://web.arba.gov.ar/sites/default/files/2023-12/instructivoconsultaycargadededucciones_0.pdf), [AGIP: Gestión AR](https://www.agip.gob.ar/tramites/261/?categoria=3). La ficha de AGIP se titula para contribuyentes locales: verificar el acceso y la representación efectivos si el contribuyente tributa por Convenio Multilateral, sin cambiar su régimen.

SIFERE WEB Consultas puede aportar información, pero no asumir cobertura de todos los agentes y jurisdicciones. Su [documentación oficial](https://www.ca.gob.ar/preguntas-frecuentes/sistemas/sifere/sifere-web-consultas) advierte sobre faltantes y remite a los fiscos. Verificar adhesiones y vigencia efectiva de sistemas nuevos como SIRCIP para el período; una adhesión normativa o fecha inicial anunciada no prueba implementación. No confundir percepciones de proveedores con recaudaciones bancarias SIRCREB/SIRCUPA ni con padrones de alícuotas.

## Disponibilidad

Los registros provienen de declaraciones de los agentes, no de una lista pública definitiva de compras. Consultar lo disponible y conservar fecha de extracción, período, jurisdicción, filtros y avisos de actualización. Si no se puede iniciar sesión, informar disponibilidad **no comprobada**, no «sin percepciones».

Los vencimientos de los agentes sirven para decidir cuándo volver a comprobar, pero no son fechas garantizadas de publicación. Revisar calendario, régimen y prórrogas vigentes: [ARBA, agentes de recaudación](https://web.arba.gov.ar/vencimientos-agentes-recaudacion) y [AGIP, calendario fiscal 2026 y modificaciones](https://boletinoficial.buenosaires.gob.ar/normativaba/norma/831825). No fijar en la skill un día de disponibilidad permanente. Una consulta temprana o sin coincidencias no acredita importe cero; puede haber presentaciones tardías, rectificativas o datos aún no incorporados.

## Conciliación y conservación

1. Buscar primero los archivos fiscales ya conservados por el contribuyente. Los de otros meses sirven para reconocer el formato, no para imputar importes al mes auditado.
2. Obtener las percepciones sufridas por la CUIT correcta para las jurisdicciones pertinentes. Preferir consulta o exportación sin crear ni presentar una DDJJ. Usar accesos autorizados específicos del organismo; las credenciales de SOS no se presumen válidas allí.
3. Cruzar CUIT del agente, fecha, tipo y letra, punto de venta, número e importe de percepción. Preservar ceros iniciales, signos, jurisdicción y registro fuente. Si un formato omite el PV o trunca números, contrastar el detalle u otra exportación: no declarar una coincidencia única solo por fecha o importe. Deduplicar una misma percepción obtenida de dos sistemas; no eliminar percepciones de distintas jurisdicciones por pertenecer a la misma factura.
4. Comparar el resultado con el detalle de compra, Libro IVA y asiento de SOS. Separar cada jurisdicción y tributo. No deducir percepciones por diferencia del total, aplicar alícuotas históricas como evidencia ni convertir impuestos nacionales o cargos del proveedor en IIBB.
5. Conservar la exportación original y el cruce como respaldo fiscal complementario, con sus límites. No renombrarlos como factura ni contabilizarlos como un original recuperado. Un registro informado respalda esa percepción, pero no reconstruye artículos, bases ni IVA por alícuota y no resuelve automáticamente su cómputo fiscal.

Mantener estados distintos: original disponible, respaldo alternativo parcial, consulta pendiente y discrepancia. Registrar el criterio reutilizable por empresa en sus instrucciones vigentes; comprobantes concretos y resultados en el expediente. Proponer cualquier corrección en SOS con el flujo habitual de vista previa, autorización vigente y verificación independiente.
