# Serializers de `contabilidad/serializers.py`

## `AsientoDetalleSerializer`

Serializa cada línea del asiento, **enriqueciendo** datos de relaciones para que el cliente no tenga que hacer consultas adicionales:

- `codigo_cuenta`, `nombre_cuenta`: desde `id_cuenta`.
- `razon_social_entidad`: desde `id_entidad` (opcional, `allow_null`).

Campos: `id_detalle`, `numero_linea`, `id_cuenta`, `codigo_cuenta`, `nombre_cuenta`, `tipo_movimiento`, `monto`, `id_entidad`, `razon_social_entidad`, `glosa`.

**Qué controla la terminación del ciclo**: son campos `read_only` de tipo `source="..."`: DRF los lee recorriendo la relación (bucle interno de serialización que termina con cada fila); nada de esto es escribible por el cliente.

---

## `AsientoContableSerializer`

Serializa un asiento completo con sus líneas anidadas y datos legibles:

- `detalles`: todas las líneas (`asientodetalle_set`, `read_only`).
- `nombre_empresa`: razón social de la empresa (`id_empresa.razon_social`).
- `nombre_libro`: nombre del libro (`id_libro.nombre`).
- `periodo`: el `__str__` del período (`id_periodo.__str__`), p. ej. `"2026-09 (ABIERTO)"`.

`read_only_fields`: `numero_asiento`, `estado`, `total_debe`, `total_haber`, `fecha_contabilizacion`, `fecha_creacion`.

Son campos que **solo escribe el sistema**: la numeración (`numero_asiento`) y los totales los calcula PostgreSQL; el estado lo controla el ciclo de contabilización.

---

## `PeriodoContableSerializer` y `LibroContableSerializer`

Serializers `__all__`: exponen todos los campos del modelo tal cual.

---

## `PlanCuentasSerializer`

Expone solo un subconjunto "seguro" del plan de cuentas:

`id_cuenta`, `codigo_cuenta`, `nombre_cuenta`, `tipo_cuenta`, `naturaleza`, `nivel`, `es_detalle`, `activo`, `clasificacion_ifrs`.

Oculta campos internos como `cuenta_padre_id` (jerarquía), evitando exponer la estructura interna a la API de listado general.