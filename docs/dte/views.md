# Vistas de `dte/views.py`

## Helper `_parse_fields_param(request, fields_default)`

Lee el parámetro de consulta `?fields=campo1,campo2` y devuelve la lista de campos.

**Ciclo y terminación**:
- Si viene `fields` → lo divide por `,` (comprensión de lista con `strip()` para limpiar espacios y filtro para descartar vacíos); **el ciclo termina al recorrer todos los fragmentos**.
- Si no viene → devuelve el valor por defecto.

Es la base de los endpoints "resumidos": el cliente decide qué columnas recibir.

---

## `HealthCheckView(APIView)`

Endpoint de salud. **Ciclo**: `GET` → responde `{"status": "OK", "message": "..."}`.

- `permission_classes = []` y `authentication_classes = []`: **abierto**, sin autenticación (para monitoreo/orquestación). Al no haber permisos, DRF no bloquea nada — el ciclo de autorización simplemente no aplica.

---

## `EntidadViewSet(viewsets.ReadOnlyModelViewSet)`

Solo lectura (`ReadOnlyModelViewSet`): el cliente no puede crear/editar entidades vía esta API (se gestionan con admin u otro mecanismo).

- `get_queryset`: devuelve las entidades de **la empresa actual** con `activo=True`. Si no hay empresa → `Entidad.objects.none()` (queryset vacío; la respuesta será `[]`).
- `list`: aplica `_parse_fields_param` para filtrar las claves del JSON de cada entidad.

**Ciclo de `list`**: si `fields != ["__all__"]`, para cada `item` de `data` reconstruye `{k: v for k, v in item.items() if k in fields}` (comprensión de dict que **termina al recorrer las claves**); si `fields == ["__all__"]` no filtra.

---

## `DocumentoTributarioViewSet(viewsets.ModelViewSet)`

**ModelViewSet**: lista, crea, detalla, actualiza y elimina documentos, más las acciones personalizadas.

### `get_queryset()`

```
¿request.empresa_actual existe?
  SÍ → DocumentoTributario.objects.filter(id_empresa=empresa_actual)
        .order_by("-fecha_emision", "-numero_documento")
  NO → objects.none()   (vacío)
```
- **Filtro por empresa**: pilar del multi-tenancy.
- Orden: los más recientes primero.

### `perform_create(serializer)`

Ciclo al crear:
```
¿existe empresa_actual?
  SÍ → serializer.save(id_empresa=empresa_actual)   (fuerza la empresa del usuario)
  NO → raise PermissionError("No tiene empresa asignada")   ← TERMINA con error
```

Es una **protección**: el cliente nunca decide a qué empresa pertenece el documento; queda forzado a la del usuario autenticado.

### Acción `emitir` (`POST .../emitir/`)

```
documento = get_object()
try:
    result = DTEService.emitir_documento(documento.id_documento)
except DatabaseError as exc:
    # Errores de la base (ej. triggers) → 400 con mensaje
    return Response({"detail": mensaje}, status=400)   ← TERMINA
result["success"]?
  SÍ → Response(result, 200)   ← TERMINA
  NO → Response(result, 400)   ← TERMINA
```

**Qué controla la terminación**: el `try/except DatabaseError` captura los fallos que vienen de PostgreSQL (25000, etc.) y los convierte en **400** (error del cliente), no en 500. Luego, el `success` del resultado determina 200 u otro 400.

### Acción `anular` (`POST .../anular/`)

```
result = DTEService.anular_documento(documento.id_documento)
success? → 200 : 400
```

Idéntico patrón: **el `success` del servicio decide el código HTTP** y termina el ciclo.

### Acción `detalles_completos` (`GET .../detalles_completos/`)

```
result = DTEService.get_documento_con_detalles(documento.id_documento)
result no es None? → Response(result, 200)
None?              → Response({"error": "Documento no encontrado"}, 404)  ← TERMINA
```

### Acción `lista_resumida` (`GET .../lista-resumida/`)

Usa `_parse_fields_param` para devolver solo los campos clave (`id_documento`, `tipo_documento`, `numero_documento`, `folio`, `fecha_emision`, `total`, `estado`) de la lista completa.

---

## `DocumentoTributarioRawListView(APIView)`

Vista dedicada que devuelve el **JSON en bruto** de los documentos tributarios de la empresa, útil para ver la respuesta completa en el navegador.

- `permission_classes = []` y `authentication_classes = []`: **abierta** en desarrollo (como `HealthCheckView`), para poder abrirla en el navegador sin credenciales.
- `serializer_class = DocumentoTributarioSerializer`: misma serialización que el listado principal (`detalles`, `traslado`, `referencias`, `razon_social_entidad`, `rut_entidad`, etc.).

### Ciclo de `get(request)`

