# Servicios de `dte/services.py`

`DTEService` agrupa la lógica de negocio de los documentos, fuera de las vistas (patrón *service layer*). Métodos estáticos: no requieren instanciar la clase.

---

## `emitir_documento(id_documento) -> dict`

Cambia el estado de un documento de `BORRADOR` a `EMITIDO`.

### Ciclo del método

```
transaction.atomic()                     # 1. Abre una transacción
   │
   ▼
DocumentoTributario.objects.get(id_documento)   # 2. Carga el documento
   │
   ▼
┌─ ¿documento.estado != "BORRADOR"?      # 3. Guarda de seguridad
│   SÍ → return {"success": False, "error": ...}   ← TERMINA el ciclo (sin emitir)
│   NO ↓
▼
documento.estado = "EMITIDO"             # 4. Cambia estado
documento.save()                         #    (dispara triggers de PostgreSQL:
   │                                      #     folio, asiento contable, etc.)
   ▼
documento.refresh_from_db()              # 5. Recarga los campos actualizados por la BD
   │
   ▼
return {"success": True, "folio": ..., "estado": ..., "contabilizado": ...}
```

### Qué controla la finalización del ciclo

- **`transaction.atomic()`**: si algo falla a mitad, **se revierte todo** (rollback) y la excepción propaga. El `with` garantiza cerrar la transacción al salir.
- **Guard `if documento.estado != "BORRADOR"`**: si el documento ya fue emitido/anulado/rechazado, se retorna error y el ciclo **termina ahí**: el documento no se vuelve a emitir.
- **`documento.save()` / `refresh_from_db()`**: la BD es la que "termina" la transición aplicando sus triggers; al refrescar, Python ve el resultado final.
- El `return` de éxito cierra el método.

### Conexión con la base de datos

La lógica financiera real (asignar folio, generar asiento) la hacen los **triggers de PostgreSQL**. Python solo hace el *commit* lógico del cambio de estado.

---

## `anular_documento(id_documento) -> dict`

Anula un documento (estado → `ANULADO`).

### Ciclo del método

```
transaction.atomic()
   ▼
documento = get(id_documento)
   ▼
┌─ ¿documento.estado in ("ANULADO", "RECHAZADO_SII")?
│   SÍ → return {"success": False, "error": "El documento ya está ..."}  ← TERMINA
│   NO ↓
▼
documento.estado = "ANULADO"
documento.save()
   ▼
return {"success": True, "id_documento": ..., "estado": ...}
```

### Qué controla la finalización del ciclo

- **Guard**: no se pueden anular dos veces ni anular documentos que el SII ya rechazó (los rechazados quedan como evidencia, no se anulan localmente). Ese `if` es el "freno" del ciclo.
- `transaction.atomic()` revierte ante cualquier excepción.

---

## `get_documento_con_detalles(id_documento)`

Obtiene un documento **con todas sus líneas** en una sola consulta SQL (en lugar de varias consultas ORM).

### Ciclo del método

```
with connection.cursor() as cursor:
    cursor.execute( QUERY...)          # JOIN documento + entidad + detalles
    │                                  #  json_agg(...) agrupa líneas por documento
    ▼
    row = cursor.fetchone()            # una sola fila (o None)
        │
        ▼
        ¿row?
           SÍ → return {dict con todos los campos}   ← TERMINA
           NO → return None                           ← TERMINA
```

### Qué hace y qué termina el ciclo

- El **bucle de agregación ocurre del lado SQL**: `json_agg(json_build_object(...) ORDER BY dd.numero_linea)` convierte todas las líneas en un array JSON ordenado por número de línea — **la BD itera las líneas y termina cuando las agrupa todas**.
- En Python solo hay un `fetchone()`: devuelve la única fila y termina.
- Si no existe documento → `None` (el llamante responderá 404).

```python
# Estructura devuelta
{
  "id_documento": ..., "tipo_documento": ..., "numero_documento": ...,
  "folio": ..., "fecha_emision": ..., "estado": ..., "neto": ...,
  "iva": ..., "total": ..., "entidad_nombre": ..., "entidad_rut": ...,
  "detalles": [ {id_detalle, numero_linea, descripcion, cantidad, precio_unitario, monto_neto, monto_total}, ... ]
}
```

### Sobre el SQL directo

Este método usa SQL crudo en vez del ORM porque necesita una **agregación JSON** y un *JOIN* que en el ORM sería más verboso y menos eficiente. El `with connection.cursor()` libera el cursor automáticamente al salir.