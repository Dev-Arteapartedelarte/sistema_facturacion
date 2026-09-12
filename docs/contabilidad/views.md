# Vistas de `contabilidad/views.py`

Los ViewSets son de solo lectura y exigen `IsAuthenticated` + `EmpresaPermission` (multiempresa). Además hay vistas HTML de lectura (`lista_asientos`).

## Helper `_parse_fields_param(request, fields_default)`

Igual que en `dte` (ver [vistas dte](../dte/views.md)): parsea `?fields=a,b,c` a lista, con ciclo que **termina al recorrer todos los fragmentos** o al devolver el default si no viene el parámetro.

---

## Helper `_empresa_del_request(request)`

Resuelve la empresa para las vistas HTML: usa `request.empresa_actual` (asignado por el middleware) y, si no existe, cae a `Empresa.objects.first()` y lo cachea en el request. Base del multi-tenancy de `lista_asientos`.

---

## `lista_asientos(request)` (HTML)

Página HTML en `/api/contabilidad/` que lista los asientos de la empresa con un **combo de filtro por tipo de asiento** (`?tipo=<tipo_asiento>`).

**Ciclo**:

```
login_required
empresa = _empresa_del_request(request)
¿no hay empresa? → render con error                     ← TERMINA
asientos = AsientoContable.objects.filter(id_empresa=empresa)
tipos = valores distintos de tipo_asiento presentes en la BD de la empresa
¿?tipo está en tipos?  (VARCHAR exacto, ej. CIERRE_ANUAL)
  SÍ → asientos = asientos.filter(tipo_asiento=tipo)
  NO → se ignora el filtro (muestra todos)
asientos = select_related(id_libro, id_periodo)
           .order_by("-fecha_asiento", "-numero_asiento")
render('contabilidad/lista_asientos.html',
       {empresa, asientos, tipos_options, tipo_seleccionado})   ← TERMINA
```

- **Qué controla la terminación**: la existencia de empresa (corte con mensaje si no la hay).
- **Qué controla el filtrado**: `tipo` solo se aplica si es un valor **ya presente** en la BD de esa empresa (evita respuestas vacías por filtros inexistentes). El combo se arma con esos valores y su etiqueta desde `AsientoContable.TIPO_ASIENTO_CHOICES`.
- `select_related` precarga `id_libro` y `id_periodo` (evita N+1 al mostrar nombre de libro y año-mes del período).
- El `select` reenvía por GET (`onchange="this.form.submit()"`), con botones "Filtrar"/"Limpiar".

---

## `AsientoContableViewSet`

### `get_queryset()`

```
¿existe empresa_actual?
  SÍ → AsientoContable.objects.filter(id_empresa=empresa_actual)
        .order_by("-fecha_asiento", "-numero_asiento")
  NO → objects.none()
```

Filtra por empresa y ordena de más reciente a más antiguo.

### Acción `detalles` (`GET .../detalles/`)

Muestra las **líneas** de un asiento:

```
asiento = get_object()                    # (aplica permisos por objeto)
detalles = AsientoDetalle.objects.filter(id_asiento=asiento.id_asiento)
           .order_by("numero_linea")      # orden ascendente: 1, 2, 3...
serializer = AsientoDetalleSerializer(detalles, many=True)
return Response(serializer.data)
```

**Ciclo y terminación**: DRF serializa todos los detalles (bucle interno de DRF que termina al recorrer el queryset completo); el `order_by("numero_linea")` define el orden de lectura de la BD.

### Acción `balance_comprobacion` (`GET .../balance_comprobacion/`)

Llama a la función almacenada:

```sql
SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)
```

**Ciclo**:
```
¿no hay empresa_actual? → Response(403 "No tiene empresa asignada")  ← TERMINA
NO ↓
con connection.cursor() as cursor:
    cursor.execute(...)
    columns = [col[0] for col in cursor.description]   # nombres de columnas
    results = []
    for row in cursor.fetchall():                       # bucle sobre filas
        results.append(dict(zip(columns, row)))         #   fila → dict
    return Response(results)                            # ← TERMINA
```

- El `for row in cursor.fetchall()` **termina cuando no quedan filas**.
- `dict(zip(columns, row))` empareja cada nombre con su valor (bucle implícito sobre columnas).
- `with connection.cursor()` libera el cursor al salir.

### Acción `lista_resumida` (`GET .../lista-resumida/`)

Aplica `_parse_fields_param` con campos clave (`id_asiento`, `numero_asiento`, `fecha_asiento`, `tipo_asiento`, `estado`, `total_debe`, `total_haber`, `empresa`) a la lista completa, limitando el JSON entregado.

---

## `PeriodoContableViewSet`

Consulta períodos contables (`id_empresa` + `order_by("-año", "-mes")`). `get_queryset()` sigue el mismo patrón (filtro empresa o `none()`).

---

## `LibroContableViewSet`

Consulta el catálogo de libros contables de la empresa.

---

## `PlanCuentasViewSet`

Consulta el plan de cuentas. Además **filtra por `tipo_cuenta`**:

```
queryset = PlanCuentas.objects.filter(activo=True)
¿existe empresa_actual? → filter(id_empresa=empresa_actual)
tipo = request.query_params.get("tipo")
¿tipo? → filter(tipo_cuenta=tipo)      # ej. ?tipo=ACTIVO
return queryset
```

**Ciclo y terminación**: cada `filter()` **acumula** restricciones (QuerySet lazy); el ciclo de ejecución real ocurre cuando DRF *materializa* el queryset al serializar (en ese momento PostgreSQL ejecuta el `SELECT` y devuelve las filas; el `for` interno termina al agotarlas).

---

## Enrutado (`contabilidad/urls.py`)

- Ruta manual `""` → `lista_asientos` (página HTML en `/api/contabilidad/`), registrada **antes** del router.
- Router con `asientos`, `periodos`, `libros`, `plan-cuentas`.
- Ruta manual `asientos/lista-resumida/` **antes** del router (evita colisión como en dte).