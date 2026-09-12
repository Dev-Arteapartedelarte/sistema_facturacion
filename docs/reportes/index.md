# Módulo `reportes`

El módulo `reportes` genera los **estados financieros** de la empresa: Estado de Resultados, Balance General e Indicadores Financieros. Existe en dos formatos:

- **HTML** (vistas con plantillas) — para navegar en el navegador.
- **JSON** (API) — para consumir desde otro sistema o frontend.

La base de los cálculos son **funciones almacenadas de PostgreSQL**:

- `contabilidad.balance_general(id_empresa, fecha_corte)`.
- `contabilidad.balance_comprobacion(id_empresa, fecha)`.
- `contabilidad.estado_resultados(id_empresa, fecha_desde, fecha_hasta)`.

## Qué contiene

| Archivo | Propósito |
|---------|-----------|
| `views.py` | Vistas HTML + API JSON |
| `urls.py` | Rutas |
| `models.py` | Vacío |
| `apps.py` | Configuración |

## Rutas

| Ruta | Tipo | Función |
|------|------|---------|
| `/reportes/` | HTML | Dashboard de reportes |
| `/reportes/estado-resultados/` | HTML | Estado de Resultados |
| `/reportes/balance-general/` | HTML | Balance General |
| `/reportes/indicadores/` | HTML | Indicadores financieros |
| `/reportes/api/test/` | JSON | Prueba de la API |
| `/reportes/api/estado-resultados/` | JSON | Estado de Resultados |
| `/reportes/api/balance-general/` | JSON | Balance General |

## Concepto contable

- **Estado de Resultados**: ingresos − gastos → resultado del período (pérdidas o ganancias). Clasifica cuentas `INGRESO` y `GASTO`.
- **Balance General**: activo = pasivo + patrimonio (ecuación contable). Clasifica `ACTIVO`, `PASIVO` y `PATRIMONIO`.
- **Indicadores**: liquidez, endeudamiento, rentabilidad y margen a partir de saldos de cuentas específicas.

## Documentación detallada

- [Vistas](views.md).
- [Referencia API](api_reference.md): autogenerada.