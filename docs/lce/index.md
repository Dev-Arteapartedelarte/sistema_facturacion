# Módulo `lce` — Libros Contables Electrónicos

El módulo `lce` maneja la generación, firma y preparación de los **Libros Contables Electrónicos (LCE)** que las empresas chilenas deben enviar al SII: **Libro Diario**, **Libro Mayor** y **Diccionario de Cuentas**.

## ¿Qué son los LCE?

Desde 2015 (Ley N° 20.780) los contribuyentes deben llevar sus libros contables en formato **XML** según los esquemas **XSD del SII**. Este módulo se encarga de:

1. **Generar** el XML a partir de los datos contables (mediante funciones almacenadas de PostgreSQL).
2. **Firmar** el XML (agregar datos del firmante y firma digital con certificado).
3. **Guardar** el resultado como pendiente de envío.

## Qué contiene

| Archivo | Propósito |
|---------|-----------|
| `views.py` | Vistas HTML (dashboard, descarga de XML, previsualización) y endpoints API JSON |
| `services.py` | `LCEService`: puente a las funciones almacenadas de generación de XML |
| `signer.py` | `LCESigner`: firma digital del XML |
| `urls.py` | Rutas (HTML + API) |
| `models.py` | Vacío (los modelos viven en `core`) |

## Endpoints

Bajo `/lce/` (HTML) y `/api/lce/` (API):

| Ruta | Función |
|------|---------|
| `/lce/` | Dashboard LCE (períodos disponibles) |
| `/lce/libro-diario/?año=&mes=` | Descarga XML del Libro Diario |
| `/lce/libro-mayor/?año=&mes=` | Descarga XML del Libro Mayor |
| `/lce/diccionario/?año=` | Descarga XML del Diccionario de Cuentas |
| `/lce/previsualizar/` | Previsualización del Libro Diario en HTML |
| `/api/lce/periodos/` | JSON con períodos disponibles |
| `/api/lce/cal/` | JSON con los CAL (Códigos de Autorización de Libros) |

## Concepto clave: el XML viene de la base de datos

La generación del XML **no la hace Python**: la hace PostgreSQL con funciones como:

```sql
SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s);
SELECT contabilidad.generar_xml_libro_mayor(%s, %s, %s);
SELECT contabilidad.generar_xml_diccionario_cuentas(%s, %s);
```

Python solo ejecuta la función y recibe el texto XML como resultado. Esto mantiene la coherencia con el resto del sistema (la lógica vive en la BD).

## Documentación detallada

- [Servicios](services.md): `LCEService`.
- [Firma digital](signer.md): `LCESigner` (firma, preparación y guardado del envío).
- [Vistas](views.md): cada endpoint.
- [Referencia API](api_reference.md): autogenerada.