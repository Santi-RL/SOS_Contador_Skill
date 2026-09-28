---
name: sos-contador-api
description: Consultar y registrar operaciones de SOS Contador con CUIT explícita, recetas comprobadas, vista previa y verificación. Usar para ventas, compras, cobranzas, pagos y sus documentos; separar el desarrollo de capacidades nuevas de la operación real.
---

# SOS Contador

Usar el CLI incluido. Priorizar la API pública **comprobada para la variante concreta**; `web-session` significa HTTP directo, no navegador. No descubrir rutas durante una tarea operativa.

## Elegir el modo

Anunciar el modo en la primera respuesta. Inferirlo por el pedido; no exigir al usuario conocer sus nombres. Una solicitud explícita de revisar o mejorar la skill habilita desarrollo. Un fallo operativo no cambia el modo por sí solo.

| Modo | Alcance | CLI |
|---|---|---|
| Operativo | Ejecutar únicamente recetas habilitadas, con datos reales y límites conocidos. | Predeterminado: `--work-mode operational`. |
| Desarrollo | Auditar código, documentación, perfiles y capacidades; consultas y previews sin escritura comercial. | `--work-mode development`, antes del subcomando. |
| Validación controlada | Probar una escritura real delimitada después de mostrar su preview y recibir autorización específica. | `--work-mode controlled-validation`, además de `--confirm`. |

Desarrollo no autoriza pruebas de escritura. No agregar flags de desarrollo o validación para eludir un bloqueo operativo. En validación controlada indicar CUIT, operación, campos, efecto fiscal/contable, cantidad máxima y lectura de verificación; no prometer rollback de un comprobante fiscal.

## Secuencia operativa

1. Leer las preferencias privadas generales si existe `<SOS_CONTADOR_HOME>/local/INSTRUCCIONES.md`.
2. Resolver el contribuyente por el catálogo; no confiar en memoria ni en el último seleccionado:

```powershell
python scripts/sos_contador_api.py auth resolve-cuit --name "empresa demo"
```

3. Fijar `--cuit-trabajo`, `--cuit-trabajo-id` o `--cuit-trabajo-nombre` en operaciones JWTC. Un borrador puede conservar la CUIT ya resuelta. Leer la entrada privada de esa empresa y solo los temas pertinentes conforme a [taxpayer-instructions.md](references/taxpayer-instructions.md).
4. Elegir la receta exacta en [operating-recipes.md](references/operating-recipes.md). Consultar solo la referencia documental que esa receta necesita. `api catalog` y `api describe` informan capacidades; no habilitan por sí solos una operación.
5. Para lecturas, ejecutar y comprobar filtros, período y cobertura. Para escrituras, resolver IDs, preparar el borrador o `--dry-run`, mostrarlo y comprobar autorización del efecto concreto **después de su vista previa**. Reutilizar una autorización vigente solo si cubre exactamente el mismo resultado ya presentado.
6. Ejecutar con `--confirm` sin cambiar el contenido aprobado. Verificar con una lectura independiente identidad, campos, estado activo y efecto comercial/contable requerido. Un ID o HTTP exitoso no basta.
7. Guardar evidencia privada y entregar el resultado. No editar scripts, catálogo, instrucciones públicas ni perfiles de extracción en modo operativo.

La configuración proviene de variables de entorno o `<SOS_CONTADOR_HOME>/.env.local`; el hogar predeterminado es `~/.sos-contador`. No pedir credenciales disponibles ni seleccionar una CUIT por variables heredadas. Ver [auth.md](references/auth.md) solo para configurar o resolver problemas de acceso.

## Cuándo detenerse

Detener las escrituras si falta una receta para la variante, el borrador no cuadra, la identidad es ambigua, el campo no se conserva o la respuesta difiere de lo esperado. No improvisar scripts, parámetros, asociaciones, asientos compensatorios ni un recorrido web para completar el resultado.

Se permiten las lecturas de verificación previstas por la receta para saber qué ocurrió. Ante timeout de escritura, **no reenviar**: el resultado puede haber sido registrado. Si no se puede determinar el estado, informar «resultado no confirmado» y detener ese trabajo.

Explicar al usuario: «Esta variante no tiene un procedimiento validado / no produjo el resultado esperado. Para investigar necesitamos pasar a modo desarrollo; eso puede modificar la skill reutilizable. Cualquier prueba que escriba en SOS requiere un alcance y una aprobación aparte». Pedir esa decisión sin cambiar de modo unilateralmente. Completar otras consultas independientes que sigan siendo seguras.

## Límites comunes

- API pública primero dentro de las rutas habilitadas. Usar únicamente los fallbacks HTTP nombrados en la receta; un error no autoriza un transporte nuevo. Los detalles de cobro y PDF requieren `--allow-web-session-fallback` cuando el fallback esté autorizado.
- No usar navegador en modo operativo. Las observaciones de UI de [capabilities-and-verification.md](references/capabilities-and-verification.md) son evidencia de desarrollo, no recetas alternativas. Un trabajo explícito sobre la UI es desarrollo y conserva sus límites de lectura/escritura.
- Bajas/anulaciones de comprobantes bloqueadas. Una aprobación de alta no autoriza borrados, CAE, correos, configuraciones compartidas ni nuevas operaciones.
- Separar registrar una venta, solicitar CAE, descargar PDF y enviar correo. La emisión con CAE todavía requiere validar su variante; no prometerla por disponer del flag `--obtienecae`.
- Excluir de activos los registros con `cancelado=1`, `fechabaja` no vacía o sección `ANULADOS`, salvo consulta expresa sobre anulados.
- Mantener documentos, CUIT, nombres, IDs, exportaciones, perfiles, capturas y secretos reales fuera de cualquier repositorio público. Respetar un destino privado local o remoto indicado por el usuario.
- No borrar archivos preexistentes para ordenar. Aplicar [safety-and-storage.md](references/safety-and-storage.md) para estructura privada, destinos, temporales y limpieza con inventario.

## Desarrollo y aprendizaje

Leer [development-roadmap.md](references/development-roadmap.md) antes de elegir una capacidad por investigar. Contiene prioridades, el método de pruebas en empresa ficticia y criterios de promoción. Aplicar ese método antes de ensayar variantes nuevas sobre una empresa real. El catálogo [public-api.md](references/public-api.md) describe contratos; la [matriz de evidencia](references/capabilities-and-verification.md) conserva límites observados. No confundir documentación, tests simulados y validación real.

Generalizar un hallazgo solo después de comprobarlo. Actualizar la regla existente, su receta, catálogo y pruebas ficticias; conservar payloads, respuestas e identificadores en el expediente privado. Los perfiles locales se diseñan y prueban en desarrollo; en operativo solo se consumen los existentes.

## Terminal manual y salida

Si el usuario pide terminal sin scripts, seguir [manual-terminal-api.md](references/manual-terminal-api.md): un comando por vez, sin cargar `.env.local` ni usar helpers. Este formato no elimina los límites de modo, vista previa y autorización.

Presentar conjuntos de registros en tablas Markdown; un detalle puede usar prosa. No explicar transportes salvo diagnóstico o una limitación material. Si pidió «facturas» y hay notas de crédito/débito en el período, preguntar si las incluye y, si acepta, devolver una sola tabla combinada.
