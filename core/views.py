from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import render

from .models import AsientoContable, DocumentoTributario, Empresa


@login_required
def dashboard(request):
    """Dashboard principal del sistema"""
    empresa = Empresa.objects.first()

    # Estadísticas básicas
    total_documentos = DocumentoTributario.objects.count()
    documentos_emitidos = DocumentoTributario.objects.filter(estado="EMITIDO").count()
    total_asientos = AsientoContable.objects.count()

    # Últimos documentos
    ultimos_documentos = DocumentoTributario.objects.all().order_by("-fecha_creacion")[:10]

    # Últimos asientos
    ultimos_asientos = AsientoContable.objects.all().order_by("-fecha_creacion")[:10]

    context = {
        "empresa": empresa,
        "total_documentos": total_documentos,
        "documentos_emitidos": documentos_emitidos,
        "total_asientos": total_asientos,
        "ultimos_documentos": ultimos_documentos,
        "ultimos_asientos": ultimos_asientos,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def balance_general(request):
    """Vista del balance general"""
    empresa = Empresa.objects.first()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)", [str(empresa.id_empresa)])
        columns = [col[0] for col in cursor.description]
        cuentas = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Separar por tipo
    activos = [c for c in cuentas if c["tipo_cuenta"] == "ACTIVO"]
    pasivos = [c for c in cuentas if c["tipo_cuenta"] == "PASIVO"]
    patrimonio = [c for c in cuentas if c["tipo_cuenta"] == "PATRIMONIO"]
    ingresos = [c for c in cuentas if c["tipo_cuenta"] == "INGRESO"]
    gastos = [c for c in cuentas if c["tipo_cuenta"] == "GASTO"]

    context = {
        "empresa": empresa,
        "activos": activos,
        "pasivos": pasivos,
        "patrimonio": patrimonio,
        "ingresos": ingresos,
        "gastos": gastos,
        "total_activo": sum(c["saldo"] for c in activos if c["saldo"] > 0),
        "total_pasivo": sum(c["saldo"] for c in pasivos if c["saldo"] > 0),
        "total_patrimonio": sum(c["saldo"] for c in patrimonio if c["saldo"] > 0),
    }
    return render(request, "core/balance_general.html", context)
