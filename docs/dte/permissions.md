# Permisos de `dte/permissions.py`

## `EmpresaPermission(permissions.BasePermission)`

Es una clase de **permiso DRF** que decide si una petición puede o no ejecutarse.

Un permiso DRF expone dos hooks:

- `has_permission(request, view)` → se llama **una vez por petición** (antes de entrar a la vista).
- `has_object_permission(request, view, obj)` → se llama **por objeto** (en vistas de detalle, tras obtener el objeto).

### `has_permission(request, view)`

**Ciclo de decisión y qué lo termina:**

```
¿request.user no existe o no está autenticado?
  SÍ → return False    ← TERMINA (denegado: 403)
NO ↓
¿es superusuario?
  SÍ → return True     ← TERMINA (todo permitido)
NO ↓
¿tiene request.empresa_actual asignada por el middleware?
  SÍ → return True     ← TERMINA (permitido)
  NO → return False    ← TERMINA (denegado)
```

- El primer `return False` corta el acceso de anónimos.
- El `return True` del superusuario es una **salida rápida** (bypass) para administradores.
- La última condición repite la regla del middleware: **sin empresa no hay acceso**.

### `has_object_permission(request, view, obj)`

**Ciclo de decisión y qué lo termina:**

```
¿es superusuario?
  SÍ → return True    ← TERMINA
NO ↓
¿obj tiene id_empresa Y existe empresa_actual?
  SÍ → return (obj.id_empresa == empresa_actual)   ← TERMINA
                                            (True si es su empresa,
                                             False si no → 404/403)
NO → return True      ← TERMINA (objetos sin empresa: acceso abierto)
```

La última línea es un *default defensivo*: si un objeto no tiene `id_empresa` (p. ej. no es multiempresa), no se bloquea.

### Resumen de control de flujo

- Cada camino **termina en un `return`**: nunca hay continuidad entre un caso y otro.
- El permiso es **cascada**: primero autenticación, luego superusuario, luego empresa — y cada etapa puede dejar caer la petición.

!!! info "¿Qué efecto tiene en el usuario final?"
    Si el permiso devuelve `False`, DRF responde **403 Forbidden** (o 404 si además se usa el mecanismo de "no revelar existencia"). Protege las consultas de una empresa para que no se filtren datos de otra.