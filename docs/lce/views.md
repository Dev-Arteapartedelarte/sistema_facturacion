# Vistas de `lce/views.py`

Este archivo combina **vistas clásicas de Django** (HTML, con `@login_required`) y **endpoints JSON**. Además, hay un bloque preparado de vistas DRF (con `@authentication_classes` / `@permission_classes`) que actualmente **no se usa** (rutas tomadas por las funciones HTML).

## Patrón compartido

Casi toda vista empieza igual:

```python
empresa = getattr(request, "empresa_actual", None)   # lo puso EmpresaMiddleware
if not empresa:
    empresa = Empresa.objects.first()                 # fallback: primera empresa
    if empresa:
        request.empresa_actual = empresa
```

!!! warning "Fallback a `Empresa.objects.first()`"
    Si el middleware no asignó empresa (p. ej. superusuario sin perfil), se toma la primera de la BD. En producción conviene evitarlo; es un mecanismo de desarrollo.

---

## `dashboard_lce(request)`

Dashboard de LCE. **Ciclo**:

```
login_required → ¿no empresa? → render con {} y TERMINA
NO ↓
SELECT DISTINCT año, mes, COUNT(*) 
FROM asiento_contable 
WHERE id_empresa=%s AND estado IN ('CONTABILIZADO','CERRADO')
GROUP BY año, mes ORDER BY año DESC, mes DESC
   ↓
render('lce/dashboard.html', {'empresa':..., 'periodos': periodos})
```

- `periodos` (tuplas de filas) alimenta el selector de período del template.
- La **agregación y orden** ocurre del lado SQL; el `fetchall()` termina la lectura.

---

## `generar_libro_diario(request)` y `generar_libro_mayor(request)`

Descarga el XML del libro como *attachment*.

**Ciclo**:
1. Empresa (con fallback). ¿No hay? → `JsonResponse(400)`. **TERMINA**.
2. Lee `año` y `mes` de `request.GET`. ¿Faltan? → `400`. **TERMINA**.
3. `int(año)` / `int(mes)` en `try`; si `ValueError` → `400 "Año y mes deben ser números"`. **TERMINA**.
4. `connection.cursor()` → `SELECT contabilidad.generar_xml_libro_diario/mayor(...)`:
   - ¿sin resultado? → `400 "No se pudo generar el XML..."`. **TERMINA**.
5. Construye `HttpResponse(xml_content, content_type='application/xml; charset=utf-8')`:
   - Nombre de archivo: `libro_diario_{año}_{mes:02d}_{rut_sin_guion}.xml`.
   - `Content-Disposition: attachment` fuerza la descarga.
6. Devuelve la respuesta HTML. **TERMINA**.

`except Exception as e` → `500` con el mensaje (red final del ciclo).

---

## `generar_diccionario_cuentas(request)`

Igual pero **anual**:
- Lee solo `año` (si falta, usa `datetime.now().year`).
- `SELECT contabilidad.generar_xml_diccionario_cuentas(%s, %s)`.
- Archivo: `diccionario_cuentas_{año}_{rut}.xml`.

---

## `previsualizar_libro_diario(request)`

Muestra el XML del Libro Diario **dentro de una página HTML** (`lce/previsualizar.html`), con error amigable si no hay período.

**Ciclo**:
1. Empresa + período disponibles (misma consulta).
2. ¿Faltan `año`/`mes`? → render sin `xml_content`. **TERMINA en render**.
3. ¿`int()` falla? → render con `error`. **TERMINA**.
4. Genera el XML:
   - Sin resultado → render con `error "No se encontraron datos..."`. **TERMINA**.
   - Con XML → render con `xml_content` y `tipo="Libro Diario"`. **TERMINA**.
5. `except Exception` → render con `error=str(e)`. **TERMINA**.

El estado `xml_content` (o `error`) es lo que **controla el contenido final** del render.

---

## `ver_xml_libro(request, tipo)`

Visualiza en el navegador el XML de un libro por tipo: `diario`, `mayor` o `diccionario`. Es la "vista por Libro" que complementa a las descargas.

