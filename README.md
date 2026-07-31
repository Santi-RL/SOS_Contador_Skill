# SOS Contador API para Codex

Skill comunitaria para consultar y operar SOS Contador mediante su API, con selección explícita del CUIT de trabajo, previsualización antes de escrituras y almacenamiento privado fuera del repositorio.

## Contenido

- `sos-contador-api/`: skill instalable.
- `tests/`: pruebas determinísticas con datos ficticios.
- `AGENTS.md`: reglas de desarrollo, seguridad y portabilidad.

## Instalación

1. Copiar `sos-contador-api/` al directorio de skills de Codex.
2. Instalar las dependencias:

```powershell
python -m pip install -r .\sos-contador-api\requirements.txt
```

3. Crear el hogar operativo privado. De forma predeterminada se usa `~/.sos-contador`.
4. Copiar `sos-contador-api/.env.local.example` como `~/.sos-contador/.env.local` y completar las credenciales propias.
5. Si se necesita otra ubicación, definir `SOS_CONTADOR_HOME` con una ruta privada absoluta.

Los comprobantes, perfiles, exportaciones, cachés y credenciales no deben almacenarse dentro del clon.

## Desarrollo

```powershell
python -m pip install -r .\requirements-dev.txt
python -m pytest -q
python -X utf8 <ruta-skill-creator>\scripts\quick_validate.py .\sos-contador-api
```

Todas las pruebas y ejemplos públicos deben usar entidades e identificadores inequívocamente ficticios.

## Alcance

La skill prioriza la API pública. El transporte HTTP `web-session` es un fallback explícito para capacidades que la API no cubre y no reutiliza perfiles ni cookies del navegador.

## Licencia

Apache License 2.0. Consultar [LICENSE](LICENSE).
