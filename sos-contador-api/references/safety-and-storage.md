# Seguridad, transporte y almacenamiento

## Índice

- [CUIT de trabajo](#cuit-de-trabajo)
- [Lecturas y escrituras](#lecturas-y-escrituras)
- [Bajas y anulaciones](#bajas-y-anulaciones)
- [Transporte](#transporte)
- [Credenciales y datos sensibles](#credenciales-y-datos-sensibles)
- [Exportaciones](#exportaciones)

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
3. Confirmar con el usuario el efecto concreto.
4. Repetir con `--confirm`.
5. Verificar mediante una lectura independiente.

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

No usar automatización de navegador como sustituto de ninguno de estos transportes.

## Credenciales y datos sensibles

Mantener `.env.local`, cachés, tokens y cookies bajo el hogar operativo privado, fuera del repositorio. Usar `~/.sos-contador` de forma predeterminada o definir `SOS_CONTADOR_HOME` con una ruta absoluta. No incluir secretos en parámetros de URL, documentación, pruebas ni previsualizaciones.

El CLI debe redactar claves con semántica de contraseña, secreto o token. Las operaciones internas `auth.login` y `cuit.credentials` no se invocan mediante `api invoke`; usar los helpers de autenticación para evitar exponer los JWT.

## Exportaciones

Guardar artefactos durables en:

```text
<SOS_CONTADOR_HOME>/local/exports/<cuit_trabajo>/<tipo>/<YYYY>/<MM>/
```

Usar carpetas estables como `ventas`, `compras`, `cobranzas`, `clientes`, `productos`, `asientos`, `libros_iva` o `plan_de_cuentas`.

Prefijar los nombres con fecha ISO, por ejemplo:

```text
2026-07-30-libro-iva-ventas-<cuit_trabajo>.json
```

Guardar, cuando aporte trazabilidad, la respuesta cruda y una versión normalizada `.csv`, `.md` o `.meta.json`.
