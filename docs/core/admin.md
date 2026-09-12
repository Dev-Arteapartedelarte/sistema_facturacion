# Admin de `core/admin.py`

Configura el **panel de administración de Django** (http://localhost:8000/admin/), la interfaz web gratuita que Django genera para gestionar datos.

## `PerfilInline` y `CustomUserAdmin`

- **`PerfilInline`**: muestra el perfil (empresa + rol) directamente dentro del formulario de cada usuario.
- **`CustomUserAdmin`**: re-registra el `User` de Django para:
  - Incluir el `PerfilInline`.
  - Mostrar la empresa de cada usuario en la lista (`get_empresa`).

**Ciclo**: el admin des-registra el `User` original (`admin.site.unregister(User)`) y lo re-registra con la versión extendida.

## `PerfilAdmin`

Lista usuarios con su empresa y rol; permite filtrar por `rol` y `empresa`, y buscar por username, email o razón social.

## `EmpresaAdmin`

Gestión de empresas: se muestran `rut`, `razon_social`, `giro`, `activo`; busca por `rut`/`razon_social`; los campos `id_empresa`, `fecha_creacion` y `fecha_modificacion` son de solo lectura (los gestiona la BD).

## `PlanCuentasAdmin`

ADministra el plan de cuentas: filtros por `tipo_cuenta`, `naturaleza`, `activo`; búsqueda por código/nombre de cuenta.

## `EntidadAdmin`

Clientes/proveedores: filtros por `es_cliente`, `es_proveedor`, `activo`; búsqueda por `rut`/`razon_social`.

## `ProductoAdmin`

Admin del catálogo: muestra código, nombre, precio y stock; filtro por control de stock y estado.

## `DocumentoTributarioAdmin`

Panel para documentos tributarios:
- Columnas: tipo, número, folio, fecha, entidad, total, estado, contabilizado y un enlace a detalles (`ver_detalles`).
- Filtros por `tipo_documento`, `estado`, `contabilizado`.
- Inline `DocumentoDetalleInline` para editar líneas desde el mismo documento.

**Qué controla la finalización del "ciclo" visual**: el método `ver_detalles` cuenta las líneas (`count()`) y genera un enlace hacia la lista de detalles filtrada por documento — es un *link* de navegación, no un bucle.

## `DocumentoDetalleAdmin` / `AsientoContableAdmin` / `AsientoDetalleAdmin`

- Detalles de documentos: búsqueda por descripción, filtro por tipo de documento.
- Asientos: columnas con totales debe/haber, jerarquía de fecha (`date_hierarchy`), filtros por tipo/estado/empresa, y nombre de empresa calculado (`empresa_nombre`).
- Detalles de asientos: filtros por tipo de asiento, cuenta y movimiento.

## Resumen

El admin es una **capa de lectura/escritura** sobre el mismo modelo `managed = False`. Permite a personal no técnico (contadores) operar los datos sin tocar SQL. Las convenciones `snake_case` y `_nombre` (los calculados con sufijo descriptivo) se mantienen consistentes.