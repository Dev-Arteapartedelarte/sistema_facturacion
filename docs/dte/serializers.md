# Serializers de `dte/serializers.py`

Los **serializers** de Django REST Framework convierten:

- Objeto Python/modelo → **JSON** (para enviar al cliente).
- JSON del cliente → **objeto validado** (para crear/actualizar en BD).

Aquí son importantes porque contienen **la validación y el cálculo de montos** (IVA 19%, totales).

## `DocumentoDetalleSerializer`

Serializa cada línea del documento. Todos sus campos son del modelo `DocumentoDetalle`.

## `DocumentoTrasladoSerializer`

Serializa los datos de traslado (guías de despacho).

- `required = False`: el bloque traslado es opcional en general.
- **`to_internal_value`**: **normaliza cadenas vacías a `None`** antes de validar (un dict con `"patente": ""` pasa a `"patente": None`). Evita que campos vacíos se rechacen como inválidos.

**Ciclo de `to_internal_value`**: recibe `data` (dict JSON) → si es dict, recorre cada `(key, value)` con una **comprensión de dict** (bucle que **termina cuando se recorren todas las claves**) convirtiendo strings vacíos en `None` → delega en `super().to_internal_value(data)` para la validación estándar de DRF.

## `DocumentoReferenciaSerializer`

Serializa las referencias a otros documentos. También `required = False` (la referencia es opcional según el tipo de documento).

## `EntidadSerializer`

Lista campos clave de la entidad: `id_entidad`, `rut`, `razon_social`, `giro`.

## `DocumentoTributarioSerializer`

El serializer principal. Anida:

- `detalles`: las líneas (`documentodetalle_set`).
- `traslado`: datos de transporte (guía).
- `referencias`: documentos referenciados.
- `razon_social_entidad`, `rut_entidad`: datos **de solo lectura** del cliente (tomados de `id_entidad`).

### Campos de solo lectura

`numero_documento`, `folio`, `estado`, `contabilizado`, `fecha_contabilizacion`, `fecha_creacion`, `fecha_modificacion` son `read_only_fields`: **el cliente no puede escribirlos** (los asigna el sistema/BD).

### `validate(self, data)`

Es el corazón de la validación. **Ciclo de cada operación y qué lo termina:**

#### 1. Regla para GUIA_DESPACHO
```
¿tipo_documento == "GUIA_DESPACHO"?
  SÍ → ¿no viene "traslado"?
         SÍ → raise ValidationError("La guía de despacho requiere los datos de traslado...")
               ← TERMINA (rechaza la petición)
         NO → verifica campos obligatorios del traslado:
              [tipo_despacho, ind_traslado, dir_destino, comuna_destino,
               ciudad_destino, fecha_salida, hora_salida]
              Si falta alguno → raise ValidationError  ← TERMINA
```

Esto implementa la **Resolución Ex. SII N° 154/2025** que exige datos de traslado en las guías.

#### 2. Guías y facturas exentas (sin IVA)
```
¿tipo_documento in ("GUIA_DESPACHO", "FACTURA_EXENTA")?
  SÍ → data["iva"] = 0 ; data["total"] = neto + exento
       return data   ← TERMINA acá (no calcula IVA)
```

#### 3. Cálculo automático de IVA (19%)
```
¿iva == 0 y el cliente NO envió "iva"?
  SÍ → iva = neto * 0.19 ; redondea a 2 decimales (quantize)
```

**Qué controla la finalización**: la condición `"iva" not in self.initial_data` — solo auto-calcula si el cliente **no lo mandó explícitamente**.

#### 4. Cálculo automático del total
```
¿total == 0 y el cliente NO envió "total"?
  SÍ → total = neto + iva + exento ; redondea
```

#### 5. Verificación de coherencia
```
total_calculado = neto + iva + exento
¿|total - total_calculado| > 0.01?
  SÍ → raise ValidationError("El total no coincide con neto + iva + exento")
       ← TERMINA el ciclo
NO → return data   ← fin válido del ciclo de validación
```

El margen de `0.01` tolera redondeos de centavos.

### `validate_neto` y `validate_exento`

Validaciones individuales de campo:
```
¿valor < 0 ? → raise ValidationError("...no puede ser negativo")  ← TERMINA
NO → return value
```

### `create(validated_data)` — creación atómica

Decorado con `@transaction.atomic` (todo se crea en una transacción; si algo falla, **rollback total**).

**Ciclo**:
1. Aparta las listas anidadas: `detalles_data`, `traslado_data`, `referencias_data`.
2. Obtiene `id_empresa` (requerido; si falta → `raise ValidationError` y **termina**).
3. **SQL para numerar**: `SELECT COALESCE(MAX(numero_documento), 0) + 1` — la BD da el siguiente número de documento para esa empresa (**termina el ciclo de numeración** evitando colisiones con `MAX`).
4. Fija `numero_documento` y `estado = "BORRADOR"` (todo documento nuevo nace en borrador).
5. Crea el documento padre con ORM.
6. **Bucles** sobre `detalles_data`, `traslado_data` y `referencias_data`:
   - Cada `for ... in ...` **termina cuando se recorren todos los elementos** de su lista.
   - Cada iteración agrega `id_documento` (relación con el documento padre) y crea su registro.
7. `return documento` → cierra y, al salir del decorador, **hace commit** de la transacción.

### `update(instance, validated_data)` — actualización atómica

1. Aparta datos anidados.
2. Recorre `validated_data.items()` con un bucle `for attr, value`: hace `setattr` sobre la instancia (**bucle termina al agotar las claves**) y guarda.
3. Si viene `traslado_data` → `update_or_create` (crea o actualiza el traslado del documento; es un 1 a 1).
4. Si viene `detalles_data` → **borra todas las líneas existentes** y las recrea (patrón "reemplazo completo").
5. Igual para `referencias_data`.
6. `return instance`.

**Qué controla la finalización**: los `if ... is not None` — el serializer solo toca cada sub-bloque si el cliente lo envió (`None` = no lo mandó = no tocar). Esto evita borrados accidentales de líneas que no se querían modificar.