# Módulo `core`

El módulo `core` es el **núcleo del sistema**: define los modelos de datos principales, el middleware multiempresa, las vistas base (HTML) y el acceso a las funciones almacenadas de PostgreSQL.

No es una app "de negocio" en el sentido de DTE o LCE; es la base que usan las demás.

## Qué contiene

| Archivo | Propósito |
|---------|-----------|
| `models.py` | Todos los modelos principales: Empresa, PlanCuentas, Entidad, DocumentoTributario, AsientoContable, FolioSii, Perfil, etc. |
| `middleware.py` | `EmpresaMiddleware`: asigna la empresa actual a cada petición |
| `views.py` | Dashboard, balance general (HTML) y `UserView` (API) |
| `urls.py` | Rutas raíz del módulo |
| `context_processors.py` | Inyecta la empresa actual en todas las plantillas |
| `db_helpers.py` | `DBHelpers`: puente a funciones almacenadas de PostgreSQL |
| `admin.py` | Registro y personalización del panel de administración |
| `apps.py` | Configuración de la app |
| `migrations/` | Migraciones (solo para `Perfil`, que es el único modelo `managed = True`) |

## El modelo de datos de un vistazo

```
Empresa  (1)───┬──(N) PlanCuentas
               ├──(N) Entidad (clientes/proveedores)
               ├──(N) Producto
               ├──(N) DocumentoTributario ──(N) DocumentoDetalle
               ├──(N) AsientoContable ──(N) AsientoDetalle
               ├──(N) FolioSii
               ├──(N) PeriodoContable
               ├──(N) LibroContable
               └──(N) SecuenciaControl
```

Todos tienen `managed = False`: **mapean tablas ya existentes en el esquema `contabilidad`** de PostgreSQL. El único modelo gestionado por Django (que sí crea su tabla con migraciones) es `Perfil`.

!!! info "¿Qué significa `managed = False`?"
    Django no creará ni modificará esa tabla. Sirve para que el ORM pueda *consultar* una tabla que ya existe en la base de datos, manteniendo el control del esquema en SQL (enfoque *database-first*).

## Ciclo de uso típico

```
request → EmpresaMiddleware asigna request.empresa_actual
        → las demás apps filtran sus consultas por esa empresa
```

Esta separación es lo que permite la multiempresa explicada en [arquitectura](../arquitectura.md).

## Convención de nombres

Todos los campos siguen **`snake_case`** y coinciden con los nombres de las columnas PostgreSQL (`id_empresa`, `razon_social`, `fecha_emision`). Esto hace que el traspaso ORM ↔ SQL sea directo, sin renombres.

## Documentación detallada

- [Modelos](models.md): cada clase de `models.py`.
- [Middleware](middleware.md): cómo se asigna la empresa.
- [Vistas](views.md): dashboard, balance y `UserView`.
- [Consultas a funciones almacenadas](db_helpers.md): `DBHelpers`.
- [Admin](admin.md): panel de administración.
- [Referencia API](api_reference.md): generada automáticamente por mkdocstrings.