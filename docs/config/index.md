# Módulo `config`

El módulo `config` es el **corazón de configuración** del proyecto Django. No contiene lógica de negocio: contiene todo lo necesario para que Django arranque y sepa cómo responder.

## Archivos que contiene

| Archivo | Propósito |
|---------|-----------|
| `settings.py` | Toda la configuración del proyecto (apps, middleware, base de datos, seguridad, API) |
| `urls.py` | El "mapa de rutas" raíz: dice qué URL responde cada app |
| `wsgi.py` | Punto de entrada para servidores WSGI (producción, ej. gunicorn) |
| `asgi.py` | Punto de entrada para servidores ASGI (websockets, asíncrono) |
| `__init__.py` | Marca la carpeta como paquete Python |

---

## `settings.py`

Es un archivo declarativo: define constantes que Django lee al iniciar.

### Ciclo de carga

```
1. load_dotenv()  → lee variables desde el archivo .env
2. BASE_DIR       → raíz del proyecto (se calcula con Pathlib)
3. SECRET_KEY     → clave secreta (para firmar sesiones y JWT)
4. DEBUG          → True en desarrollo, False en producción
5. INSTALLED_APPS → lista de apps activas
6. MIDDLEWARE     → cadena de middlewares (en orden)
7. DATABASES      → conexión a PostgreSQL
8. REST_FRAMEWORK → configuración de DRF (auth JWT, permisos, throttling)
9. SIMPLE_JWT     → duración y algoritmo de los tokens
10. LOGGING       → cómo y dónde se registran los logs
```

### Bloques relevantes explicados

#### Apps instaladas (`INSTALLED_APPS`)

Mezcla de apps de Django (admin, auth, sessions...) con apps de terceros (DRF, simplejwt, corsheaders, csp) y las apps propias:

- `core`, `dte`, `contabilidad`, `reportes`, `lce`, `seguridad`.

#### Base de datos (`DATABASES`)

```python
'OPTIONS': {
    'options': '-c search_path=contabilidad,public',
},
```

Es un detalle técnico importante: configura el **search_path** para que las consultas SQL sin esquema explícito busquen primero en el esquema `contabilidad`. Así los modelos `managed = False` apuntan a las tablas existentes.

`CONN_MAX_AGE = 60` mantiene conexiones abiertas 60 segundos (evita reconectar en cada request).

#### Cadena de middleware

Incluye los middlewares estándar de Django + CORS + **`core.middleware.EmpresaMiddleware`** (el último de la lista), clave para el multi-tenancy.

#### REST Framework

```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.BasicAuthentication',
],
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
],
```

- **Autenticación**: primero se intenta JWT; si no, sesión por cookie; si no, usuario/password básico.
- **Permisos**: por defecto toda vista exige usuario autenticado.
- **Throttling**: limita 100 peticiones/día para anónimos y 1000/día por usuario.

#### Seguridad

En producción (`DEBUG=False`):
- Redirección a HTTPS, cookies seguras, HSTS, `X_FRAME_OPTIONS = 'DENY'` y Content Security Policy (CSP) restringido.
- El CORS y CSRF solo permiten orígenes definidos por variables de entorno.

---

## `urls.py`

El **routeador raíz**. Ciclo:

```
Petición a /api/dte/documentos/...
   │
   ▼
config/urls.py revisa cada patrón en orden
   │
   ▼
encuentra 'api/dte/' → delega en dte/urls.py
   │
   ▼
dte/urls.py encuentra la vista → ejecuta
```

| Ruta | Destino | Propósito |
|------|---------|-----------|
| `admin/` | admin de Django | Panel administrativo |
| `` | `core.urls` | Dashboard y balance (HTML) |
| `api/token/` | JWT login | Obtener token de acceso |
| `api/token/refresh/` | JWT refresh | Renovar token |
| `api/dte/` | `dte.urls` | API de documentos tributarios |
| `api/contabilidad/` | `contabilidad.urls` | API contable |
| `reportes/` | `reportes.urls` | Reportes (HTML) |
| `lce/` | `lce.urls` | LCE (HTML) |
| `api/lce/` | `lce.urls` | LCE (API) |
| `api/seguridad/` | `seguridad.urls` | Seguridad (vacío) |

**Qué controla la terminación del ciclo de enrutado**: el primer patrón que hace *match* con la URL **detiene** la búsqueda y ejecuta su vista. Si ninguno coincide, Django responde 404.

---

## `wsgi.py` y `asgi.py`

Son simples puentes estándar:

- `wsgi.py` → sirve el proyecto con **WSGI** (el protocolo clásico de Python para servidores síncronos).
- `asgi.py` → sirve el proyecto con **ASGI** (protocolo moderno que además soporta asíncrono/websockets).

Ninguno tiene lógica propia: solo exportan `application` llamando a `get_wsgi_application()` / `get_asgi_application()`.

---

## Referencia API

Para la referencia automática de los módulos de configuración, consulta la documentación autogenerada por mkdocstrings según se registren. Al ser un paquete de configuración sin clases de negocio, la documentación de este módulo es principalmente esta narración.