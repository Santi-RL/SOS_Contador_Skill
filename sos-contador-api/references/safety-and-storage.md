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
3. Comprobar que el usuario autorizó el efecto concreto. Una autorización vigente para el mismo alcance no se pide otra vez; la vista previa sigue siendo obligatoria.
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

Usar la API pública para toda capacidad documentada. Usar HTTP `web-session` únicamente para:

- filtros o detalles no disponibles en la API pública;
- cuerpos enriquecidos con cheques o retenciones;
- asociaciones de cobranzas;
- operaciones públicas documentadas que hayan fallado y cuyo fallback haya sido autorizado explícitamente.

No usar automatización de navegador como sustituto general de estos transportes. Si ambos carecen de una ruta suficiente para el campo o acción requerida, aplicar únicamente las excepciones acotadas de [capabilities-and-verification.md](capabilities-and-verification.md), con navegador visible autorizado o intervención del usuario. Mantener la verificación independiente y no extraer ni reutilizar cookies del navegador por fuera de esa herramienta.

## Credenciales y datos sensibles

Mantener `.env.local`, cachés, tokens y cookies bajo el hogar operativo privado, fuera del repositorio. Usar `~/.sos-contador` de forma predeterminada o definir `SOS_CONTADOR_HOME` con una ruta absoluta. No incluir secretos en parámetros de URL, documentación, pruebas ni previsualizaciones.

El CLI debe redactar claves con semántica de contraseña, secreto o token. Las operaciones internas `auth.login` y `cuit.credentials` no se invocan mediante `api invoke`; usar los helpers de autenticación para evitar exponer los JWT.

Si el usuario ya autorizó iniciar o renovar sesión, no pedir la misma autorización porque venció el acceso. Cuando el fallback web esté autorizado y el formulario legítimo tenga las credenciales cargadas, accionar **Ingresar** sin leer ni copiar la contraseña y comprobar después la sesión y el contribuyente seleccionado. Pedir intervención solo ante una credencial realmente faltante, una verificación personal o un error de acceso que no pueda resolverse dentro del alcance autorizado. El permiso de autenticación no autoriza registraciones, pagos, presentaciones ni cambios de seguridad.

## Exportaciones

Respetar primero la ruta o directorio privado indicado por el usuario. No sobrescribir archivos ajenos a la modificación autorizada, no colocar datos reales en un repositorio público ni crear una copia adicional solo para imponer la estructura predeterminada.

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
