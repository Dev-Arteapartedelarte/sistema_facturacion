from django.db import connection
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import AsientoContable, AsientoDetalle, LibroContable, PeriodoContable, PlanCuentas

from .serializers import (
    AsientoContableSerializer,
    AsientoDetalleSerializer,
    LibroContableSerializer,
    PeriodoContableSerializer,
    PlanCuentasSerializer,
)


class AsientoContableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar asientos contables"""

    queryset = AsientoContable.objects.all().order_by("-fecha_asiento", "-numero_asiento")
    serializer_class = AsientoContableSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get("empresa")
        if empresa_id:
            queryset = queryset.filter(id_empresa=empresa_id)
        return queryset

    @action(detail=True, methods=["get"])
    def detalles(self, request, pk=None):
        asiento = self.get_object()
        detalles = AsientoDetalle.objects.filter(id_asiento=asiento.id_asiento).order_by("numero_linea")
        serializer = AsientoDetalleSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def balance_comprobacion(self, request):
        empresa_id = request.query_params.get("empresa")
        if not empresa_id:
            return Response({"error": "Se requiere el parámetro empresa"}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM contabilidad.balance_comprobacion(%s, CURRENT_DATE)", [empresa_id])
            columns = [col[0] for col in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return Response(results)


class PeriodoContableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PeriodoContable.objects.all().order_by("-año", "-mes")
    serializer_class = PeriodoContableSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get("empresa")
        if empresa_id:
            queryset = queryset.filter(id_empresa=empresa_id)
        return queryset


class LibroContableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LibroContable.objects.all()
    serializer_class = LibroContableSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get("empresa")
        if empresa_id:
            queryset = queryset.filter(id_empresa=empresa_id)
        return queryset


class PlanCuentasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanCuentas.objects.filter(activo=True)
    serializer_class = PlanCuentasSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get("empresa")
        if empresa_id:
            queryset = queryset.filter(id_empresa=empresa_id)
        return queryset
