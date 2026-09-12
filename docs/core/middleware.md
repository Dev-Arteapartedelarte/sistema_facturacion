# Middleware: `core/middleware.py`

## ¿Qué es un middleware?

Un **middleware** en Django es una capa de software que se ejecuta **antes** de que llegue la petición a la vista y **después** de que la vista genera la respuesta. Es una cadena: cada middleware recibe `request`, hace algo y llama a `get_response(request)` para pasar el control al siguiente.

## `EmpresaMiddleware`

Es el pilar de la **multiempresa**: en este sistema una instalación sirve a varias empresas, y cada petición debe quedar asociada a una. Este middleware resuelve **cuál**.

### Ciclo del middleware (qué hace el ciclo)

```
Llega la petición HTTP
        │
        ▼
┌─ ¿request.user ya está autenticado?  ─┐
│   NO  → se intenta autenticar con JWT │
│         (si el token es válido, se    │
│          asigna request.user)         │
└──────────────┬────────────────────────┘
               ▼
┌─ ¿hay usuario autenticado? ── NO → pasar directo a la vista
│   SÍ
▼
¿La ruta es de /admin/, /login/, /logout/, /accounts/, /api/token/?
   SÍ → ruta excluida: no asignar empresa, pasar directo a la vista
   NO ↓
┌─ ¿request.user.perfil existe y tiene empresa? ─┐
│   SÍ → request.empresa_actual = perfil.empresa  │
│   NO y es superusuario → asignar la primera     │
│        empresa de la BD (Empresa.objects.first())│
│   NO y NO es superusuario → responde 403 JSON    │
│        (el ciclo TERMINA aquí, no llega a la vista)│
└──────────────┬───────────────────────────────────┘
               ▼
        Se llama a get_response(request)
        (siguiente middleware o la vista)
        ▼
      Se devuelve la respuesta
```

### Qué controla la finalización del ciclo

1. **Ruta excluida**: si la petición va a `/admin/`, `/login/`, etc., el middleware se salta la asignación. **Termina el intento de asignación**, no el ciclo HTTP (pasa a la vista).
2. **Sin empresa asignada**:
   - Usuario normal sin empresa/perfil → `return JsonResponse({...}, status=403)`: la petición **muere en el middleware**, nunca llega a la vista.
   - Superusuario → recibe la primera empresa de la BD como *fallback* (utilidad para desarrollo/pruebas).
3. **Sin empresas en la BD** (superusuario) → responde 400 "No hay empresas disponibles".
4. **Excepción inesperada** → se captura (`except Exception`), se loguea y se responde 500.

### Detalle técnico: autenticación JWT "manual" en el middleware

```python
if not request.user.is_authenticated:
    auth = JWTAuthentication()
    result = auth.authenticate(request)
```

Esto permite que peticiones **API** con token `Authorization: Bearer <token>` (y sin sesión) queden autenticadas y luego tengan `empresa_actual`. Es una doble vía: las vistas DRF ya validan JWT por su cuenta, pero el middleware lo hace **antes** para poder asignar la empresa.

Los tokens inválidos se capturan con `(InvalidToken, AuthenticationFailed)` y solo se registran en el log — **no cortan la petición** (la vista se encargará de rechazarla si hace falta).

### Notas de estilo

- Los logs usan emojis como `🔑`, `✅`, `⚠️`, `❌` para facilitar la lectura en consola.
- Las variables internas siguen `snake_case`: `excluded_paths`, `empresa`, `is_excluded`.
- La importación de `Empresa` se hace **dentro** del bloque (importación perezosa) para evitar dependencias circulares entre módulos.