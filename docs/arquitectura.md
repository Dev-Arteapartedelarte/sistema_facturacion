# Arquitectura del Sistema

Este documento explica **cómo** está construido el sistema y por qué. Combina varios paradigmas y tecnologías; aquí se aclaran los conceptos técnicos de forma sencilla.

## 1. La conjunción de paradigmas

El sistema no es un Django "de libro de texto". Tiene **tres capas de lógica**:

### 1.1 Django (paradigma MTV — Modelo-Plantilla-Vista)

- **Modelo**: descripción de los datos (tablas) en Python.
- **Plantilla**: HTML que muestra datos al usuario.
- **Vista**: función o clase que recibe una petición HTTP, procesa y responde.

En este sistema las vistas de la API usan **DRF** (Django REST Framework), que extiende el paradigma añadiendo *serializers* y *viewsets*. Aun así, es el mismo patrón: **petición → lógica → respuesta**.

### 1.2 PostgreSQL "inteligente" (funciones almacenadas / stored procedures)

Aquí está lo distintivo: **la lógica de contabilidad no vive en Python, vive en la base de datos**, como funciones almacenadas dentro del esquema `contabilidad`.

Ejemplos:

```sql
SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)
SELECT contabilidad.obtener_siguiente_numero(%s, %s, %s)
SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s)
```

Esto significa que, al emitir un documento tribuibutario, los **triggers de la base de datos** son los que calculan folios, generan asientos contables y actualizan el estado. Python solo "toca el interruptor" y la base hace el trabajo pesado.

!!! info "Por qué es así"
    - Los modelos de Django se definen con `managed = False`, es decir, Django **no crea ni altera las tablas**; solo las lee/escribe mapeándolas a clases de Python.
    - Es un enfoque **database-first**: primero existió el modelo de datos en SQL, el código Python lo refleja.

### 1.3 Scripts utilitarios standalone

En `xsd_validator/` hay scripts independientes (ejecutables con `python` directamente) que validan XML contra los XSD del SII. No forman parte del ciclo de vida de Django: son herramientas de verificación.

## 2. Multiempresa (multi-tenancy)

Una misma instalación sirve a **muchas empresas**. Cada tabla de negocio tiene una columna `id_empresa` (UUID), y el sistema garantiza que un usuario **solo vea los datos de su empresa**.

El mecanismo es el **middleware** `core.middleware.EmpresaMiddleware`:

```
Petición HTTP
   │
   ▼
[validar JWT?] ── si está autenticado
   │
   ▼
[leer perfil del usuario → obtener su empresa]
   │
   ▼
[asignar request.empresa_actual]
   │
   ▼
[vista] ─── filtra sus consultas por request.empresa_actual
```

!!! note "Qué es un middleware"
    En Django, un **middleware** es código que se ejecuta entre el servidor web y la vista: recibe cada petición, puede modificarla, y pasa el control al siguiente elemento de una cadena. Piensa en él como un "guardia de seguridad" por el que pasa toda petición.

## 3. Ciclo de vida de una petición completa

Un ejemplo real ayuda a entender el ciclo y qué lo termina:

**Operación:** *Emitir un documento* (`POST /api/dte/documentos/{id}/emitir/`)

1. **Petición HTTP** llega al servidor.
2. **EmpresaMiddleware** asigna `request.empresa_actual` (si el usuario está autenticado y tiene perfil con empresa). Si falla → responde JSON con error y **el ciclo termina**.
3. **URL resolver** (`config/urls.py` → `dte/urls.py`) encuentra la ruta `emitir`.
4. **`DocumentoTributarioViewSet.emitir()`** (dte/views.py) llama a `DTEService.emitir_documento()`.
5. **`DTEService.emitir_documento()`** abre `transaction.atomic()`:
   - Carga el documento.
   - Si el estado **no es** `BORRADOR` → retorna error y **el ciclo termina** (no se emite).
   - Si es `BORRADOR` → cambia estado a `EMITIDO`, guarda y refresca desde la BD.
   - El `save()` dispara los **triggers** de PostgreSQL que, por ejemplo, asignan folio y generan el asiento contable.
6. **Retorno**: la vista responde JSON con `success: True` y los datos del documento. **El ciclo termina** con la respuesta HTTP.

En cada método documentado verás una descripción de **qué hace el ciclo** y **qué controla su finalización** (el famoso "return", una validación que corta, una excepción atrapada, o una condición de un bucle).

## 4. Convención `snake_case`

Todo el código sigue la convención **`snake_case`** para variables, funciones y campos de la base de datos:

- Campos del modelo: `id_empresa`, `razon_social`, `fecha_emision`, `numero_documento`.
- Variables: `empresa`, `documento`, `total_debe`, `total_haber`.
- Esta convención es estándar de Python (PEP 8) y en este proyecto también coincide con los nombres de las columnas de PostgreSQL, lo que evita traducciones entre Python y SQL.

La herramienta **ruff** (configurada en `pyproject.toml`) hace cumplir el estilo de código, incluidas las reglas de nombrado (N).

## 5. Calidad y pruebas

- **Ruff** 📏: lint + formateo (`make lint`, `make format`).
- **Mypy** 🧠: verificación de tipos (`make type-check`).
- **Pytest** 🧪: tests unitarios y de integración (`make test`). Actualmente las carpetas de tests existen pero están casi vacías; la infraestructura está lista.
- **pre-commit**: ejecuta ruff antes de cada commit.
- **`make check`**: ejecuta todo en serie (quality gates).

## 6. Infraestructura (docker-compose)

El `docker-compose.yml` levanta:

- **postgres**: base de datos principal (puerto 5432).
- **pgadmin**: cliente gráfico de la base (puerto 5050).
- **redis**: broker de tareas para Celery (puerto 6379).

## 7. Límites y pendientes conocidos

- `seguridad/` es una app vacía (placeholder).
- Celery está configurado en settings pero no hay tareas implementadas.
- La firma digital `LCESigner.firmar_xml()` devuelve el XML sin inserción real del nodo `Signature` (solo firma base64); los pasos se explican en [lce/signer](lce/signer.md).
- Los modelos son `managed = False`: cualquier cambio de esquema se hace en SQL, no con migraciones de Django (excepto el modelo `Perfil`).