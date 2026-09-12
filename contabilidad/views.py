from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AsientoContable, AsientoDetalle, Empresa, LibroContable, PeriodoContable, PlanCuentas

from .permissions import EmpresaPermission
from .serializers import (
    AsientoContableSerializer,
    AsientoDetalleSerializer,
    LibroContableSerializer,
    PeriodoContableSerializer,
    PlanCuentasSerializer,
)


def _parse_fields_param(request, fields_default):
    """Parse the ?fields= query parameter and return a list of field names."""
    fields = request.query_params.get("fields")
    if fields:
        return [f.strip() for f in fields.split(",") if f.strip()]
    return fields_default


def _empresa_del_request(request):
    """Resuelve la empresa actual, con respaldo en la primera registrada."""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa
    return empresa


@login_required(login_url="login")
def lista_asientos(request):
    """Página HTML con el listado de asientos contables, filtrable por tipo de asiento."""
    empresa = _empresa_del_request(request)
    if not empresa:
        return render(request, "contabilidad/lista_asientos.html", {"error": "No hay empresa asignada"})

    asientos = AsientoContable.objects.filter(id_empresa=empresa)
    tipos = list(asientos.values_list("tipo_asiento", flat=True).distinct())

    tipo_seleccionado = None
    tipo = request.GET.get("tipo")
    if tipo in tipos:
        tipo_seleccionado = tipo
        asientos = asientos.filter(tipo_asiento=tipo)

    asientos = asientos.select_related("id_libro", "id_periodo").order_by("-fecha_asiento", "-numero_asiento")

    tipo_labels = dict(AsientoContable.TIPO_ASIENTO_CHOICES)
    tipos_options = [(tipo, tipo_labels.get(tipo, tipo)) for tipo in tipos]
    return render(
        request,
        "contabilidad/lista_asientos.html",
        {
            "empresa": empresa,
            "asientos": asientos,
            "tipos_options": tipos_options,
            "tipo_seleccionado": tipo_seleccionado,
        },
    )


class AsientoContableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar asientos contables con control de acceso"""

    serializer_class = AsientoContableSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        """Filtra asientos por la empresa del usuario"""
        if hasattr(self.request, "empresa_actual"):
            return AsientoContable.objects.filter(id_empresa=self.request.empresa_actual).order_by(
                "-fecha_asiento", "-numero_asiento"
            )
        return AsientoContable.objects.none()

    @action(detail=True, methods=["get"])
    def detalles(self, request, pk=None):
        """Obtener los detalles de un asiento"""
        asiento = self.get_object()
        detalles = AsientoDetalle.objects.filter(id_asiento=asiento.id_asiento).order_by("numero_linea")
        serializer = AsientoDetalleSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def balance_comprobacion(self, request):
        """Obtener balance de comprobación"""
        if not hasattr(request, "empresa_actual") or not request.empresa_actual:
            return Response({"error": "No tiene empresa asignada"}, status=status.HTTP_403_FORBIDDEN)

        empresa_id = str(request.empresa_actual.id_empresa)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)", [empresa_id])
            columns = [col[0] for col in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return Response(results)

    @action(detail=False, methods=["get"])
    def lista_resumida(self, request):
        """Vista resumida con combo de campos clave para asientos"""
        fields = _parse_fields_param(
            request,
            [
                "id_asiento",
                "numero_asiento",
                "fecha_asiento",
                "tipo_asiento",
                "estado",
                "total_debe",
                "total_haber",
                "empresa",
            ],
        )
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        if fields != ["__all__"]:
            data = [{k: v for k, v in item.items() if k in fields} for item in data]
        return Response(data)


class PeriodoContableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar períodos contables con control de acceso"""

    serializer_class = PeriodoContableSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        if hasattr(self.request, "empresa_actual"):
            return PeriodoContable.objects.filter(id_empresa=self.request.empresa_actual).order_by("-año", "-mes")
        return PeriodoContable.objects.none()


class LibroContableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar libros contables con control de acceso"""

    serializer_class = LibroContableSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        if hasattr(self.request, "empresa_actual"):
            return LibroContable.objects.filter(id_empresa=self.request.empresa_actual)
        return LibroContable.objects.none()


class PlanCuentasViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar plan de cuentas con control de acceso"""

    serializer_class = PlanCuentasSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        queryset = PlanCuentas.objects.filter(activo=True)
        if hasattr(self.request, "empresa_actual"):
            queryset = queryset.filter(id_empresa=self.request.empresa_actual)

        tipo = self.request.query_params.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo_cuenta=tipo)

        return queryset
