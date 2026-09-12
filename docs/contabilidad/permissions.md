# Permisos de `contabilidad/permissions.py`

## `EmpresaPermission(permissions.BasePermission)`

Misma estrategia que en `dte` (ver [permisos dte](../dte/permissions.md)). Es una clase duplicada en cada app: `dte` y `contabilidad` definen su propia `EmpresaPermission` con la misma lógica.

### `has_permission(request, view)`

**Ciclo de decisión y qué lo termina:**

```
¿usuario no autenticado? → return False      ← TERMINA (403)
NO ↓
¿superusuario?           → return True       ← TERMINA (bypass)
NO ↓
¿tiene empresa_actual?   → return True       ← TERMINA
                          → return False     ← TERMINA (403)
```

### `has_object_permission(request, view, obj)`

```
¿superusuario?              → return True    ← TERMINA
NO ↓
¿obj.id_empresa existe y    → return (obj.id_empresa == empresa_actual)
   hay empresa_actual?                        ← TERMINA
NO → return True                              ← TERMINA (default seguro)
```

### ¿Por qué está duplicada?

Por convención de Django, cada app es en lo posible autocontenida. Si en el futuro `contabilidad` necesita una regla distinta (p. ej. "solo contadores ven ciertos asientos"), puede modificarse sin tocar `dte`.

!!! tip "Duplicación aceptable"
    Son ~30 líneas; la duplicación es deliberada y comentada. Si creciera, convendría moverla a un módulo común (p. ej. `core/permissions.py`) y reutilizarla.