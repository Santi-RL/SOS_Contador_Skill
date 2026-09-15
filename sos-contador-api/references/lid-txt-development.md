# Diagnóstico de TXT de Libro IVA — desarrollo

Usar [reconcile_lid_txt.py](../scripts/development/reconcile_lid_txt.py) exclusivamente en desarrollo para comparar un CSV normalizado con los TXT de comprobantes y alícuotas. Reutiliza la lectura de anchos fijos y la comparación decimal del prototipo. No conecta con SOS, no modifica fuentes ni genera TXT corregidos. Una salida sin diferencias **no valida fiscalmente** el archivo.

```powershell
python scripts/development/reconcile_lid_txt.py --work-mode development --csv <csv_privado> --cbte <comprobantes_privados.txt> --alicuotas <alicuotas_privadas.txt>
```

Devuelve JSON por stdout; tratarlo como privado cuando los insumos sean reales. Código de salida: `0`, comparación parcial sin discrepancias; `1`, diferencias o advertencias; `2`, entrada no soportada o inválida. No sustituir una columna omitida por cero ni cambiar el formato automáticamente ante un error.

Contrato actualmente probado con datos ficticios:

- CSV UTF-8 con cabecera y separador coma. Columnas obligatorias: `tipo_documento` (`F` o `C`, donde `C` es nota de crédito), `letra`, `punto_venta`, `numero`, `cuit_emisor`, `fecha` (AAAAMMDD o AAAA-MM-DD), `total`, `gravado_0`, `iva_0`, `gravado_10_5`, `iva_10_5`, `gravado_21`, `iva_21`, `gravado_27`, `iva_27`, `exento`, `no_gravado`, `otros_impuestos`. `proveedor` es opcional. Los importes vacíos representan cero; máximo dos decimales y sin separador de miles. La coma decimal exige comillas CSV.
- TXT UTF-8 con líneas CBTE de 325 caracteres y ALICUOTAS de 84, según el formato heredado del prototipo. Subconjunto: códigos `001`, `003`, `011`, `081`; alícuotas `0003`, `0004`, `0005`, `0006`. No certifica la vigencia ni el conjunto completo del diseño fiscal.
- Rechaza claves duplicadas, alícuotas huérfanas, códigos fiscales diferentes entre CBTE/ALICUOTAS y conjuntos CSV/CBTE distintos. No agrega alícuotas repetidas.
- Compara fecha, total, no gravado, exento, crédito fiscal, otros tributos agregados y neto/IVA por alícuota. Las NC se comparan por magnitud. No valida CUIT por dígito verificador, autorización fiscal, moneda, jurisdicciones ni todos los campos del formato.
- Los residuales y negativos inesperados se informan. No se absorben en bases, IVA o percepciones. La distribución entre tributos exige cotejar el original.

## Próximo desarrollo

D16 incorpora el diagnóstico reutilizable; la generación de correcciones sigue pendiente. Antes de ampliarla: contrastar diseño oficial vigente y originales, preservar identidad y todos los campos, distinguir tipo 001/081/201, moneda, jurisdicciones y NC, agregar fixtures por variante y verificar contra una segunda lectura. No reconstruir importes para forzar el total. Cualquier eventual exportador debe usar salidas nuevas, preview de cada diferencia y autorización del resultado concreto; nunca sobrescribir originales.

Cuando exista un prototipo previo aún no validado, conservarlo en el hogar privado bajo `local/development/tools/<herramienta>/`, junto con su procedencia, límites y relación con el módulo integrado. Ese material es patrimonio de desarrollo; no es una receta operativa ni una dependencia del CLI.
