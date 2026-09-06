from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import redirect, render

from .models import AsientoContable, DocumentoTributario, Empresa


@login_required(login_url="/admin/login/")
def dashboard(request):
    """Dashboard principal del sistema"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "core/dashboard.html",
            {
                "empresa_actual": None,
                "total_documentos": 0,
                "documentos_emitidos": 0,
                "total_asientos": 0,
                "ultimos_documentos": [],
                "ultimos_asientos": [],
            },
        )

    total_documentos = DocumentoTributario.objects.filter(id_empresa=empresa).count()
    documentos_emitidos = DocumentoTributario.objects.filter(id_empresa=empresa, estado="EMITIDO").count()
    total_asientos = AsientoContable.objects.filter(id_empresa=empresa).count()

    ultimos_documentos = DocumentoTributario.objects.filter(id_empresa=empresa).order_by("-fecha_creacion")[:10]

    ultimos_asientos = AsientoContable.objects.filter(id_empresa=empresa).order_by("-fecha_creacion")[:10]

    context = {
        "empresa_actual": empresa,
        "total_documentos": total_documentos,
        "documentos_emitidos": documentos_emitidos,
        "total_asientos": total_asientos,
        "ultimos_documentos": ultimos_documentos,
        "ultimos_asientos": ultimos_asientos,
    }
    return render(request, "core/dashboard.html", context)


@login_required(login_url="/admin/login/")
def balance_general(request):
    """Vista del balance general"""
    empresa = getattr(request, "empresa_actual", None)

    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa

    if not empresa:
        return render(
            request,
            "core/balance_general.html",
            {
                "empresa": None,
                "activos": [],
                "pasivos": [],
                "patrimonio": [],
                "total_activo": 0,
                "total_pasivo": 0,
                "total_patrimonio": 0,
            },
        )

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)", [str(empresa.id_empresa)])
        columns = [col[0] for col in cursor.description]
        cuentas = [dict(zip(columns, row)) for row in cursor.fetchall()]

    activos = [c for c in cuentas if c["tipo_cuenta"] == "ACTIVO"]
    pasivos = [c for c in cuentas if c["tipo_cuenta"] == "PASIVO"]
    patrimonio = [c for c in cuentas if c["tipo_cuenta"] == "PATRIMONIO"]

    context = {
        "empresa": empresa,
        "activos": activos,
        "pasivos": pasivos,
        "patrimonio": patrimonio,
        "total_activo": sum(c["saldo"] for c in activos if c["saldo"] > 0),
        "total_pasivo": sum(c["saldo"] for c in pasivos if c["saldo"] > 0),
        "total_patrimonio": sum(c["saldo"] for c in patrimonio if c["saldo"] > 0),
    }
    return render(request, "core/balance_general.html", context)


def logout_view(request):
    """Vista personalizada para cerrar sesión"""
    logout(request)
    return redirect("/admin/login/")
