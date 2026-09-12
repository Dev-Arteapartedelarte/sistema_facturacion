# Sistema de Facturación Electrónica

Bienvenido a la documentación de desarrollo del **Sistema de Facturación Electrónica**.

## ¿Qué es este sistema?

Es una plataforma construida con **Django (Python)** y **PostgreSQL** que gestiona el ciclo completo de la facturación electrónica chilena (SII) y la contabilidad de una empresa:

- **Facturación electrónica (DTE)**: creación, emisión, anulación y consulta de Documentos Tributarios Electrónicos (facturas, boletas, notas de crédito/débito, guías de despacho, etc.).
- **Contabilidad**: asientos contables, período contable, plan de cuentas, libros contables.
- **Libros Contables Electrónicos (LCE)**: generación, firma y validación del XML que se envía al SII (Libro Diario, Libro Mayor y Diccionario de Cuentas).
- **Reportes financieros**: estado de resultados, balance general e indicadores financieros.

## Stack tecnológico

| Capa | Tecnología | Para qué se usa |
|------|-----------|-----------------|
| Framework web | Django 5.1 | ORM, vistas, admin, templates |
| API REST | Django REST Framework (DRF) | Endpoints JSON consumidos por frontend |
| Autenticación API | djangorestframework-simplejwt | Tokens JWT |
| Base de datos | PostgreSQL 16 | Persistencia; la lógica de negocio vive en funciones almacenadas |
| Firma digital | cryptography + lxml + xmlsec | Firmas electrónicas de LCE y DTE |
| Validación XML | xmlschema | Validación de XML contra los XSD del SII |
| Colas (opcional) | Celery + Redis | Tareas asíncronas (configurado, no implementado) |
| Calidad de código | ruff, mypy, pytest, pre-commit | Lint, type-check, tests |
| Entorno virtual | uv | Gestión de dependencias |

## Estructura de la documentación

- **[Arquitectura](arquitectura.md)**: cómo se organiza el sistema y qué paradigmas combina.
- **[config](config/index.md)**: configuración global (settings, urls).
- **[core](core/index.md)**: el "núcleo": modelos, middleware de empresa, vistas base.
- **[dte](dte/index.md)**: módulo de Documentos Tributarios Electrónicos.
- **[contabilidad](contabilidad/index.md)**: módulo contable (asientos, períodos, plan de cuentas).
- **[lce](lce/index.md)**: Libros Contables Electrónicos (XML, firma digital).
- **[reportes](reportes/index.md)**: reportes y estados financieros.
- **[seguridad](seguridad/index.md)**: módulo de seguridad (placeholder).
- **[xsd_validator](xsd_validator/index.md)**: herramientas para validar XML contra los XSD del SII.

## Comandos útiles

```bash
make dev          # Instalar todas las dependencias
make run          # Ejecutar el servidor de desarrollo
make test         # Ejecutar las pruebas
make check        # Quality gates (lint + type-check + tests)
make docs-serve   # Ver esta documentación en http://127.0.0.1:8000
make docs-build   # Generar el sitio estático en site/
```