**Diccionario de tipos** (dentro de la función):

```
'diario'      → label "Libro Diario",        función generar_xml_libro_diario,        necesita mes SI
'mayor'       → label "Libro Mayor",         función generar_xml_libro_mayor,         necesita mes SI
'diccionario' → label "Diccionario de Cuentas", función generar_xml_diccionario_cuentas, no mes
```

**Ciclo**:
1. Empresa (con fallback). ¿No hay? → render con `error`, **TERMINA**.
2. ¿`tipo` no está en el diccionario? → render con `error "Tipo de libro no válido"`, **TERMINA**.
3. Obtiene `periodos` disponibles (misma consulta agregada de `dashboard_lce`).
4. ¿Viene `año`? Si no, render del selector sin XML (estado `xml_content=None`). **TERMINA**.
   - `int(año)` falla → `error`. **TERMINA**.
5. Según tipo y la presencia/ausencia de `mes`, llama a la función SQL correspondiente:
   - `diccionario` → solo `año`.
   - `diario`/`mayor` → exige `año` y `mes`; falta el mes → `error "Se requiere año y mes"`. **TERMINA**.
6. `int(mes)` falla → `error "Mes debe ser un número"`. **TERMINA**.
7. ¿`xml_content` vacío? → `error` de datos insuficientes. **TERMINA**.
8. Render de `lce/ver_xml.html` con `xml_content`, `tipo_label`, `necesita_mes`, `año`, `mes`. **TERMINA**.

**Qué controla la terminación**: el `mapping de tipos` valida el libro, y los `errores de validación/generación` cortan antes del render final. La plantilla decide qué bloques mostrar según `xml_content`, `error` y `necesita_mes`.

---

## `api_periodos(request)`

API JSON de períodos disponibles.

```
SELECT DISTINCT año, mes, COUNT(*) FROM asiento_contable ... GROUP BY ...
   ↓
for row in cursor.fetchall():                     # bucle que termina con las filas
    data.append({'año': row[0], 'mes': row[1], 'total_asientos': row[2]})
   ↓
return JsonResponse({'periodos': data})
```

## `api_cal(request)`

API JSON de CAL disponibles (libros autorizados):

```
SELECT id_cal, tipo_libro, numero_cal, fecha_autorizacion FROM cal_libros_electronicos
WHERE id_empresa=%s AND activo=true ORDER BY tipo_libro
   ↓
for row in cursor.fetchall():                     # bucle que termina con las filas
    data.append({'id': str(row[0]), 'tipo_libro': row[1], 'numero_cal': row[2],
                 'fecha_autorizacion': row[3].isoformat() if row[3] else None})
   ↓
return JsonResponse({'cal': data})
```

- `str(row[0])`: el UUID se serializa como texto para JSON.
- `row[3].isoformat() if row[3] else None`: convierte fecha a string o deja `None`.

---

## Bloque DRF (sin usar actualmente)

Al inicio hay imports de DRF (`APIView`, `BasicAuthentication`, etc.) y decoradores `@authentication_classes`/`@permission_classes`, pero **no hay vistas que los usen**: las rutas existentes son funciones. Es un bloque *vestigial* preparado para migrar la API de LCE a DRF (con autenticación básica igual que el resto).

## Rutas (`lce/urls.py`)

| Ruta | Vista | Tipo |
|------|-------|------|
| `/lce/` | `dashboard_lce` | HTML |
| `/lce/libro-diario/` | `generar_libro_diario` | HTML/descarga |
| `/lce/libro-mayor/` | `generar_libro_mayor` | HTML/descarga |
| `/lce/diccionario/` | `generar_diccionario_cuentas` | HTML/descarga |
| `/lce/previsualizar/` | `previsualizar_libro_diario` | HTML |
| `/lce/ver-xml/<tipo>/` | `ver_xml_libro` | HTML (dónde `<tipo>` = `diario`, `mayor`, `diccionario`) |
| `/lce/api/periodos/` | `api_periodos` | JSON |
| `/lce/api/cal/` | `api_cal` | JSON |