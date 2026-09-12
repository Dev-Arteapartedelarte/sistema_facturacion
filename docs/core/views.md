# Vistas de `core/views.py`

Este archivo mezcla **dos paradigmas**:

1. **Vistas clásicas de Django** (funciones que renderizan plantillas HTML): `dashboard`, `balance_general`, `handler404`, `handler500`.
2. **Vista DRF** (clase que responde JSON): `UserView`.

Ambas comparten un requisito: el usuario debe estar autenticado.

---

## `UserView(APIView)`

API que devuelve el **usuario actual** en JSON.

- **Permiso**: `IsAuthenticated` (solo usuarios autenticados).
- **Método**: `GET /api/user/`.

**Ciclo**: llega el `GET` → se comprueba autenticación (si no hay token/sesión válida, DRF responde 401 y **el ciclo termina**) → se lee `request.user` → se construye el dict con `id`, `username`, `email`, `first_name`, `last_name` → `Response(...)`.

**Qué termina el ciclo**: el control de DRF retorna la respuesta; no hay bucles.

---

## `dashboard(request)`

Vista HTML (protegida con `@login_required`) que muestra el **panel principal** con estadísticas de la empresa:

- Total de documentos tributarios.
- Documentos emitidos (`estado == "EMITIDO"`).
- Total de asientos contables.
- Últimos 10 documentos y asientos.

**Ciclo**:
```
login_required (¿autenticado? NO → redirige a /login/)      │
                                                             ▼
se lee request.empresa_actual (lo puso EmpresaMiddleware)    │
   ¿No hay empresa?
      SÍ → renderiza dashboard con contadores en 0.          │ Termina (no consulta BD)
   NO ↓
   consultas ORM: count() y order_by(...)[:10] para la       │
   empresa actual (el ORM filtra por id_empresa)             │
   ▼
   render(request, 'core/dashboard.html', context)           │ Termina: respuesta HTML
```

**Qué controla la finalización del ciclo**: la comprobación `if not empresa` corta la lógica hacia la plantilla con ceros; si hay empresa, el ciclo termina al renderizar la plantilla. Cada consulta ORM es un mini-ciclo sobre la BD cuyo fin es el cierre del `QuerySet`.

---

## `balance_general(request)`

Vista HTML que muestra el **balance general** llamando a la función almacenada de PostgreSQL:

```sql
SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)
```

**Ciclo**:
1. `login_required`.
2. Empresa actual (igual que dashboard).
3. Si no hay empresa → renderiza balance vacío y **termina**.
4. Si hay empresa → abre `connection.cursor()`:
   - Ejecuta la función almacenada con `id_empresa`.
   - Lee los nombres de columna (`cursor.description`) y convierte cada fila a un dict con `dict(zip(columns, row))`.
   - `cursor.fetchall()` cierra el ciclo de lectura de filas cuando no quedan más.
5. Clasifica las cuentas en `activos`, `pasivos`, `patrimonio` por `tipo_cuenta` (bucle `for c in cuentas` que **termina cuando se recorren todas**).
6. Suma los saldos (bucle sobre cada lista; termina al recorrerla).
7. Renderiza `core/balance_general.html`.

**Qué controla la finalización del ciclo**:
- `with connection.cursor()` cierra automáticamente el cursor al salir del bloque (context manager).
- La condición `if c['saldo'] > 0` filtra qué se suma.
- Cada `for` termina al agotar su lista.

---

## `handler404(request, exception)` y `handler500(request)`

Páginas de error personalizadas. Devuelven las plantillas `core/404.html` (status 404) y `core/500.html` (status 500).

Son los **últimos eslabones del ciclo de una petición que falló**: son invocadas por Django solo cuando ninguna ruta coincide (404) o cuando una vista lanza una excepción (500). Es decir, **controlan el fin "de emergencia" del ciclo de petición**.

---

## Rutas expuestas (`core/urls.py`)

| Ruta | Vista | Uso |
|------|-------|-----|
| `` | `dashboard` | Panel principal |
| `login/` | `LoginView` (Django) | Autenticación; tras loguear redirige al **dashboard** (`next_page=reverse_lazy('dashboard')`) |
| `logout/` | `LogoutView` (Django) | Cierra sesión y vuelve a `/login/` (POST con CSRF) |
| `balance/` | `balance_general` | Balance general |
| `api/user/` | `UserView` | Usuario actual (JSON) |

### Redirección del login al dashboard

Antes, todos los `@login_required(login_url='/admin/login/')` llevaban al usuario al **login de Django Admin**, que tras autenticarse lo dejaba en el **menú de admin**. Ahora:

- Existe una vista de login propia en `/login/` (`django.contrib.auth.views.LoginView`, plantilla `core/login.html`, `redirect_authenticated_user=True`).
- Todos los decoradores usan `login_url='login'`, por lo que un usuario no autenticado es redirigido a `/login/` y, al ingresar, aterriza en el **dashboard** (`next_page=reverse_lazy('dashboard')`).
- El logout de la app usa `LogoutView` en `/logout/` (ya no depende de `admin:logout`).
- `config/settings.py`: `LOGIN_URL = 'login'` y `LOGIN_REDIRECT_URL = '/'` como respaldo de estas rutas.
- **Login del Admin** (`/admin/login/`): en `config/urls.py` se redefine la clase del sitio por defecto (`admin.site.__class__ = DashboardAdminSite`) sobreescribiendo `login()`: si tras autenticar la respuesta es un **302** (éxito), se redirige a `/` (dashboard) en lugar del índice de admin. Los registros de modelos vía `admin.site.register` se conservan intactos.

**Qué controla la terminación del ciclo de login**: `LoginView` valida el formulario; si es válido redirige a `next` (o al `next_page`, es decir el dashboard). Si el usuario ya está autenticado, `redirect_authenticated_user=True` lo envía directo con **terminación inmediata**. En el Admin, el 302 de éxito se intercepta y **termina** en `/`.