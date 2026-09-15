# SOS Contador API para agentes de IA

Skill comunitaria y portable para consultar y operar SOS Contador mediante su API, con selección explícita del CUIT de trabajo, previsualización antes de escrituras y almacenamiento privado fuera del repositorio.

El flujo principal es independiente del proveedor del agente: cualquier agente capaz de leer instrucciones Markdown y ejecutar Python puede utilizar `SKILL.md` y el CLI incluido. Los archivos de integración específicos de una plataforma son opcionales.

## Contenido

- `sos-contador-api/`: instrucciones, CLI y referencias reutilizables.
- `tests/`: pruebas determinísticas con datos ficticios.
- `AGENTS.md`: reglas de desarrollo, seguridad y portabilidad.
- `sos-contador-api/agents/`: adaptadores opcionales de integración con plataformas compatibles.

## Instalación

1. Clonar el repositorio o copiar `sos-contador-api/` a una ubicación accesible para el agente.
2. Instalar las dependencias del CLI:

```powershell
python -m pip install -r .\sos-contador-api\requirements.txt
```

Para procesar imágenes o PDFs escaneados, instalar también Tesseract con los datos de idioma español (`spa`). La skill prioriza español y usa inglés (`eng`) únicamente cuando `spa` no está disponible. Verificar los idiomas instalados con `tesseract --list-langs`; si Tesseract o sus datos están fuera de las rutas predeterminadas, configurar `SOS_CONTADOR_TESSERACT_CMD` y `TESSDATA_PREFIX`.

3. Crear el hogar operativo privado. De forma predeterminada se usa `~/.sos-contador`.
4. Copiar `sos-contador-api/.env.local.example` como `~/.sos-contador/.env.local` y completar las credenciales propias.
5. Si se necesita otra ubicación, definir `SOS_CONTADOR_HOME` con una ruta privada absoluta.

El agente debe leer `sos-contador-api/SKILL.md` antes de operar. Si la plataforma admite un directorio de skills, se puede copiar allí la carpeta completa. `sos-contador-api/agents/openai.yaml` aporta metadatos opcionales para plataformas compatibles con ese formato; el CLI y las instrucciones no dependen de ese archivo.

Los comprobantes, perfiles, exportaciones, cachés y credenciales no deben almacenarse dentro del clon.

Las instrucciones vigentes de cada empresa tienen un punto de entrada privado y estable, separado de los expedientes mensuales. La skill indica cómo localizarlas y actualizarlas sin convertirlas en un historial de acciones; ver [instrucciones por contribuyente](sos-contador-api/references/taxpayer-instructions.md).

## Desarrollo

```powershell
python -m pip install -r .\requirements-dev.txt
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m pytest -q -p no:cacheprovider
```

Además, validar el formato de la skill con las herramientas disponibles en la plataforma de destino. Todas las pruebas y ejemplos públicos deben usar entidades e identificadores inequívocamente ficticios.

## Alcance

El CLI usa modo operativo por defecto. Los caminos no habilitados se detienen antes de autenticar; para investigar usar `--work-mode development` antes del subcomando. Ese modo permite consultas y previews, y no escribe aunque se agregue `--confirm`. Una prueba real necesita su autorización y `--work-mode controlled-validation`.

Las [recetas operativas](sos-contador-api/references/operating-recipes.md) delimitan variantes de ventas, compras, cobranzas y pagos. [El roadmap](sos-contador-api/references/development-roadmap.md) guía el trabajo pendiente por operación. La importación histórica de planillas queda fuera de operativo hasta congelar el lote aprobado; el análisis `afip draft` permanece disponible. La emisión con CAE requiere validación fiscal separada.

La skill prioriza la API pública. El transporte HTTP `web-session` es un fallback explícito para capacidades que la API no cubre y no reutiliza perfiles ni cookies del navegador.

La [matriz de capacidades y verificación](sos-contador-api/references/capabilities-and-verification.md) delimita los campos y modos comprobados, las limitaciones observadas y las acciones que requirieron una interfaz web autorizada. Un endpoint disponible no garantiza que persista todos los campos enviados.

## Licencia

Apache License 2.0. Consultar [LICENSE](LICENSE).
