# Vistas de `reportes/views.py`

## Patrón común (`login_required` + fallback de empresa)

```python
@login_required(login_url="/admin/login/")
def vista(request):
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()      # fallback de desarrollo
        if empresa:
            request.empresa_actual = empresa
```

- Sin login → redirige a `/admin/login/`.
- Sin empresa → primera empresa de la BD (fallback de desarrollo).

---

## `api_test(request)`

Endpoint de prueba. **Ciclo**: devuelve JSON con estado, usuario, autenticación y empresa. Ningún bucle; un solo `JsonResponse` termina el ciclo.

## `dashboard_reportes(request)`

Dashboard con los años y meses disponibles (para los filtros de los reportes):

```sql
SELECT DISTINCT EXTRACT(YEAR FROM fecha_asiento)::INT as año
FROM asiento_contable
WHERE id_empresa=%s AND estado IN ('CONTABILIZADO','CERRADO')
ORDER BY año DESC
```

y la equivalente para meses.

**Ciclo y terminación**: `cursor.fetchall()` recolecta todo y pasa a `[row[0] for row in ...]` (comprensión de lista que **termina al recorrer todas las filas**); luego `render(...)` termina con la respuesta HTML.

---

## `estado_resultados(request)`

### Fase 1 — Definir el período (fechas desde/hasta)

```
¿vienen ?año= y ?mes= ?
  SÍ → fecha_desde = date(año, mes, 1)
        fecha_hasta = (año+1, 1, 1) si mes==12, si no (año, mes+1, 1)
  NO → consulta el último período con asientos:
        SELECT EXTRACT(anio), EXTRACT(mes) ... ORDER BY fecha_asiento DESC LIMIT 1
        ├─ hay resultado → usa ese año/mes
        └─ no hay → mes en curso (desde 1° del mes hasta hoy)
```

**Qué termina esta fase**: la condición `if año and mes` (o el `if result` de la consulta posterior) — antes de continuar, ya hay un rango definido. La rama sin período usa `LIMIT 1`, que hace que PostgreSQL **termine la consulta devolviendo una sola fila**.

### Fase 2 — Listas de años/meses para el filtro

Mismas consultas que dashboard. `fetchall()` termina la recolección.

### Fase 3 — Calcular el resultado

```sql
SELECT * FROM contabilidad.estado_resultados(%s, %s, %s)
```

```
columns = [col[0] for col in cursor.description]
ingresos, gastos = [], []
total_ingresos = total_gastos = Decimal("0")
for row in cursor.fetchall():                    # bucle sobre filas → termina al agotarlas
    data = dict(zip(columns, row))
    if data["tipo_cuenta"] == "INGRESO":
        ingresos.append(data); total_ingresos += data["monto"]
    elif data["tipo_cuenta"] == "GASTO":
        gastos.append(data);  total_gastos += data["monto"]
resultado_operacional = total_ingresos - total_gastos
```

**Qué controla la finalización del bucle**: `for row in cursor.fetchall()` termina cuando `fetchall()` ya agotó las filas; dentro, cada `if/elif` decide la clasificación, y sumar `Decimal` evita errores de punto flotante.

### Fase 4 — Render

`render('reportes/estado_resultados.html', context)` termina el ciclo.

---

## `balance_general_view(request)`

### Ciclo

1. Empresa (con fallback).
2. `fecha_corte` = `?fecha=` o la fecha de hoy.
3. `SELECT * FROM contabilidad.balance_general(%s, %s)`.

```
activos, pasivos, patrimonio = [], [], []
total_activo = total_pasivo = total_patrimonio = Decimal("0")
for row in cursor.fetchall():                    # bucle → termina con las filas
    data = dict(zip(columns, row))
    if data["tipo_cuenta"] == "ACTIVO":     activos.append(data);     total_activo += data["saldo"]
    elif data["tipo_cuenta"] == "PASIVO":   pasivos.append(data);     total_pasivo += data["saldo"]
    elif data["tipo_cuenta"] == "PATRIMONIO": patrimonio.append(data); total_patrimonio += data["saldo"]
balance_cuadrado = abs(total_activo - (total_pasivo + total_patrimonio)) < Decimal("0.01")
```

4. `render('reportes/balance_general.html', context)`.

**Qué controla la terminación**: el `for` (agotar filas) y la comparación `balance_cuadrado` (ecuación activo = pasivo + patrimonio con tolerancia de un centavo).

---

## `indicadores_financieros(request)`

Calcula indicadores sobre los últimos 12 meses (`fecha_inicio = hoy - 365 días`).

**Ciclo**:
1. Empresa.
2. `fecha_fin = today`, `fecha_inicio = today - timedelta(days=365)`.
3. Balance general → `cuentas[codigo_cuenta] = saldo` (bucle sobre filas; termina al agotarlas).
4. Estado de resultados → suma ingresos/gastos (bucle; termina con las filas).
5. Selecciona saldos de cuentas concretas:

```
total_activo  = cuentas["110001"] + cuentas["110101"]     (Caja + Banco)
total_pasivo  = cuentas["210101"] + cuentas["210301"]
patrimonio_neto = cuentas["320001"]
```

6. Calcula indicadores con guardas contra división por cero:

```
liquidez      = total_activo  / total_pasivo   if total_pasivo > 0  else 0
endeudamiento = total_pasivo  / total_activo   if total_activo > 0  else 0
rentabilidad  = resultado     / total_ingresos if total_ingresos > 0 else 0
margen        = rentabilidad * 100
```

7. `render('reportes/indicadores.html', context)`.

**Qué controla la finalización del ciclo**: los `if ... else 0` **protegen la división** y terminan cada cálculo devolviendo 0 cuando el denominador es 0 (evita `ZeroDivisionError`).

---

## API JSON

### `api_estado_resultados(request)`

Igual que `estado_resultados` pero responde **JSON** en lugar de HTML:

1. Empresa (sin fallback: si no hay → `400`). **TERMINA**.
2. Período desde `GET` o `SELECT MAX(fecha_asiento) ... LIMIT` (con `if result and result[0]`).
3. Ejecuta `contabilidad.estado_resultados(...)`.
4. Bucle de clasificación (mismas reglas).
5. `try/except`: 
   - Éxito → `JsonResponse({success: True, data, total_ingresos, total_gastos, resultado})` — números convertidos con `float()` porque **JSON no soporta `Decimal`**. **TERMINA**.
   - Error → `JsonResponse({success: False, error}, status=500)**. **TERMINA**.

El `float()` es necesario para serializar los montos (`Decimal` no es JSON-serializable nativo).

### `api_balance_general(request)`

Análoga: fecha de corte, `contabilidad.balance_general(...)`, clasificación, y:

```
cuadrado = abs(total_activo - (total_pasivo + total_patrimonio)) < Decimal("0.01")
```

(también expuesto en el JSON como `cuadrado`; igual `float()` para los totales). `try/except` con `status=500` en error.