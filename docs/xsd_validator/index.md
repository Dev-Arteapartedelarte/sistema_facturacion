# Validación XSD — `xsd_validator/`

Carpeta con **herramientas independientes** (no son parte del ciclo de vida de Django) para **validar los XML generados contra los esquemas XSD del SII**.

Son scripts ejecutables directamente:

```bash
uv run python xsd_validator/validate_xsd.py
```

o con la versión instalada:

```bash
cd xsd_validator && python validate_xsd.py
```

## ¿Qué es una validación XSD?

Un **XSD (XML Schema Definition)** es un "contrato" sobre cómo debe verse un XML: qué elementos existen, en qué orden, qué atributos, qué tipos de dato (fechas, montos). Validar el XML contra el XSD garantiza que el SII lo aceptará (o al menos que cumple la estructura oficial).

## Estructura de la carpeta

| Archivo | Propósito |
|---------|-----------|
| `validate_xsd.py` | Validador general (`SIIValidator`) con mapeo libro↔XSD, reporte JSON y salida por consola |
| `validate_diario.py` | Validador mínimo específico del Libro Diario |
| `validate_lce_lxml.py` | Validación con **lxml** (con manejo de namespaces) |
| `validate_lce_structure.py` | Validador de **estructura mínima** (elementos requeridos, salvo `RutFirma`/`TmstFirma`) |
| `validate_lce_complete.py` | Validador completo (xmlschema) de los tres libros |
| `validate_lce_correct.py` | Variante con **codificación ISO-8859-1** |
| `validate_lce_final.py` | Variante que maneja correctamente las **inclusiones** de XSD |
| `validate_lce_fixed.py` | Validador completo que guarda `validation_report.json` |
| `validate_envio_complete.py` | Valida el XML como parte de un **envío de libros** (`LceEnvioLibros_v10.xsd`) |
| `fix_and_validate.py` | **Corrige** el XML (agrega namespace) y luego valida |
| `schemas/sii/` | Los XSD oficiales del SII (Diario, Mayor, Diccionario, Envío, Firma, etc.) |
| `xml_samples/` | XML de ejemplo: `libro_diario.xml`, `libro_mayor.xml`, `diccionario.xml` |

## Ciclo común de todos los validadores

```
Cargar el XSD (xmlschema.XMLSchema o lxml.XMLSchema)
   │
   ▼
Leer el XML (archivo o string)
   │
   ▼
schema.validate(xml)  o  schema.assertValid(doc)
   │
   ├─ Sin errores → IMPRIME "VÁLIDO"   ── return True  ← TERMINA
   └─ Error       → IMPRIME "INVÁLIDO" + detalle ── return False  ← TERMINA
```

**Qué controla la finalización del ciclo**:
- La excepción `XMLSchemaValidationError` (xmlschema) o `DocumentInvalid` (lxml) detiene la validación en el primer error o recoge los errores.
- Cada `return True/False` cierra el flujo del archivo.
- Los `with open(...)` y `with etree.XML(...)` liberan recursos al salir.

## Tipos de XSD disponibles (`schemas/sii/`)

- **Libros**: `LceDiario_v10.xsd`, `LceMayor_v10.xsd`, `LceDic_v10.xsd`, `LceBalance_v10.xsd`, `LceResultado_v10.xsd`.
- **Envío**: `LceEnvioLibros_v10.xsd`, `LceEnvioOblig_v10.xsd`.
- **Soporte**: `LceSiiTypes_v10.xsd`, `SiiTypes_v10.xsd`, `LceDiarioRes_v10.xsd`, `LceMayorRes_v10.xsd`, `xmldsignature_v10.xsd`, `LceCal_v10.xsd`, `LceCoCertif_v10.xsd`, `LceCoCierre_v10.xsd`.
- **DTE**: `DTE_v10.xsd`, `EnvioDTE_v10.xsd` (para documentos tributarios).

## Los "intentos" repetidos

Hay varios scripts *casi iguales* (`complete`, `correct`, `final`, `fixed`, `lxml`...). Son **iteraciones de desarrollo**: cada uno probó un enfoque distinto (librería, namespace, codificación ISO-8859-1, inclusiones de XSD). El más completo y reutilizable es `validate_xsd.py` con la clase `SIIValidator`.

## `SIIValidator` (validate_xsd.py) — la clase principal

**Qué hace**: gestiona la carga de esquemas y la validación con reporte.

### `_load_schemas()`

Carga los tres XSD (`diario`, `mayor`, `diccionario`) usando `xmlschema.XMLSchema`. El bucle `for name, filename in SCHEMA_MAP.items()` **termina al recorrer el mapa completo** (3 esquemas), registrando si cada archivo existe y carga bien.

### `validate_xml(xml_content, schema_type)`

- Intenta interpretar el XML como **ruta de archivo** (si el Path existe lee el contenido) o como **string XML**.
- Llama a `schema_info['schema'].validate(xml_str)`.
- **Finalización**: `try/except` que captura `XMLSchemaValidationError`, `XMLSyntaxError` y cualquier otra excepción → rellena `result['errors']` y devuelve `result` con `valid: True/False`. El `return` siempre ocurre.

### `validate_file(filepath)`

Detecta el tipo automáticamente leyendo el contenido (`'LceDiario'`, `'LceMayor'`, `'LceDiccionario'`). Si no lo identifica → `return {'error': 'No se pudo detectar el tipo de libro'}` (**termina**).

### `validate_string(xml_string, schema_type)`

Valida cualquier string XML en memoria (útil para los XML recién generados por la BD).

### `generate_report(output_file=None)`

Consolida el reporte `{summary, details}` y opcionalmente lo **escribe a JSON**. El `if output_file` decide si hay escritura; el `return report` termina.

### `print_results()`

Imprime los resultados por consola con colores ANSI. El bucle sobre `self.report['validations']` **termina cuando se recorren todas las validaciones**; por cada error muestra solo los primeros 5 (bucle con `[:5]`) para no saturar.

### Detalle: `fix_namespace` en `fix_and_validate.py`

Agrega el namespace `xmlns="http://www.sii.cl/SiiLce"` al elemento raíz si falta (búsqueda con regex del primer tag). **Finaliza** con `return` en cuanto confirma si ya tiene `xmlns` (`if 'xmlns' in content`) o tras reemplazar el tag (un solo `re.sub(..., count=1)`).

## Relación con el resto del sistema

Los XML que genera el módulo `lce` (desde PostgreSQL) deberían poder validarse con estas herramientas antes de firmarlos/enviarlos. Es el "control de calidad" offline del flujo LCE.