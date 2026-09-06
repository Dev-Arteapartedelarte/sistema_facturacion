# reportes/views.py
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from core.models import Empresa

logger = logging.getLogger(__name__)


# ============================================================
# ENDPOINT DE PRUEBA
# ============================================================


@login_required(login_url="/admin/login/")
def api_test(request):
    """Endpoint de prueba para verificar que la API funciona"""
    empresa = getattr(request, "empresa_actual", None)
    return JsonResponse(
        {
            "status": "OK",
            "message": "API de reportes funcionando correctamente",
            "user": str(request.user),
            "authenticated": request.user.is_authenticated,
            "empresa": str(empresa) if empresa else None,
        }
    )


# ============================================================
# VISTAS HTML
# ============================================================


@login_required(login_url="/admin/login/")
def dashboard_reportes(request):
    """Dashboard de reportes financieros"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "reportes/dashboard_reportes.html",
            {
                "empresa": None,
            },
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT EXTRACT(YEAR FROM fecha_asiento)::INT as año
            FROM asiento_contable
            WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
            ORDER BY año DESC
        """,
            [str(empresa.id_empresa)],
        )
        años = [row[0] for row in cursor.fetchall()]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT EXTRACT(MONTH FROM fecha_asiento)::INT as mes
            FROM asiento_contable
            WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
            ORDER BY mes DESC
        """,
            [str(empresa.id_empresa)],
        )
        meses = [row[0] for row in cursor.fetchall()]

    context = {
        "empresa": empresa,
        "años": años,
        "meses": meses,
    }
    return render(request, "reportes/dashboard_reportes.html", context)


@login_required(login_url="/admin/login/")
def estado_resultados(request):
    """Vista del Estado de Resultados (Pérdidas y Ganancias)"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "reportes/estado_resultados.html",
            {
                "empresa": None,
            },
        )

    año = request.GET.get("año")
    mes = request.GET.get("mes")

    if año and mes:
        fecha_desde = date(int(año), int(mes), 1)
        if int(mes) == 12:
            fecha_hasta = date(int(año) + 1, 1, 1)
        else:
            fecha_hasta = date(int(año), int(mes) + 1, 1)
    else:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXTRACT(YEAR FROM fecha_asiento)::INT, EXTRACT(MONTH FROM fecha_asiento)::INT
                FROM asiento_contable
                WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
                ORDER BY fecha_asiento DESC
                LIMIT 1
            """,
                [str(empresa.id_empresa)],
            )
            result = cursor.fetchone()
            if result:
                año = result[0]
                mes = result[1]
                fecha_desde = date(año, mes, 1)
                if mes == 12:
                    fecha_hasta = date(año + 1, 1, 1)
                else:
                    fecha_hasta = date(año, mes + 1, 1)
            else:
                fecha_desde = date.today().replace(day=1)
                fecha_hasta = date.today()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT EXTRACT(YEAR FROM fecha_asiento)::INT as año
            FROM asiento_contable
            WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
            ORDER BY año DESC
        """,
            [str(empresa.id_empresa)],
        )
        años = [row[0] for row in cursor.fetchall()]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT EXTRACT(MONTH FROM fecha_asiento)::INT as mes
            FROM asiento_contable
            WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
            ORDER BY mes DESC
        """,
            [str(empresa.id_empresa)],
        )
        meses = [row[0] for row in cursor.fetchall()]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM contabilidad.estado_resultados(%s, %s, %s)
        """,
            [str(empresa.id_empresa), fecha_desde, fecha_hasta],
        )
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    ingresos = []
    gastos = []
    total_ingresos = Decimal("0")
    total_gastos = Decimal("0")

    for row in rows:
        data = dict(zip(columns, row))
        if data["tipo_cuenta"] == "INGRESO":
            ingresos.append(data)
            total_ingresos += data["monto"]
        elif data["tipo_cuenta"] == "GASTO":
            gastos.append(data)
            total_gastos += data["monto"]

    resultado_operacional = total_ingresos - total_gastos

    context = {
        "empresa": empresa,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "ingresos": ingresos,
        "gastos": gastos,
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "resultado_operacional": resultado_operacional,
        "años": años,
        "meses": meses,
        "año_seleccionado": año,
        "mes_seleccionado": mes,
    }
    return render(request, "reportes/estado_resultados.html", context)


