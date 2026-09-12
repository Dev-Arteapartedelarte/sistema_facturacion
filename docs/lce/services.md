# Servicios de `lce/services.py`

## `LCEService`

Capa de servicio que **invoca las funciones almacenadas** del esquema `contabilidad` para generar los XML de los LCE. Métodos estáticos.

Todos los métodos siguen el mismo ciclo:

```
with connection.cursor() as cursor:
    cursor.execute("SELECT contabilidad.funcion(...)", [params])
    result = cursor.fetchone()          # ← lee el resultado y termina la lectura
    if result and result[0]:
        return result[0]                # ← TERMINA: XML generado
    return None                          # ← TERMINA: sin datos para el período
```

**Qué controla la finalización del ciclo**:
- `with connection.cursor()` cierra el cursor automáticamente.
- `fetchone()` devuelve una fila o `None` — fin de la lectura.
- La comprobación `if result and result[0]` distingue "función devolvió XML" (retorna el texto) de "no hay datos" (retorna `None`); el llamante decide el mensaje de error.

---

## Métodos

### `generar_xml_libro_diario(empresa_id, año, mes)`

- **Qué hace**: invoca `contabilidad.generar_xml_libro_diario(%s, %s, %s)` y devuelve el XML del Libro Diario del período `año`/`mes`.
- **Qué termina el ciclo**: el `fetchone()` y la sentencia de retorno; `None` si el período no tiene asientos contabilizados/cerrados.

### `generar_xml_libro_mayor(empresa_id, año, mes)`

- Análogo al anterior con `generar_xml_libro_mayor` (Libro Mayor).

### `generar_xml_diccionario_cuentas(empresa_id, año)`

- Invoca `generar_xml_diccionario_cuentas(%s, %s)` (sin `mes`: el diccionario es anual).
- Devuelve el XML del Diccionario de Cuentas o `None` si no está configurado.

### `obtener_periodos_disponibles(empresa_id)`

- Consulta los períodos con asientos `CONTABILIZADO`/`CERRADO`:

```sql
SELECT DISTINCT
    EXTRACT(YEAR FROM fecha_asiento)::INT as año,
    EXTRACT(MONTH FROM fecha_asiento)::INT as mes,
    COUNT(*) as total_asientos
FROM asiento_contable
WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
GROUP BY EXTRACT(YEAR ...), EXTRACT(MONTH ...)
ORDER BY año DESC, mes DESC
```

- **Ciclo y terminación**: `fetchall()` devuelve todas las filas y **termina la lectura de la BD**; el `GROUP BY` + `COUNT(*)` agrega los asientos por mes del lado SQL (el bucle de conteo ocurre en la BD y termina al agrupar todo).
- Devuelve una tupla de filas `(año, mes, total_asientos)`.

### `obtener_cal_disponibles(empresa_id)`

- Devuelve los **CAL** (Códigos de Autorización de Libros) activos de la empresa:

```sql
SELECT id_cal, tipo_libro, numero_cal, fecha_autorizacion
FROM cal_libros_electronicos
WHERE id_empresa = %s AND activo = true
ORDER BY tipo_libro
```

- **Ciclo y terminación**: `fetchall()` recolecta todas las filas; `ORDER BY tipo_libro` controla el orden en que se recorren/entregan.

---

## Relación con las vistas

Las vistas de `lce/views.py` usan estos métodos (o ejecutan el `SELECT` directamente). La diferencia: `LCEService` encapsula la consulta para reutilizarla; algunas vistas ejecutan su propio SQL porque `lce/views.py` fue escrito antes que `services.py` y no migró todo.