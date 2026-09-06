from django.db import connection
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AsientoContable, AsientoDetalle, LibroContable, PeriodoContable, PlanCuentas

from .permissions import EmpresaPermission
from .serializers import (
    AsientoContableSerializer,
    AsientoDetalleSerializer,
    LibroContableSerializer,
    PeriodoContableSerializer,
    PlanCuentasSerializer,
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
