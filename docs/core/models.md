# Modelos de `core/models.py`

Todos los modelos mapean tablas del esquema PostgreSQL `contabilidad` (con `managed = False`), salvo `Perfil`.

Campo común en casi todos: `id_empresa`, que identifica la empresa dueña del registro y habilita la multiempresa.

---

## Empresa

**Tabla**: `contabilidad.empresa`

Representa a cada empresa que usa el sistema. Es la **raíz de la multiempresa**: sus datos (RUT, razón social, giro, resolución SII) identifican al contribuyente ante el SII.

Campos destacados:
- `id_empresa` (UUID, PK): identificador único, generado automáticamente.
- `rut`, `razon_social`: identidad legal de la empresa.
- `moneda_base`: por defecto `CLP` (peso chileno).
- `activo`: si la empresa está operativa.
- `resolucion_sii`, `fecha_resolucion`: autorización del SII para emitir DTE.

Método:
- `__str__()` → `"Razón Social (RUT)"`, usado en admin y representación legible.

---

## PlanCuentas

**Tabla**: `contabilidad.plan_cuentas`

Es el **catalogo de cuentas contables**. Las cuentas pueden tener jerarquía (padre/hijo) mediante `cuenta_padre_id`.

Campos destacados:
- `codigo_cuenta`, `nombre_cuenta`: identificación de la cuenta (ej. `110001`, "Caja").
- `tipo_cuenta`: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, ORDEN — determina dónde aparece en los estados financieros.
- `naturaleza`: DEBE o HABER — lado del asiento donde "crece" la cuenta.
- `es_detalle`: si es cuenta de nivel hoja (la que acepta movimientos).
- `clasificacion_ifrs`: CORRIENTE / NO_CORRIENTE — clasificación contable internacional.
- `acepta_centros_costo`, `acepta_auxiliares`, `requiere_documento`: reglas de uso.

`__str__()` → `"codigo - nombre"`.

---

## Entidad

**Tabla**: `contabilidad.entidad`

Define a las **contrapartes** de la empresa: clientes, proveedores y empleados. Los flags `es_cliente`, `es_proveedor`, `es_empleado` indican el rol.

Campos destacados:
- `condicion_pago` (días, por defecto 30), `limite_credito`, `vendedor_id`.
- `cuenta_contable_cliente` / `cuenta_contable_proveedor`: FK a `PlanCuentas` — qué cuenta usar según el rol.

---

## CentroCosto

**Tabla**: `contabilidad.centro_costo`

Permite imputar movimientos a centros de costo (ej. por sucursal). También tiene jerarquía (`centro_padre_id`).

---

## Producto

**Tabla**: `contabilidad.producto`

Catálogo de productos/servicios:
- `codigo`, `nombre`, `unidad_medida`, `precio_unitario`.
- `controla_stock` + `stock_actual`: si el producto lleva o no inventario.
- `cuenta_contable_id`: cuenta contable asociada.

---

## DocumentoTributario

**Tabla**: `contabilidad.documento_tributario`

Es el **documento estrella** del sistema: representa un DTE (factura, boleta, nota de débito/crédito, guía de despacho, etc.).

### Ciclo de vida del documento (máquina de estados)

```
            emitir()                      enviar al SII
 BORRADOR ──────────► EMITIDO ──────────► ENVIADO_SII ──► ACEPTADO_SII
   ▲                     │                                        │
   │                     │                                        ▼
   └─────────────────────┴──────────────────────────────────► RECHAZADO_SII
        anular()                        (también CEDIDO)
   ──────────► ANULADO
```

**Qué controla el avance del ciclo** (transiciones implementadas en Python):
- `BORRADOR → EMITIDO`: solo si `estado == BORRADOR` (lo controla `DTEService.emitir_documento`). Los triggers de PostgreSQL hacen el trabajo pesado (folio, asiento).
- `→ ANULADO`: `DTEService.anular_documento`; no se puede anular si ya está `ANULADO` o `RECHAZADO_SII`.
- Los estados `ENVIADO_SII` / `ACEPTADO_SII` / `RECHAZADO_SII` son flujos SII (persistidos en la columna `estado`).

