# Seguridad, transporte y almacenamiento

## Índice

- [CUIT de trabajo](#cuit-de-trabajo)
- [Lecturas y escrituras](#lecturas-y-escrituras)
- [Bajas y anulaciones](#bajas-y-anulaciones)
- [Transporte](#transporte)
- [Credenciales y datos sensibles](#credenciales-y-datos-sensibles)
- [Exportaciones](#exportaciones)
- [Instrucciones vigentes y expedientes](#instrucciones-vigentes-y-expedientes)

## CUIT de trabajo

Exigir un CUIT de trabajo explícito para toda operación JWTC. Aceptar únicamente:

- `--cuit-trabajo <cuit>`;
- `--cuit-trabajo-id <id>`;
- `--cuit-trabajo-nombre <nombre>` resuelto con `auth resolve-cuit`;
- un documento cuyo comprador o receptor identifique una única CUIT accesible.

Permitir sin CUIT solo las operaciones de descubrimiento y cuenta: `auth info`, `auth list-cuits`, `auth resolve-cuit`, `api catalog`, `api describe` y operaciones catalogadas con autenticación `none` o `jwt`.

No usar `SOS_CONTADOR_CUIT`, `SOS_CONTADOR_CUIT_ID` ni el último contribuyente seleccionado como destino implícito.

## Lecturas y escrituras

Ejecutar las lecturas directamente. El catálogo marca `compra.search` y `venta.search` como lecturas semánticas aunque usen `POST`.

Para toda operación con `side_effect=true`:

1. Resolver el CUIT y los IDs involucrados.
2. Ejecutar `--dry-run` y revisar la previsualización técnica y comercial.
3. Comprobar que el usuario autorizó el efecto concreto después de conocer la vista previa. Una autorización vigente para el mismo resultado ya presentado no se pide otra vez. «Cargá este archivo» no aprueba importes, altas adicionales o efectos fiscales aún no mostrados.
4. Repetir con `--confirm`.
5. Verificar mediante una lectura independiente los campos guardados y el efecto buscado. Un ID devuelto no acredita persistencia completa; ante un resultado ambiguo, consultar antes de reintentar.

No interpretar una confirmación de creación o modificación como autorización para anular.

## Bajas y anulaciones

Mantener bloqueadas las bajas de compras, ventas, cobros y pagos. No intentar descubrir campos de cancelación mediante prueba y error.

En lecturas, excluir de resultados activos los registros con cualquiera de estos indicadores:

- `cancelado=1`;
- `fechabaja` no vacía;
- pertenencia a una sección `ANULADOS`.

Permitir su consulta solo si el usuario pide revisar comprobantes anulados.

## Transporte

En operativo, usar la API pública para la variante comprobada y habilitada en [operating-recipes.md](operating-recipes.md). Documentado no significa validado. Usar HTTP `web-session` únicamente mediante sus helpers existentes para:

- filtros o detalles no disponibles en la API pública;
- cuerpos enriquecidos con cheques o retenciones;
- asociaciones de cobranzas;
- el registro histórico de ventas sin CAE y la comprobación activa complementaria de compras;
- fallbacks de detalle de cobro y PDF expresamente autorizados, con `--allow-web-session-fallback`.

Si no hay una ruta suficiente, detener la operación y solicitar desarrollo. No usar navegador en operativo. Las observaciones de UI de [capabilities-and-verification.md](capabilities-and-verification.md) se investigan en desarrollo explícito; no son un fallback automático. No extraer ni reutilizar cookies del navegador por fuera de la herramienta permitida.

El CLI usa `--work-mode operational` por defecto. `development` habilita consultas y previews; bloquea escrituras reales aun con `--confirm`. `controlled-validation` requiere aprobación del caso antes de ejecutarlo, conserva confirmaciones y no levanta el bloqueo de bajas de comprobantes. El flag de modo es una barrera contra errores del agente, no un sistema de autorización independiente; no demuestra una aprobación humana. Los imports Python directos son interfaces de desarrollo y no deben utilizarse para eludir el CLI.

Los reintentos automáticos se limitan a GET y POST de lectura conocidos. Ante timeout de una escritura, el cliente no reenvía: consultar el estado por las lecturas de la receta y detener si sigue ambiguo. No suponer que «falló la conexión» significa «no se registró».

## Credenciales y datos sensibles

Mantener `.env.local`, cachés, tokens y cookies bajo el hogar operativo privado, fuera del repositorio. Usar `~/.sos-contador` de forma predeterminada o definir `SOS_CONTADOR_HOME` con una ruta absoluta. No incluir secretos en parámetros de URL, documentación, pruebas ni previsualizaciones.

El CLI debe redactar claves con semántica de contraseña, secreto o token. Las operaciones internas `auth.login` y `cuit.credentials` no se invocan mediante `api invoke`; usar los helpers de autenticación para evitar exponer los JWT.

Si el usuario ya autorizó iniciar o renovar sesión, no pedir la misma autorización porque venció el acceso. Cuando el fallback web esté autorizado y el formulario legítimo tenga las credenciales cargadas, accionar **Ingresar** sin leer ni copiar la contraseña y comprobar después la sesión y el contribuyente seleccionado. Pedir intervención solo ante una credencial realmente faltante, una verificación personal o un error de acceso que no pueda resolverse dentro del alcance autorizado. El permiso de autenticación no autoriza registraciones, pagos, presentaciones ni cambios de seguridad.

## Exportaciones

Precedencia: archivo completo explícito → directorio explícito con nombre seguro → estructura privada predeterminada. El destino puede ser una carpeta local, una unidad montada o un directorio remoto autorizado. Resolver la ruta absoluta y comprobar acceso, carácter privado y ausencia de colisión antes de escribir. No tratar una ruta remota inaccesible como una carpeta local con el mismo texto; preparar la transferencia únicamente al destino autorizado y verificar tamaño/hash o lectura equivalente. No prometer entrega si la transferencia no se confirmó.

No sobrescribir archivos ajenos a la modificación autorizada, no colocar datos reales en un repositorio ni crear una copia adicional solo para imponer la estructura predeterminada. El CLI rechaza salidas existentes: elegir nombre nuevo; una autorización de reemplazo requiere un procedimiento de conservación proporcional, no eludir ese control. Los paths resueltos dentro del paquete/repositorio se rechazan aunque estén ignorados por Git.

Si no se indicó destino, guardar exportaciones durables en:

```text
<SOS_CONTADOR_HOME>/local/exports/<nombre_normalizado>__<CUIT_formateada>/<tipo>/<YYYY>/<MM>/
```

Usar carpetas estables como `ventas`, `compras`, `cobranzas`, `clientes`, `productos`, `asientos`, `libros_iva` o `plan_de_cuentas`.

Prefijar los nombres con fecha ISO, por ejemplo:

```text
2026-07-30-libro-iva-ventas-<cuit_trabajo>.json
```

Guardar, cuando aporte trazabilidad, la respuesta cruda y una versión normalizada `.csv`, `.md` o `.meta.json`.

Localizar directorios existentes por CUIT antes de crear uno. La clave con nombre es para navegación humana; no renombrar automáticamente directorios antiguos, cachés ni perfiles de extracción que usan solo CUIT.

## Instrucciones vigentes y expedientes

Mantener las reglas de cada empresa en `local/taxpayers/<nombre_cuit>/INSTRUCCIONES.md` y los temas enlazados que necesite. Leer y actualizar conforme a [taxpayer-instructions.md](taxpayer-instructions.md). No incluir fechas en sus nombres ni acumular entradas de ejecución.

Conservar fuentes, borradores, respuestas y entregables de una tarea en `local/jobs/<nombre_cuit>/<YYYY>/<MM>/<job_id>/{sources,drafts,results,artifacts}/`. Esos archivos aportan evidencia; no sustituyen las instrucciones vigentes. Si el usuario indicó una fuente existente, leerla allí sin moverla ni duplicarla por esta convención.

## Estructura privada completa

```text
<SOS_CONTADOR_HOME>/
  .env.local                     credenciales; nunca evidencia ni instrucciones
  .cuit_* / .document_*           cachés internos existentes
  .draft_cache/                  borradores del CLI; conservar sus paths
  local/
    INSTRUCCIONES.md              preferencias generales expresas
    taxpayers/<nombre_cuit>/      instrucciones vigentes y temas por empresa
    document_profiles/<cuit>/    perfiles de extracción existentes
    inbox/<nombre_cuit>/<tipo>/<YYYY>/<MM>/<job_id>/
    inbox/_pending_classification/<YYYY>/<MM>/<job_id>/
    jobs/<nombre_cuit>/<YYYY>/<MM>/<job_id>/
      sources/                   originales adjuntos sin destino elegido
      drafts/                    extracción, OCR, crops y normalizaciones
      results/                   respuestas y verificación independiente
      artifacts/                 entregables finales
    exports/<nombre_cuit>/<tipo>/<YYYY>/<MM>/
    development/<fecha>-<tema>/   investigación general privada, sin mezclar emisores
    development/tools/<herramienta>/ prototipos reutilizables pendientes, con procedencia y límites
    archive/                     legado preservado; no autoriza borrado automático
    temp/<id_tarea>/              intermediarios desechables identificados
```

Crear solo lo necesario. `nombre_cuit` es `<nombre_normalizado>__<CUIT_formateada>` validada por catálogo; buscar por sufijo para evitar duplicados y sanear caracteres inválidos en Windows. Si no se puede clasificar un documento, conservar cada grupo independiente en pendientes y aclarar la empresa antes de cualquier escritura SOS. Un adjunto temporal sin destino duradero se conserva como fuente del expediente; no mover un original explícito del usuario por esta convención.

Los documentos fiscales, perfiles y decisiones de emisores nunca se integran al repositorio público, aunque se cambien sus nombres. Solo se transfiere el aprendizaje general con fixtures inventados desde cero. Los archivos históricos de tareas son evidencia, no nuevas instrucciones vigentes.

## Temporales y limpieza segura

Los scripts ad hoc con datos reales y capturas permanecen en el expediente privado o `local/temp/<id_tarea>/`; los tests ficticios usan el temporal del sistema. No crear directorios temporales permanentes en el proyecto. Al cerrar, clasificar cada artefacto generado como entregable, evidencia, aprendizaje/código candidato o desechable; registrar únicamente lo que deba conservarse.

Para auditar legado, ejecutar en desarrollo:

```powershell
python scripts/audit_workspace.py --root <proyecto> --out <inventario_privado_nuevo.json>
```

El inventario es de solo lectura e incluye hash, tamaño y paths; omite `.git` y no sigue enlaces. Es privado por contener nombres/rutas. Revisar aparte archivos Git versionados, ignorados y cambios; `.gitignore` no borra el historial ni evita un `git add -f`.

Antes de limpiar, presentar origen absoluto, tipo/procedencia, consumidor conocido, propuesta, destino y razón de conservación/eliminación. Aplicar estas reglas:

| Clase | Acción |
|---|---|
| Original, adjunto, comprobante o evidencia de emisor | Conservar y clasificar en su expediente. Mover solo dentro del alcance autorizado, preservando integridad y referencias. Nunca borrar por antigüedad, extensión o nombre «tmp». |
| Script o nota preexistente con posible aprendizaje | Leer su contenido y consumidores. Integrar lo genérico útil en scripts/referencias de la skill, probarlo y enlazarlo desde la guía pertinente. Conservar las partes pendientes en desarrollo privado con procedencia, límites y próximo paso. No mezclar patrimonio reutilizable con residuos ni habilitar correcciones fiscales sin validar. |
| Archivo preexistente o procedencia incierta | Conservar; presentar decisión sobre movimiento/eliminación. Un hash duplicado no demuestra que el archivo sea prescindible. |
| Temporal creado en esta tarea, desechable y reproducible | Se puede retirar al terminar si no es fuente, evidencia ni única copia. Limitarse a paths exactos registrados por esta tarea. |

Cuando el usuario autorice separar material prescindible, hacerlo **después** de integrar lo reutilizable y conservar los documentos/evidencias en sus destinos permanentes. Agrupar solo residuos comprobados en un único contenedor fuera del repositorio público. No debe ser un archivo histórico del que dependa el trabajo futuro: ningún documento, configuración, script, instrucción o expediente conservado puede enlazarlo o necesitar su contenido. Comprobar referencias y ejecutar la skill en una copia aislada que lo excluya. Un archivo de utilidad incierta se conserva para desarrollo o clasificación; no se declara desechable.

Para mover o borrar directorios, resolver primero todos los paths y comprobar que permanecen dentro del origen y destino previstos. Rechazar enlaces/junctions y colisiones; no construir comandos de shell a partir de nombres de documentos. Verificar hashes, tamaños y conteos después de un movimiento autorizado. Para material conservado, guardar un manifiesto privado de origen/destino y cualquier error; si la verificación falla, no eliminar la fuente. La lista de residuos puede permanecer dentro del propio contenedor, sin referencias externas a su ubicación. Un respaldo o la aprobación general de una auditoría no autorizan eliminar documentación preexistente. Pedir decisión sobre la lista concreta cuando corresponda.