@login_required(login_url="/admin/login/")
def balance_general_view(request):
    """Vista del Balance General"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "reportes/balance_general.html",
            {
                "empresa": None,
            },
        )

    fecha_corte = request.GET.get("fecha")
    if not fecha_corte:
        fecha_corte = date.today()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM contabilidad.balance_general(%s, %s)", [str(empresa.id_empresa), fecha_corte])
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    activos = []
    pasivos = []
    patrimonio = []
    total_activo = Decimal("0")
    total_pasivo = Decimal("0")
    total_patrimonio = Decimal("0")

    for row in rows:
        data = dict(zip(columns, row))
        if data["tipo_cuenta"] == "ACTIVO":
            activos.append(data)
            total_activo += data["saldo"]
        elif data["tipo_cuenta"] == "PASIVO":
            pasivos.append(data)
            total_pasivo += data["saldo"]
        elif data["tipo_cuenta"] == "PATRIMONIO":
            patrimonio.append(data)
            total_patrimonio += data["saldo"]

    context = {
        "empresa": empresa,
        "fecha_corte": fecha_corte,
        "activos": activos,
        "pasivos": pasivos,
        "patrimonio": patrimonio,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_patrimonio": total_patrimonio,
        "balance_cuadrado": abs(total_activo - (total_pasivo + total_patrimonio)) < Decimal("0.01"),
    }
    return render(request, "reportes/balance_general.html", context)


@login_required(login_url="/admin/login/")
def indicadores_financieros(request):
    """Vista de indicadores financieros"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "reportes/indicadores.html",
            {
                "empresa": None,
            },
        )

    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=365)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM contabilidad.balance_general(%s, %s)", [str(empresa.id_empresa), fecha_fin])
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    cuentas = {}
    for row in rows:
        data = dict(zip(columns, row))
        cuentas[data["codigo_cuenta"]] = data["saldo"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM contabilidad.estado_resultados(%s, %s, %s)
        """,
            [str(empresa.id_empresa), fecha_inicio, fecha_fin],
        )
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    total_ingresos = Decimal("0")
    total_gastos = Decimal("0")
    for row in rows:
        data = dict(zip(columns, row))
        if data["tipo_cuenta"] == "INGRESO":
            total_ingresos += data["monto"]
        elif data["tipo_cuenta"] == "GASTO":
            total_gastos += data["monto"]

    resultado = total_ingresos - total_gastos

    total_activo = cuentas.get("110001", Decimal("0")) + cuentas.get("110101", Decimal("0"))
    total_pasivo = cuentas.get("210101", Decimal("0")) + cuentas.get("210301", Decimal("0"))
    patrimonio_neto = cuentas.get("320001", Decimal("0"))

    liquidez = total_activo / total_pasivo if total_pasivo > 0 else Decimal("0")
    endeudamiento = total_pasivo / total_activo if total_activo > 0 else Decimal("0")
    rentabilidad = resultado / total_ingresos if total_ingresos > 0 else Decimal("0")
    margen = rentabilidad * 100

    indicators = {
        "liquidez": liquidez,
        "endeudamiento": endeudamiento,
        "rentabilidad": rentabilidad,
        "margen": margen,
        "resultado": resultado,
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "patrimonio_neto": patrimonio_neto,
    }

    context = {
        "empresa": empresa,
        "indicadores": indicators,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }
    return render(request, "reportes/indicadores.html", context)


# ============================================================
# API ENDPOINTS (JSON)
# ============================================================


@login_required(login_url="/admin/login/")
def api_estado_resultados(request):
    """API para Estado de Resultados en JSON"""
    logger.info(f"API Estado Resultados - Usuario: {request.user.username}")

    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        logger.warning("No hay empresa asignada")
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    año = request.GET.get("año")
    mes = request.GET.get("mes")

    if año and mes:
        fecha_desde = date(int(año), int(mes), 1)
        if int(mes) == 12:
            fecha_hasta = date(int(año) + 1, 1, 1)
        else:
            fecha_hasta = date(int(año), int(mes) + 1, 1)
    else:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT MAX(fecha_asiento)
                FROM asiento_contable
                WHERE id_empresa = %s AND estado IN ('CONTABILIZADO', 'CERRADO')
            """,
                [str(empresa.id_empresa)],
            )
            result = cursor.fetchone()
            if result and result[0]:
                fecha_hasta = result[0]
                fecha_desde = date(fecha_hasta.year, fecha_hasta.month, 1)
            else:
                fecha_desde = date.today().replace(day=1)
                fecha_hasta = date.today()

    try:
        logger.info(f"Consultando estado_resultados con fechas: {fecha_desde} - {fecha_hasta}")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM contabilidad.estado_resultados(%s, %s, %s)",
                [str(empresa.id_empresa), fecha_desde, fecha_hasta],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        data = []
        total_ingresos = Decimal("0")
        total_gastos = Decimal("0")

        for row in rows:
            item = dict(zip(columns, row))
            data.append(item)
            if item["tipo_cuenta"] == "INGRESO":
                total_ingresos += item["monto"]
            elif item["tipo_cuenta"] == "GASTO":
                total_gastos += item["monto"]

        logger.info(f"Registros encontrados: {len(data)}")
        return JsonResponse(
            {
                "success": True,
                "fecha_desde": fecha_desde.isoformat(),
                "fecha_hasta": fecha_hasta.isoformat(),
                "data": data,
                "total_ingresos": float(total_ingresos),
                "total_gastos": float(total_gastos),
                "resultado": float(total_ingresos - total_gastos),
            }
        )
    except Exception as e:
        logger.error(f"Error en API Estado Resultados: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required(login_url="/admin/login/")
def api_balance_general(request):
    """API para Balance General en JSON"""
    logger.info(f"API Balance General - Usuario: {request.user.username}")

    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        logger.warning("No hay empresa asignada")
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    fecha_corte = request.GET.get("fecha")
    if not fecha_corte:
        fecha_corte = date.today()

    try:
        logger.info(f"Consultando balance_general con fecha: {fecha_corte}")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM contabilidad.balance_general(%s, %s)", [str(empresa.id_empresa), fecha_corte])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        data = []
        total_activo = Decimal("0")
        total_pasivo = Decimal("0")
        total_patrimonio = Decimal("0")

        for row in rows:
            item = dict(zip(columns, row))
            data.append(item)
            if item["tipo_cuenta"] == "ACTIVO":
                total_activo += item["saldo"]
            elif item["tipo_cuenta"] == "PASIVO":
                total_pasivo += item["saldo"]
            elif item["tipo_cuenta"] == "PATRIMONIO":
                total_patrimonio += item["saldo"]

        logger.info(f"Registros encontrados: {len(data)}")
        return JsonResponse(
            {
                "success": True,
                "fecha_corte": fecha_corte.isoformat(),
                "data": data,
                "total_activo": float(total_activo),
                "total_pasivo": float(total_pasivo),
                "total_patrimonio": float(total_patrimonio),
                "cuadrado": abs(total_activo - (total_pasivo + total_patrimonio)) < Decimal("0.01"),
            }
        )
    except Exception as e:
        logger.error(f"Error en API Balance General: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