Campos clave del ciclo y su control de finalización:
- `estado` (BORRADOR, EMITIDO, ENVIADO_SII, ACEPTADO_SII, RECHAZADO_SII, ANULADO, CEDIDO).
- `folio`, `track_id`: número de folio y correlativo devuelto por el SII.
- `xml_documento`, `ted`: XML del DTE y Representación Trigráfica Electrónica.
- `contabilizado`, `asiento_contable_id`: si ya generó su asiento contable.
- `documento_referencia_id`, `tipo_referencia`: permite referenciar otro documento (ej. nota de crédito que anula parcialmente una factura).

---

## DocumentoDetalle

**Tabla**: `contabilidad.documento_detalle`

Las **líneas** de un documento (cada producto/servicio de la factura).

Campos numéricos importantes:
- `cantidad`, `precio_unitario`, `descuento_porcentaje`, `descuento_monto`.
- `monto_neto`, `monto_exento`, `monto_iva`, `monto_total`: los montos calculados por línea.

Restricción de unicidad: `[id_documento, numero_linea]` — no puede haber dos líneas iguales en el mismo documento.

---

## DocumentoReferencia

**Tabla**: `contabilidad.documento_referencia`

Relación **documento ↔ documento**: permite que un DTE referencie a otro (una factura referenciada por una nota de crédito). Contiene `tipo_documento_ref`, `folio_ref`, `fecha_ref`, `razon_ref`.

---

## DocumentoTraslado

**Tabla**: `contabilidad.documento_traslado`

Datos de **traslado de mercancías** para las guías de despacho (patente, transportista, chofer, origen/destino, horarios). Relación 1 a 1 con `DocumentoTributario`.

Es obligatorio cuando `tipo_documento == "GUIA_DESPACHO"` (lo valida el serializer de DTE con los campos exigidos por la Resolución Ex. SII N° 154/2025).

---

## FolioSii

**Tabla**: `contabilidad.folio_sii`

Autorización de **folios** entregada por el SII:
- `folio_desde`, `folio_hasta`, `folio_actual`: rango autorizado y folio en uso.
- `xml_caf`: el XML del CAF (Código de Autorización de Folios).

El siguiente folio se obtiene con la función almacenada `obtener_siguiente_folio_sii()`, que **controla el ciclo de consumo de folios**: avanza `folio_actual` y termina cuando se agota el rango.

---

## SecuenciaControl

**Tabla**: `contabilidad.secuencia_control`

Contador genérico por empresa + clave (`clave`) con `ultimo_numero`. Lo usa `obtener_siguiente_numero()` para numerar asientos y pagos de forma atómica y sin duplicados.

---

## PeriodoContable

**Tabla**: `contabilidad.periodo_contable`

Período contable mensual por empresa:
- `estado`: ABIERTO → CERRADO → BLOQUEADO.
- `fecha_inicio`, `fecha_fin`, `fecha_cierre`, `usuario_cierre`.

**Ciclo de un período** (qué lo termina): el período se abre al primer registro del mes; el cierre lo fija un usuario autorizado (`fecha_cierre` y `usuario_cierre`); una vez CERRADO/BLOQUEADO no recibe más asientos. La función `obtener_periodo_contable()` lo crea si no existe para la fecha dada.

---

## LibroContable

**Tabla**: `contabilidad.libro_contable`

Catálogo de libros contables (Diario, Mayor, etc.) con `requiere_autorizacion` y `activo`. Base para agrupar asientos.

---

## AsientoContable

**Tabla**: `contabilidad.asiento_contable`

Un **asiento contable** agrupa movimientos DEBE/HABER de un mismo hecho económico:
- `tipo_asiento`: MANUAL, AUTOMATICO_VENTA, AUTOMATICO_COMPRA, CIERRE_MENSUAL, etc.
- `origen_documento` / `origen_documento_id`: qué documento (factura, pago) generó el asiento.
- `total_debe`, `total_haber`: deben cuadrar (regla de partida doble).
- `estado`: BORRADOR → CONTABILIZADO → CERRADO / ANULADO.

**Ciclo del asiento y su finalización**: la función `generar_asiento_documento()` o `generar_asiento_pago()` (vía triggers) lo crea con sus detalles; `validar_asiento_cuadrado()` comprueba que debes = haberes y **termina la operación** devolviendo `True/False`; el asiento queda `CONTABILIZADO` solo si cuadra.

---

## AsientoDetalle

**Tabla**: `contabilidad.asiento_detalle`

Cada línea del asiento: `id_cuenta`, `tipo_movimiento` (DEBE/HABER), `monto`, con referencias opcionales a `id_entidad`, `id_centro_costo` y datos del documento origen.

