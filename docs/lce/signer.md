# Firma digital de LCE: `lce/signer.py`

`LCESigner` implementa la **firma y preparación de envío** de los Libros Contables Electrónicos. Usa dos bibliotecas:

- **`lxml`** → parseo y manipulación del XML (agregar nodos `RutFirma`, `TmstFirma`).
- **`cryptography`** → carga del certificado PFX y firma digital.

---

## Contexto técnico: ¿qué es firmar un XML en el SII?

El SII no exige el estándar completo XML-DSig para los LCE; exige que el XML contenga:

- **`RutFirma`**: el RUT del firmante (contribuyente).
- **`TmstFirma`**: fecha/hora de la firma.
- La firma digital con el certificado electrónico.

Este módulo implementa la primera parte (inyectar `RutFirma`/`TmstFirma` en la ubicación correcta del XML) y esboza la segunda (firma con PFX).

---

## `agregar_firma(xml_content, rut_firma, timestamp=None)`

Agrega los nodos `RutFirma` y `TmstFirma` al XML.

### Ciclo del método y qué lo termina

```
¿xml_content es bytes? → decodificar a str (UTF-8)
¿no hay timestamp?     → usar "ahora" (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
doc = etree.fromstring(...)                    # parsea el XML
   │
   ▼  Búsqueda por tipo de libro (cada una es un intento independiente):
   ├─ doc.find('.//LceDiarioRes')  → si existe, inserta en DocumentoDiarioRes
   │     ↓  return etree.tostring(...)         ← TERMINA (XML firmado)
   ├─ doc.find('.//LceMayorRes')   → idem        ← TERMINA
   ├─ doc.find('.//DocumentoDiccionario') → idem  ← TERMINA
   ▼
raise ValueError('No se pudo agregar firma al XML')  ← TERMINA con error
```

**Qué controla la finalización**: el **primer** `return` que encuentre su tipo de libro **detiene el ciclo** (if/elif encadenados); si ningún patrón coincide, se lanza `ValueError` — el XML no correspondía a ningún LCE conocido.

Los `.find('.//X')` buscan con la sintaxis de **XPath** de lxml; devuelven el primer nodo que coincide o `None`.

## `firmar_xml(xml_content, pfx_path, pfx_password)`

Firma digitalmente el XML usando el certificado **PFX**.

### Ciclo del método y qué lo termina

```
¿no existe el archivo PFX? → raise ValueError("Archivo PFX no encontrado")
                              ← TERMINA
NO ↓
pfx_data = read(pfx_path)                     # lee el certificado
   ↓
try: private_key, certificate, _ = pkcs12_load_key_and_certificates(...)
except → raise ValueError("Error al cargar certificado PFX")  ← TERMINA
   ↓
digest = sha1(xml_content.encode())           # hash SHA-1 (lo que pide el SII)
   ↓
try: signature = private_key.sign(digest, PKCS1v15(), SHA1())
except → raise ValueError("Error al firmar")  ← TERMINA
   ↓
return xml_content   (con el código actual)
```

### ⚠️ Estado actual (implementación parcial)

El método **calcula la firma** (digest SHA-1 + firma RSA PKCS#1 v1.5 con SHA-1, codificada en base64) pero **no inyecta aún el nodo `Signature` en el XML**: devuelve el `xml_content` original. El comentario en el código lo indica explícitamente:

```python
# Aquí se debe construir el nodo Signature según el XSD del SII
# Por ahora, devolvemos el XML con la firma base64
return xml_content
```

**Qué controla la terminación en producción**: cada `raise ValueError` corta con error; cuando se complete la implementación, el `return` del XML firmado terminará el ciclo. Hasta entonces, la firma *real* del XML frente al SII no es completa — solo se agregan `RutFirma`/`TmstFirma`.

## `preparar_envio_lce(empresa_id, año, mes, tipo_libro)`

Prepara el envío de un LCE: genera el XML sin firmar y le agrega la firma básica.

### Ciclo del método y qué lo termina

```
1. Generar XML: según tipo_libro ("diario"|"mayor"|"diccionario")
   ├─ diario     → SELECT generar_xml_libro_diario(%s,%s,%s)
   ├─ mayor      → SELECT generar_xml_libro_mayor(%s,%s,%s)
   ├─ diccionario→ SELECT generar_xml_diccionario_cuentas(%s,%s)
   else          → raise ValueError("Tipo de libro no válido")  ← TERMINA
   ↓
   ¿no hay resultado? → raise ValueError("No se pudo generar el XML")
                        ← TERMINA
   ↓
2. Obtener RUT de la empresa: SELECT rut FROM empresa WHERE id_empresa = %s
   ¿no hay RUT? → raise ValueError("No se encontró RUT de la empresa") ← TERMINA
   ↓
3. xml_firmado = LCESigner.agregar_firma(xml_content, rut_firma)
                 (si falla, propaga el ValueError ← TERMINA)
   ↓
return { 'xml_firmado': ..., 'rut_firma': ..., 'tipo_libro': ...,
         'año': ..., 'mes': ... }
```

**Qué controla la finalización**: cada `raise ValueError` detiene el ciclo con error descriptivo; el único `return` exitoso cierra el método con el dict ya listo.

## `guardar_envio_lce(empresa_id, tipo_libro, tipo_envio, año, mes, xml_con_firma)`

Persiste el XML firmado como enviable en `LibrosPendientesEnvio` (modelo de `core`).

### Ciclo del método y qué lo termina

```
libro, created = LibrosPendientesEnvio.objects.update_or_create(
    id_empresa_id=..., tipo_libro=..., tipo_envio=..., anio=..., mes=...,
    defaults={ 'xml_firmado': xml_con_firma, 'estado': 'FIRMADO',
               'fecha_generacion': now, 'fecha_actualizacion': now })
return libro
```

- `update_or_create` **busca** el registro (por empresa + libro + período) y:
  - Lo **actualiza** si existe (`defaults`).
  - Lo **crea** si no (con aquellos campos como clave de unicidad).
- Estado → `FIRMADO`: el ciclo avanza a la etapa de envío.
- **Qué controla el fin del ciclo**: la búsqueda termina al confirmar existencia/no-existencia; el `return libro` cierra el método.

## `validar_firma_xml(xml_content)`

Verifica que el XML tenga `RutFirma` y `TmstFirma`.

### Ciclo del método y qué lo termina

```
doc = etree.fromstring(xml_content)
rut_firma  = doc.find('.//RutFirma')
tmst_firma = doc.find('.//TmstFirma')
├─ ¿rut_firma es None?   → return (False, "Falta RutFirma")   ← TERMINA
├─ ¿tmst_firma es None?  → return (False, "Falta TmstFirma")  ← TERMINA
└─ return (True, f"RutFirma: ..., TmstFirma: ...")            ← TERMINA
except Exception as e → return (False, f"Error: {e}")          ← TERMINA
```

Devuelve una tupla `(bool, mensaje)` que la vista puede mostrar o loguear. El `try/except` global es la última red: cualquier XML malformado termina el ciclo con `(False, error)` sin romper al llamante.