# Módulo `seguridad`

El módulo `seguridad` está **creado pero vacío**: es un *placeholder* previsto para futuras funcionalidades de seguridad del sistema.

## Estado actual

| Archivo | Contenido |
|---------|-----------|
| `views.py` | Solo `# Create your views here.` |
| `models.py` | Solo `# Create your models here.` |
| `urls.py` | `urlpatterns = []` con comentario "Las rutas se agregarán aquí más adelante" |
| `admin.py` | Comentario de registro |
| `apps.py` | `SeguridadConfig` (configuración de la app) |
| `tests.py` | Vacío |

Se registra en `INSTALLED_APPS` (`config/settings.py`) y tiene ruta raíz `/api/seguridad/` en `config/urls.py`.

## Qué podría alojar en el futuro

Por el contexto del sistema (facturación electrónica, multiempresa, certificados digitales), este módulo es candidato natural para:

- Gestión de **certificados digitales** (carga, vencimiento, rotación).
- **Auditoría** de accesos y operaciones sensibles.
- Control de **roles** más fino (más allá de ADMIN/CONTADOR/USUARIO).
- **Permisos** de firmas electrónicas y aprobación de documentos.

## Ciclo

Al estar vacío, **no hay ciclo de negocio que documentar** por ahora: cualquier petición a `/api/seguridad/` termina con **404** (no hay rutas registradas). Los modelos/views/urls se agregarán cuando se desarrolle la funcionalidad.