```
¿existe request.empresa_actual?
  NO → busca la primera empresa con documentos:
       SELECT DISTINCT id_empresa FROM DocumentoTributario ORDER BY id_empresa
       → Empresa de ese id; si no hay documentos, Empresa.objects.first()
       ¿sigue sin empresa? → Response({"detail": "No hay empresas disponibles"}, 400)   ← TERMINA
queryset = DocumentoTributario.objects.filter(id_empresa=empresa)
           .order_by("-fecha_emision", "-numero_documento")
serializer = DocumentoTributarioSerializer(queryset, many=True)
return Response(serializer.data)   ← TERMINA
```

- **Qué controla la terminación**: la resolución de `empresa_actual`. Al estar abierta sin usuario, el middleware no la asigna, por lo que la vista resuelve la primera empresa **que tenga documentos** (fallback de desarrollo, útil para ver los datos de ejemplo).
- La respuesta es una lista (no paginada) ordenada igual que `List` de `DocumentoTributarioViewSet`: los más recientes primero (`-fecha_emision`, `-numero_documento`).
- Al no aplicar `_parse_fields_param` ni paginación, es la representación "bruta" de la serie.

!!! warning "Seguridad"
    Al ser un endpoint abierto, expone los XML/JSON de documentos sin autenticación. Es intencional para desarrollo; en producción debe protegerse.

---

## `lista_dte(request)` (HTML)

Página HTML en `/api/dte/` que lista los documentos tributarios de la empresa con un botón "Ver XML" por fila, y un **combo de filtro por cliente** (`?cliente=<uuid>`).

**Ciclo**:

```
login_required
empresa = _empresa_del_request(request)   # empresa_actual o primera registrada
¿no hay empresa? → render con error       ← TERMINA
documentos = DocumentoTributario.objects.filter(id_empresa=empresa)
clientes = Entidades de la empresa presentes en document.id_entidad
           (distinct, ordenadas por razon_social)
¿viene ?cliente=<uuid válido de la empresa>?
  SÍ → cliente_seleccionado = esa entidad
       documentos = documentos.filter(id_entidad=cliente_seleccionado)
  UUID inválido o no perteneciente → se ignora el filtro
documentos = documentos.order_by("-fecha_emision", "-numero_documento")
render('dte/lista_dte.html', {empresa, documentos, clientes, cliente_seleccionado})   ← TERMINA
```

- **Qué controla la terminación**: la existencia de empresa. Sin ella se corta con un mensaje; la página es el punto de entrada para llegar a `ver_xml_dte`.
- **Qué controla el filtrado**: el parámetro `cliente` se valida con `UUID()` (el malformado se ignora y no lanza `ValidationError`); luego debe ser una entidad de la misma empresa. El combo se arma con las entidades que **tienen documentos**.
- El `select` de la plantilla reenvía por GET (`onchange="this.form.submit()"`) y hay botones "Filtrar"/"Limpiar".

---

## `ver_xml_dte(request, pk)` (HTML)

Visualiza el **XML de un DTE específico** dentro de la página `/api/dte/documentos/<uuid:pk>/xml/`.

**Ciclo**:

```
login_required
empresa = _empresa_del_request(request); ¿no hay? → render con error        ← TERMINA
documento = DocumentoTributario.objects.filter(id_empresa=empresa, id_documento=pk).first()
¿no existe? → render con error "Documento no encontrado"                     ← TERMINA
xml_content = documento.xml_documento        # XML que dejó el trigger al emitir
¿vacio? → SELECT contabilidad.generar_xml_dte(pk)   # regenera bajo demanda
¿sigue vacio/None? → render con error "No se pudo generar el XML..."          ← TERMINA
render('dte/ver_xml.html', {documento, xml_content})   ← TERMINA
```

- **Qué controla la terminación**: el filtro por `id_empresa` + `pk` determina si existe el documento; el contenido de `xml_content` (guardado por `trigger_generar_xml_documento` o regenerado con `generar_xml_dte`) decide si se muestra o se corta con error.
- El template muestra el XML escapado con botones "Copiar" y "Descargar".

---

## Rutas (`dte/urls.py`)

- Router automático (`DefaultRouter`) registra `documentos` y `entidades`.
- Rutas manuales para `health/`, la raíz HTML, `lista-resumida/`, `api-raw/` y el XML por DTE, registradas antes de incluir el router.

| Ruta | ViewSet/método |
|------|----------------|
| `api/dte/` | `lista_dte` (página HTML) |
| `api/dte/health/` | HealthCheckView |
| `api/dte/documentos/lista-resumida/` | `lista_resumida` (antes que la ruta del router para no colisionar) |
| `api/dte/documentos/api-raw/` | DocumentoTributarioRawListView (`get`) |
| `api/dte/documentos/<uuid:pk>/xml/` | `ver_xml_dte` |
| `api/dte/documentos/...` | DocumentoTributarioViewSet |
| `api/dte/entidades/...` | EntidadViewSet |

!!! note "Orden de rutas"
    `lista-resumida/`, `api-raw/` y `<uuid:pk>/xml/` se registran **antes** de incluir el router para que Django las matchee primero en el ciclo de enrutado y no las confunda con un `pk` literal ("lista-resumida" o "api-raw"). El patrón `<uuid:pk>/xml/` es específico y no compite con las rutas del ViewSet.