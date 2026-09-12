# Consultas a funciones almacenadas: `core/db_helpers.py`

La clase `DBHelpers` es el **puente Python ↔ PostgreSQL**: sus métodos estáticos ejecutan las funciones almacenadas del esquema `contabilidad` usando `connection.cursor()`.

Todas siguen el mismo patrón:

```
with connection.cursor() as cursor:
    cursor.execute("SELECT contabilidad.funcion(%s, ...)", [parametros])
    result = cursor.fetchone()        # ← cierra la lectura
    return result[0] if result else <default>
```

**Qué controla la finalización del ciclo**:
- `with connection.cursor()` → al salir del bloque, el cursor y la transacción se cierran (context manager de Django).
- `cursor.fetchone()` → devuelve UNA fila (o `None`) y **termina la lectura** inmediatamente.
- Los `if result ... else ...` → proporcionan un valor por defecto si la función no devolvió nada, evitando que un `None` rompa al llamante.

---

## Métodos

### `obtener_siguiente_numero(id_empresa, tipo, id_libro=None) -> int`

Llama a `contabilidad.obtener_siguiente_numero(%s, %s, %s)`.

- **Qué hace**: obtiene el siguiente número de secuencia para asientos o pagos (numeración atómica gestionada por PostgreSQL para evitar duplicados).
- **Qué controla su terminación**: el `fetchone()` devuelve el número; si no hay resultado, retorna `1` (arranque de la secuencia).
- **Tipo**: `tipo` (ej. `'ASIENTO'`, `'PAGO'`) distingue la secuencia; `id_libro` opcional particulariza por libro.

### `obtener_siguiente_folio_sii(id_empresa, tipo_documento) -> int`

Llama a `contabilidad.obtener_siguiente_folio_sii(%s, %s::tipo_documento_tributario)`.

- El segundo parámetro se castea explícitamente al **tipo enumerado** `tipo_documento_tributario` de PostgreSQL (`::tipo_documento_tributario`), que valida que el tipo sea uno de los permitidos.
- **Qué hace**: avanza el folio SII dentro del rango autorizado por el CAF.
- **Qué controla su terminación**: cuando el rango de folios se agota, la función no devuelve valor → retorna `None`.

### `generar_asiento_documento(id_documento) -> UUID`

Llama a `contabilidad.generar_asiento_documento(%s)`.

- **Qué hace**: genera automáticamente el asiento contable de una factura/documento (GASTO, IVA, etc.) según la configuración de automatización.
- **Qué controla su terminación**: retorna el `id_asiento` creado. Si no hay resultado, retorna `None` (por ejemplo, si el documento no está listo para contabilizar).

### `generar_asiento_pago(id_pago) -> UUID`

Llama a `contabilidad.generar_asiento_pago(%s)`.

- Igual que el anterior pero para pagos/cobros.

### `validar_asiento_cuadrado(id_asiento) -> bool`

Llama a `contabilidad.validar_asiento_cuadrado(%s)`.

- **Qué hace**: verifica la **partida doble**: total DEBE == total HABER.
- **Qué controla su terminación**: la función devuelve `True/False`; si no hay resultado, por precaución retorna `False` (asiento no validado = no cuadrado).

### `obtener_periodo_contable(id_empresa, fecha) -> UUID`

Llama a `contabilidad.obtener_periodo_contable(%s, %s::date)`.

- **Qué hace**: obtiene el período contable al que pertenece una fecha, **creándolo si no existe** (la función almacenada se encarga del "apertura" automática del mes).
- **Qué controla su terminación**: retorna el `id_periodo`; `None` si no pudo determinarse.

---

## Uso típico

```python
from core.db_helpers import DBHelpers

siguiente_numero = DBHelpers.obtener_siguiente_numero(empresa.id_empresa, "ASIENTO")
siguiente_folio = DBHelpers.obtener_siguiente_folio_sii(empresa.id_empresa, "FACTURA_ELECTRONICA")
```

Estos métodos se invocan desde servicios (DTE, LCE) cuando la lógica no está cubierta por los triggers automáticos.