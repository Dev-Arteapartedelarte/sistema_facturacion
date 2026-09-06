# lce/views.py
import traceback
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from core.models import Empresa

# ============================================================
# VISTAS HTML
# ============================================================


@login_required(login_url="/admin/login/")
def dashboard_lce(request):
    """Dashboard de Libros Contables Electrónicos"""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(request, "lce/dashboard.html", {"empresa": None})

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT 
                EXTRACT(YEAR FROM fecha_asiento)::INT as año,
                EXTRACT(MONTH FROM fecha_asiento)::INT as mes,
                COUNT(*) as total_asientos
            FROM asiento_contable
            WHERE id_empresa = %s 
              AND estado IN ('CONTABILIZADO', 'CERRADO')
            GROUP BY EXTRACT(YEAR FROM fecha_asiento), EXTRACT(MONTH FROM fecha_asiento)
            ORDER BY año DESC, mes DESC
        """,
            [str(empresa.id_empresa)],
        )
        periodos = cursor.fetchall()

    return render(
        request,
        "lce/dashboard.html",
        {
            "empresa": empresa,
            "periodos": periodos,
        },
    )


@login_required(login_url="/admin/login/")
def generar_libro_diario(request):
    """Generar y descargar XML del Libro Diario"""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    año = request.GET.get("año")
    mes = request.GET.get("mes")

    if not año or not mes:
        return JsonResponse({"error": "Se requiere año y mes"}, status=400)

    try:
        año_int = int(año)
        mes_int = int(mes)
    except ValueError:
        return JsonResponse({"error": "Año y mes deben ser números"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s)", [str(empresa.id_empresa), año_int, mes_int]
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return JsonResponse(
                    {"error": "No se pudo generar el XML. Verifique que hay datos para el período."}, status=400
                )

            xml_content = result[0]

        response = HttpResponse(xml_content, content_type="application/xml; charset=utf-8")
        filename = f"libro_diario_{año_int}_{mes_int:02d}_{empresa.rut.replace('-', '')}.xml"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@login_required(login_url="/admin/login/")
def generar_libro_mayor(request):
    """Generar y descargar XML del Libro Mayor"""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    año = request.GET.get("año")
    mes = request.GET.get("mes")

    if not año or not mes:
        return JsonResponse({"error": "Se requiere año y mes"}, status=400)

    try:
        año_int = int(año)
        mes_int = int(mes)
    except ValueError:
        return JsonResponse({"error": "Año y mes deben ser números"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.generar_xml_libro_mayor(%s, %s, %s)", [str(empresa.id_empresa), año_int, mes_int]
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return JsonResponse(
                    {"error": "No se pudo generar el XML. Verifique que hay datos para el período."}, status=400
                )

            xml_content = result[0]

        response = HttpResponse(xml_content, content_type="application/xml; charset=utf-8")
        filename = f"libro_mayor_{año_int}_{mes_int:02d}_{empresa.rut.replace('-', '')}.xml"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@login_required(login_url="/admin/login/")
def generar_diccionario_cuentas(request):
    """Generar y descargar XML del Diccionario de Cuentas"""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    año = request.GET.get("año")
    if not año:
        año = str(datetime.now().year)

    try:
        año_int = int(año)
    except ValueError:
        return JsonResponse({"error": "Año debe ser un número"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.generar_xml_diccionario_cuentas(%s, %s)", [str(empresa.id_empresa), año_int]
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return JsonResponse(
                    {"error": "No se pudo generar el XML. Verifique que el diccionario está configurado."}, status=400
                )

            xml_content = result[0]

        response = HttpResponse(xml_content, content_type="application/xml; charset=utf-8")
        filename = f"diccionario_cuentas_{año_int}_{empresa.rut.replace('-', '')}.xml"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@login_required(login_url="/admin/login/")
def previsualizar_libro_diario(request):
    """Previsualizar el Libro Diario en HTML"""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "lce/previsualizar.html",
            {
                "empresa": None,
                "error": "No hay empresa asignada",
                "periodos": [],
            },
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT 
                EXTRACT(YEAR FROM fecha_asiento)::INT as año,
                EXTRACT(MONTH FROM fecha_asiento)::INT as mes
            FROM asiento_contable
            WHERE id_empresa = %s 
              AND estado IN ('CONTABILIZADO', 'CERRADO')
            ORDER BY año DESC, mes DESC
        """,
            [str(empresa.id_empresa)],
        )
        periodos = cursor.fetchall()

    año = request.GET.get("año")
    mes = request.GET.get("mes")

    if not año or not mes:
        return render(
            request,
            "lce/previsualizar.html",
            {
                "empresa": empresa,
                "periodos": periodos,
                "año": año,
                "mes": mes,
                "xml_content": None,
            },
        )

    try:
        año_int = int(año)
        mes_int = int(mes)
    except ValueError:
        return render(
            request,
            "lce/previsualizar.html",
            {
                "empresa": empresa,
                "periodos": periodos,
                "año": año,
                "mes": mes,
                "error": "Año y mes deben ser números",
                "xml_content": None,
            },
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s)", [str(empresa.id_empresa), año_int, mes_int]
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return render(
                    request,
                    "lce/previsualizar.html",
                    {
                        "empresa": empresa,
                        "periodos": periodos,
                        "año": año,
                        "mes": mes,
                        "error": "No se encontraron datos para el período seleccionado",
                        "xml_content": None,
                    },
                )

            xml_content = result[0]

        return render(
            request,
            "lce/previsualizar.html",
            {
                "empresa": empresa,
                "periodos": periodos,
                "año": año,
                "mes": mes,
                "xml_content": xml_content,
                "tipo": "Libro Diario",
                "error": None,
            },
        )

    except Exception as e:
        return render(
            request,
            "lce/previsualizar.html",
            {
                "empresa": empresa,
                "periodos": periodos,
                "año": año,
                "mes": mes,
                "error": str(e),
                "xml_content": None,
            },
        )


# ============================================================
# API ENDPOINTS
# ============================================================


@login_required(login_url="/admin/login/")
def api_periodos(request):
    """API para obtener períodos disponibles"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT 
                EXTRACT(YEAR FROM fecha_asiento)::INT as año,
                EXTRACT(MONTH FROM fecha_asiento)::INT as mes,
                COUNT(*) as total_asientos
            FROM asiento_contable
            WHERE id_empresa = %s 
              AND estado IN ('CONTABILIZADO', 'CERRADO')
            GROUP BY EXTRACT(YEAR FROM fecha_asiento), EXTRACT(MONTH FROM fecha_asiento)
            ORDER BY año DESC, mes DESC
        """,
            [str(empresa.id_empresa)],
        )
        rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({"año": row[0], "mes": row[1], "total_asientos": row[2]})

    return JsonResponse({"periodos": data})


@login_required(login_url="/admin/login/")
def api_cal(request):
    """API para obtener CAL disponibles"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        return JsonResponse({"error": "No hay empresa asignada"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_cal, tipo_libro, numero_cal, fecha_autorizacion
            FROM cal_libros_electronicos
            WHERE id_empresa = %s AND activo = true
            ORDER BY tipo_libro
        """,
            [str(empresa.id_empresa)],
        )
        rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append(
            {
                "id": str(row[0]),
                "tipo_libro": row[1],
                "numero_cal": row[2],
                "fecha_autorizacion": row[3].isoformat() if row[3] else None,
            }
        )

    return JsonResponse({"cal": data})
