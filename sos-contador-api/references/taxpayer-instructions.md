# Instrucciones privadas por contribuyente

Usar cuando se inicia una operación con una empresa conocida o cuando el usuario pide conservar aprendizajes sobre ella. Mantener una fuente estable de instrucciones vigentes, separada de los expedientes y de los perfiles de extracción.

## Localización y carga

Después de resolver el contribuyente con el catálogo, localizar:

```text
<SOS_CONTADOR_HOME>/local/taxpayers/<nombre_normalizado>__<CUIT_formateada>/
  INSTRUCCIONES.md
  configuracion-sos.json           si aporta un mapa de IDs y conceptos
  operatoria/<tema>.md             cuando un tema necesita desarrollo propio
  pendientes.md                   solo decisiones o datos aún pendientes
```

No crear archivos vacíos para completar el esquema. Un único `INSTRUCCIONES.md` basta para una empresa sencilla. No incluir año, mes ni ID de tarea en el directorio o nombre de las instrucciones vigentes.

- Buscar primero por el sufijo `__<CUIT_formateada>` y comprobar la identidad declarada dentro del archivo. Un cambio de razón social no debe crear otra carpeta para la misma CUIT.
- Si ya existe una organización privada elegida por el usuario, respetarla y mantener un solo punto de entrada; no duplicar instrucciones únicamente para imponer este esquema.
- Leer el punto de entrada y solo los temas y terceros pertinentes. Las instrucciones del usuario en la sesión prevalecen sobre una regla guardada.
- Si hay dos directorios o instrucciones incompatibles para la misma CUIT, no elegir el más reciente a ciegas. Revisar su alcance y autoridad; aclarar solo el conflicto que impide avanzar con seguridad.
- Si no hay instrucciones, continuar con la información disponible. No recorrer todos los expedientes por defecto; consultarlos para un caso concreto o para una consolidación solicitada.

El agente lee estos archivos: el CLI actual no los aplica automáticamente ni los ejecuta como reglas de clasificación. Las cuentas e IDs guardados son referencias a verificar en SOS, no destinos implícitos de una escritura.

## Qué conservar

El punto de entrada debe permitir saber cómo trabajar con la empresa, no qué hizo el agente en cada turno. Conservar según resulte útil:

- identidad validada, actividades y límites de cada operatoria;
- ubicación de documentación y forma de buscar comprobantes, sin inventariar todos los archivos;
- decisiones por tipo de operación: condición de aplicación, imputación y excepciones;
- clientes y proveedores conocidos, identificados por CUIT cuando se conozca, con el destino comprobado y sus límites;
- mapa de cuentas, centros, conceptos, puntos de venta y actividad, con fecha de verificación;
- criterios provisionales claramente identificados y el hecho que permitiría resolverlos;
- referencias breves a la evidencia o autorización que fundamenta cada tema.

Ejemplo de regla útil: «Si el servicio de un tercero integra el trabajo contratado por un cliente, imputarlo al costo de ese servicio y al centro correspondiente. Si es para uso interno, revisar su función; no aplicar la misma cuenta solo por coincidir el proveedor».

No incorporar listas de facturas procesadas, importes de cada pago, resultados de cada herramienta, capturas, payloads, conteos de registros ni relatos cronológicos. Esos datos pertenecen al expediente. No guardar tokens o credenciales en las instrucciones.

## Actualización sin crecimiento como log

1. Distinguir una instrucción expresa del usuario, un hecho comprobado y una inferencia provisional. No promover automáticamente esta última a criterio definitivo.
2. Actualizar la regla pertinente en su lugar. Integrar precisiones, sustituir la redacción superada y eliminar duplicaciones; no anexar un bloque por conversación o por factura.
3. Mantener un punto de entrada corto. Separar por tema cuando mejore la consulta, con enlaces desde el índice; no repartir instrucciones entre carpetas mensuales.
4. Conservar un respaldo proporcional fuera del documento vigente antes de una reorganización. El historial y la evidencia siguen en `jobs/` o en el archivo privado.
5. Revisar los pendientes como estado actual: retirar los resueltos y conservar su resultado en la regla aplicable o en el expediente. Un criterio aprobado no autoriza futuras escrituras sin el alcance y controles correspondientes.

No convertir una observación sobre un proveedor en una clasificación indiscriminada, ni una aprobación puntual en un permiso permanente para registrar operaciones o contactar terceros.

## Consolidar instrucciones antiguas

Cuando el usuario pida consolidación, revisar los documentos pertinentes de `local/jobs/<nombre_cuit>/`, `local/taxpayer_rules/<nombre_cuit>/` u otras ubicaciones privadas que ya utilice. Extraer las reglas vigentes y resolver contradicciones por evidencia y por instrucciones del usuario, no solo por el nombre o fecha del archivo.

Mantener los informes completos como antecedentes históricos. En los documentos que antes se presentaban como criterios, dejar una indicación breve de que son antecedentes y un enlace al punto de entrada vigente. Un archivo legado usado como índice puede convertirse en una redirección después de revisar sus consumidores. No borrar ni mover comprobantes originales, cachés o perfiles ejecutables para ordenar las instrucciones.

Puede dejarse `local/jobs/<nombre_cuit>/INSTRUCCIONES.md` como enlace de navegación al punto de entrada. Ese archivo no debe contener otra copia de las reglas. Los jobs continúan organizados por fecha porque son expedientes, no porque las instrucciones deban fragmentarse de esa forma.

## Privacidad y separación de funciones

La skill pública enseña este procedimiento y usa marcadores o entidades ficticias. Nombres, CUIT, IDs, rutas documentales, relaciones comerciales y evidencia real permanecen en el espacio privado del contribuyente. No enviarlos a repositorios, revisores externos o servicios ajenos a la tarea.

Los [perfiles documentales](local-document-profiles.md) describen cómo extraer un formato recurrente; las instrucciones por contribuyente describen cómo tratar su operatoria. No mezclar sus esquemas ni mover perfiles con consumidores activos.
