# Instrucciones del proyecto

## Entrada y modos

Leer primero [sos-contador-api/SKILL.md](sos-contador-api/SKILL.md). Esa entrada define los modos y las recetas; no duplicar sus procedimientos en este archivo. Anunciar el modo inferido en español. Un pedido de operar datos reales es operativo; una solicitud explícita de revisar/mejorar la skill es desarrollo. No escalar de operativo por iniciativa del agente.

En operativo, usar únicamente CLI y recetas comprobadas para la variante. Ante capacidad ausente, resultado inesperado o escritura ambigua: detener esa acción, verificar por lecturas previstas e informar que investigar requiere desarrollo. No cambiar código, reglas públicas, perfiles de extracción, transporte ni diseño para completar el pedido. La validación de escritura real necesita preview y aprobación específica; desarrollo por sí solo no la autoriza.

## API, seguridad y datos privados

Priorizar API pública comprobada. HTTP `web-session` es un fallback incorporado para las recetas expresas; no es navegador. El navegador se limita al desarrollo explícito sobre una capacidad/UI, sin escritura implícita. No reutilizar perfiles, cookies ni credenciales del navegador por fuera de la herramienta autorizada.

Usar credenciales de `<SOS_CONTADOR_HOME>/.env.local` (por defecto `~/.sos-contador/.env.local`); no pedirlas de nuevo si existen. Resolver el contribuyente por catálogo y mantenerlo explícito. Si falta un dato, pedir solo el faltante; no exigir una CUIT predeterminada en configuración.

Todo trabajo real —emisores/contribuyentes, clientes, proveedores, documentación, reglas, perfiles, capturas, exports y diagnóstico— queda fuera del repositorio. Un `.gitignore` no sustituye esa separación ni elimina archivos ya versionados. Publicar exclusivamente código genérico, instrucciones portables y fixtures ficticios determinísticos. No incluir datos reales, rutas personales ni identificadores de una cuenta en diffs, mensajes de commit o revisiones externas.

Respetar directorios privados locales o remotos elegidos por el usuario. Por defecto seguir [safety-and-storage.md](sos-contador-api/references/safety-and-storage.md), incluida su limpieza con inventario; nunca borrar documentos preexistentes o fuentes para ordenar. Leer instrucciones vigentes por empresa según [taxpayer-instructions.md](sos-contador-api/references/taxpayer-instructions.md).

El modo terminal manual sigue su referencia y los mismos límites; sus hallazgos concretos permanecen privados. Solo desarrollo puede integrar reglas generalizadas en la guía pública.

## Desarrollo y revisión

- Empezar por [development-roadmap.md](sos-contador-api/references/development-roadmap.md); definir caso, evidencia y criterio de promoción. No marcar una variante validada por un mock, un dry-run o un ID aislado.
- Mantener `SKILL.md` breve y referencias por tarea. Conservar una fuente principal por regla. Cambios contables particulares pertenecen a instrucciones privadas, no a la lógica pública.
- Ejecutar pruebas enfocadas y checks pertinentes. Revisión adicional de cambios en autenticación, sesiones, CUIT, documentos, salidas y portabilidad. Verificar hallazgos contra el código real.
- Obtener autorización explícita antes de enviar código o artefactos a un revisor externo. Mantener integraciones de proveedor/plataforma opcionales; el CLI no depende de ellas.
- Los temporales de pruebas se generan fuera del checkout; usar el directorio temporal del sistema, `PYTHONDONTWRITEBYTECODE=1` y pytest sin cache local. No usar `--basetemp` sobre un directorio preexistente con documentos: pytest puede vaciarlo.
- No hacer commit, push, publicación ni reescritura de historial sin pedido correspondiente. Antes de publicar, inspeccionar archivos versionados y diff por datos privados, además de `.gitignore`.
- No exigir herramientas de revisión/desarrollo durante consultas operativas.

## Idioma

Usar español profesional completo en texto de usuario: tildes, ñ y signos de apertura. ASCII solo para identificadores o formatos técnicos que lo necesiten. Revisar ortografía y enlaces antes de entregar.