---

## MedioPago y Pago y PagoDocumento

- **MedioPago** (`medio_pago`): herramientas de pago (EFECTIVO, TRANSFERENCIA, TARJETA, WEBPAY...) con cuenta contable asociada.
- **Pago** (`pago`): un pago o cobro; `tipo_pago` distingue PAGO (salida) vs COBRO (entrada); `contabilizado` indica si generó asiento.
- **PagoDocumento** (`pago_documento`): relación **muchos a muchos** entre pagos y documentos (`monto_aplicado`): cuánto de ese pago cubre cada factura.

---

## Auditoria

**Tabla**: `contabilidad.auditoria`

Registro de auditoría genérico: `tabla`, `operacion`, `id_registro`, `datos_anteriores`, `datos_nuevos`, `usuario`, `ip_address`. Permite reconstruir quién cambió qué y cuándo.

---

## ConfiguracionAutomatizacion

**Tabla**: `contabilidad.configuracion_automatizacion`

Define **plantillas de asientos automáticos** (`template_asiento` JSON) por `tipo_evento` (ej. "VENTA", "COBRO"). Cuando ocurre el evento, el sistema instancia la plantilla y genera el asiento. Es la base de la *automatización contable*.

---

## SiiPlanCuentasReferencia y DiccionarioCuentas

- **SiiPlanCuentasReferencia** (`sii_plan_cuentas_referencia`): el plan de cuentas oficial del SII (`codigo_sii`, `nombre_cuenta_sii`).
- **DiccionarioCuentas** (`diccionario_cuentas`): mapea el plan interno de la empresa (plan_cuentas) con las cuentas del SII — necesario para generar el XML del Diccionario de Cuentas (LCE).

---

## CalLibrosElectronicos

**Tabla**: `contabilidad.cal_libros_electronicos`

El **CAL (Código de Autorización de Libros)** que otorga el SII para autorizar el envío de cada libro electrónico (DIARIO, MAYOR, BALANCE, COMPRAS_VENTAS). Incluye `numero_cal` y `fecha_autorizacion`.

---

## DtePendientesFirma

**Tabla**: `contabilidad.dte_pendientes_firma`

Cola de DTEs esperando firma/envío:
- Guarda el `xml_sin_firma`, luego el `xml_firmado`, y sigue el estado: GENERADO → FIRMADO → ENVIADO → ACEPTADO/RECHAZADO.
- `track_id_sii`, `mensaje_error`: correlativo y errores del SII.

**Ciclo y su finalización**: cada etapa avanza solo si la anterior terminó exitosamente; un `mensaje_error` marca RECHAZADO y detiene el ciclo de envío de ese documento.

---

## LibrosPendientesEnvio

**Tabla**: `contabilidad.libros_pendientes_envio`

Similar al anterior, pero para **libros electrónicos** (no DTEs): guarda el XML (sin/con firma) de cada libro por empresa, tipo, año/mes. Estados: PENDIENTE_GENERAR → GENERADO → FIRMADO → ENVIADO → ACEPTADO/RECHAZADO.

---

## CertificadoDigital

**Tabla**: `contabilidad.certificado_digital`

Almacena los **certificados digitales** de las empresas:
- `tipo`: CERTIFICADO_EMPRESA (firma de DTEs) o CLAVE_CAF.
- `contenido_cifrado` (binario), `huella_sha256`, `fecha_vencimiento`, `activo`.

Los certificados se guardan cifrados y verificados por su hash SHA-256; el vencimiento controla cuándo dejan de poder firmar.

---

## Perfil

Único modelo con `managed = True` (Django gestiona su tabla con migraciones).

Relaciona un usuario de Django (`user`, 1 a 1) con su `empresa` y su rol: ADMIN, CONTADOR o USUARIO. Es el puente entre la autenticación de Django y la **multiempresa**: el middleware lee `perfil.empresa` para asignar `request.empresa_actual`.

`__str__()` → `"username - Razón social"` (o "Sin empresa").

---

## Convención y pendientes

- Todos los campos usan **snake_case** y coinciden con columnas PostgreSQL.
- Los modelos con `managed = False` **no participan** en migraciones: los cambios de esquema se hacen con SQL.
- Campos "auditoría" estándar por modelo: `fecha_creacion`, `fecha_modificacion`, `usuario_creacion`.