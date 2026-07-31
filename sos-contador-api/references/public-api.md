# Catálogo de la API pública

## Índice

- [Fuente y alcance](#fuente-y-alcance)
- [Comandos](#comandos)
- [Parámetros](#parámetros)
- [Estados de madurez](#estados-de-madurez)
- [Módulos cubiertos](#módulos-cubiertos)
- [Operaciones especiales](#operaciones-especiales)

## Fuente y alcance

El archivo [public-api-operations.json](public-api-operations.json) registra las 71 solicitudes publicadas en la colección de Postman revisada el 30 de julio de 2026.

Cada operación define:

- ID estable para el CLI;
- método y plantilla de path;
- autenticación `none`, `jwt` o `jwtc`;
- parámetros de query admitidos;
- presencia del body;
- efectos laterales;
- estado de validación.

No editar el catálogo con rutas inferidas. Incorporar únicamente operaciones publicadas o verificadas.

## Comandos

Listar todo o filtrar por módulo:

```powershell
python scripts/sos_contador_api.py api catalog
python scripts/sos_contador_api.py api catalog --module libroiva
python scripts/sos_contador_api.py api catalog --method PUT
```

Inspeccionar una operación:

```powershell
python scripts/sos_contador_api.py api describe --operation venta.save
```

Ejecutar una lectura:

```powershell
python scripts/sos_contador_api.py api invoke --operation cae.status --cuit-trabajo <cuit_trabajo> --param id=<id_venta>
```

Previsualizar y confirmar una escritura:

```powershell
python scripts/sos_contador_api.py api invoke --operation centrocosto.create --cuit-trabajo <cuit_trabajo> --body-file .\centro.json --dry-run
python scripts/sos_contador_api.py api invoke --operation centrocosto.create --cuit-trabajo <cuit_trabajo> --body-file .\centro.json --confirm
```

## Parámetros

Usar `--param clave=valor` para reemplazar segmentos como `:id`, `:periodo` o `:ejercicio`. Los valores se codifican para impedir que alteren la estructura del path.

Usar `--query clave=valor` solo para claves admitidas por la operación. El CLI rechaza parámetros desconocidos.

Usar `--body-json` o `--body-file`, nunca ambos. Consultar [public-api-payloads.md](public-api-payloads.md) para las estructuras documentadas.

Usar `--out` para respuestas binarias o exportaciones que deban persistir, por ejemplo `venta.pdf`.

## Estados de madurez

| Estado | Significado |
|---|---|
| `validated` | Probado previamente contra respuestas reales o cubierto por un helper estable. |
| `documented` | Publicado por SOS, aún sin prueba específica en este proyecto. |
| `documented-unvalidated` | Escritura publicada que requiere una prueba controlada antes de convertirse en ruta predeterminada. |
| `limited` | Funciona, pero se observaron respuestas incompletas o inconsistentes. |
| `experimental` | La propia documentación es incompleta, contradictoria o declara falta de implementación. |
| `internal` | Parte del flujo de autenticación; no invocar directamente para evitar exposición de tokens. |
| `blocked` | Operación destructiva deliberadamente bloqueada por seguridad. |

## Módulos cubiertos

| Módulo | Capacidades |
|---|---|
| Autenticación y CUIT | Registro, login interno, listado, credenciales, parámetros, CCMA, SCT y configuración móvil. |
| Maestros | Actividades, provincias, tipos, unidades, cuentas, centros de costo, clientes, productos, grupos modificadores y puntos de venta. |
| Comprobantes | Compras, ventas, cobros, pagos y recibos: listados, detalles, consultas y escrituras documentadas. |
| Contabilidad | Asientos, mayor, sumas y saldos, IVA por actividad y libros IVA compras/ventas. |
| Facturación | Estado de CAE, PDF, archivo de ventas y envío de comprobantes por correo. |
| Otros | e-Ventanilla, parámetros de impresión e índices mensuales. |

## Operaciones especiales

- `compra.search` y `venta.search` usan `POST`, pero son lecturas y no requieren `--confirm`.
- `venta.save` está documentada por SOS, pero permanece sin validación real en este proyecto.
- `cuentacorriente.list` es experimental porque Postman indica que no está implementada.
- `mayor.list` es experimental porque la solicitud publicada omite la autenticación explícita; el catálogo supone JWTC por coherencia con los reportes contables.
- `auth.login`, `auth.credentials` y `cuit.credentials` se administran internamente y no se exponen mediante `api invoke`.
- Las bajas de compras, ventas, cobros y pagos permanecen bloqueadas aunque figuren en Postman.
