# Módulo `contabilidad`

El módulo `contabilidad` expone la **API de consulta contable**: asientos, períodos, libros y plan de cuentas. Es **solo lectura** desde la API (los asientos se generan por triggers/funciones almacenadas, no se crean a mano por el cliente).

Sus modelos (en `core/models.py`) mapean las tablas del esquema `contabilidad`.

## Qué contiene

| Archivo | Propósito |
|---------|-----------|
| `views.py` | ViewSets: `AsientoContableViewSet`, `PeriodoContableViewSet`, `LibroContableViewSet`, `PlanCuentasViewSet` + helper `_parse_fields_param` |
| `serializers.py` | Serializers de asientos, períodos, libros y plan de cuentas |
| `permissions.py` | `EmpresaPermission` (misma lógica que en `dte`) |
| `urls.py` | Rutas de la API |
| `models.py` | Vacío (los modelos viven en `core`) |

## Endpoints

Bajo `api/contabilidad/`:

| Método + Ruta | Función |
|---------------|---------|
| `GET /api/contabilidad/asientos/` | Listar asientos (filtrados por empresa) |
| `GET /api/contabilidad/asientos/{id}/` | Detalle |
| `GET /api/contabilidad/asientos/{id}/detalles/` | Líneas del asiento |
| `GET /api/contabilidad/asientos/balance_comprobacion/` | Balance de comprobación (función almacenada) |
| `GET /api/contabilidad/asientos/lista-resumida/` | Lista resumida con `?fields=` |
| `GET /api/contabilidad/periodos/` | Períodos contables |
| `GET /api/contabilidad/libros/` | Libros contables |
| `GET /api/contabilidad/plan-cuentas/` | Plan de cuentas (con filtro `?tipo=`) |

## Concepto clave

La API es **de lectura**: no expone POST/PUT/DELETE para asientos. La creación de asientos ocurre automáticamente cuando la base de datos procesa un evento (venta, pago) mediante sus funciones almacenadas (`generar_asiento_documento`, `generar_asiento_pago`) y los triggers. Así se garantiza la **regularidad contable**: nadie "inventa" un asiento por API.

## Documentación detallada

- [Vistas](views.md): cada ViewSet y sus acciones.
- [Serializers](serializers.md): cómo se serializan los asientos.
- [Permisos](permissions.md): `EmpresaPermission`.
- [Referencia API](api_reference.md): autogenerada.