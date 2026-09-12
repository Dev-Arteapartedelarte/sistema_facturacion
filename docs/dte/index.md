# Módulo `dte` — Documentos Tributarios Electrónicos

El módulo `dte` expone la **API REST** para gestionar documentos tributarios electrónicos (facturas, boletas, notas de crédito/débito, guías de despacho, etc.) y las entidades (clientes/proveedores).

## Qué contiene

| Archivo | Propósito |
|---------|-----------|
| `views.py` | `DocumentoTributarioViewSet`, `EntidadViewSet`, `HealthCheckView` + helper `_parse_fields_param` |
| `serializers.py` | Serializers con **validación y cálculo automático** de IVA y totales |
| `services.py` | `DTEService`: lógica de emisión y anulación de documentos |
| `permissions.py` | `EmpresaPermission`: control de acceso por empresa |
| `urls.py` | Rutas de la API |
| `models.py` | Vacío (los modelos viven en `core`) |

## Endpoints (rutas en `dte/urls.py`)

Bajo el prefijo raíz `api/dte/`:

| Método + Ruta | Función |
|---------------|---------|
| `GET /api/dte/health/` | Comprobación de salud de la API (sin autenticar) |
| `GET/POST /api/dte/documentos/` | Listar / crear documentos |
| `GET/PUT/PATCH/DELETE /api/dte/documentos/{id}/` | Detalle / editar / eliminar |
| `POST /api/dte/documentos/{id}/emitir/` | **Emitir** documento (BORRADOR → EMITIDO) |
| `POST /api/dte/documentos/{id}/anular/` | **Anular** documento |
| `GET /api/dte/documentos/{id}/detalles_completos/` | Documento + sus líneas (SQL directo) |
| `GET /api/dte/documentos/lista-resumida/` | Lista con campos resumidos (`?fields=`) |
| `GET/POST /api/dte/entidades/` | Listar / crear entidades |

## Conceptos clave

### ¿Qué es un DTE?

Un **DTE (Documento Tributario Electrónico)** es la facturación electrónica chilena: el contribuyente genera un XML firmado digitalmente y lo envía al SII. En este sistema, la app `dte` maneja el ciclo **previo al SII**: crear, validar, emitir y anular.

El flujo completo (emisión real + firma + envío al SII) está esbozado con los módulos `lce` y `xsd_validator`, y los modelos de cola (`DtePendientesFirma`).

## Documentación detallada

- [Servicios](services.md): `DTEService.emitir_documento`, `anular_documento`, `get_documento_con_detalles`.
- [Serializers](serializers.md): validaciones y cálculo de IVA/total.
- [Vistas](views.md): ViewSets y acciones.
- [Permisos](permissions.md): `EmpresaPermission`.
- [Referencia API](api_reference.md): autogenerada.