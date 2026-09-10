# dte/views.py
from django.db import DatabaseError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DocumentoTributario, Entidad

from .permissions import EmpresaPermission
from .serializers import DocumentoTributarioSerializer, EntidadSerializer
from .services import DTEService


class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "OK", "message": "API de facturación funcionando correctamente"})


class EntidadViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar entidades (clientes/proveedores)"""

    permission_classes = [IsAuthenticated, EmpresaPermission]
    serializer_class = EntidadSerializer

    def get_queryset(self):
        empresa = getattr(self.request, "empresa_actual", None)
        if empresa:
            return Entidad.objects.filter(id_empresa=empresa, activo=True)
        return Entidad.objects.none()


class DocumentoTributarioViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentoTributarioSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        if hasattr(self.request, "empresa_actual"):
            return DocumentoTributario.objects.filter(id_empresa=self.request.empresa_actual).order_by(
                "-fecha_emision", "-numero_documento"
            )
        return DocumentoTributario.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request, "empresa_actual"):
            serializer.save(id_empresa=self.request.empresa_actual)
        else:
            raise PermissionError("No tiene empresa asignada")

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        documento = self.get_object()
        try:
            result = DTEService.emitir_documento(documento.id_documento)
        except DatabaseError as exc:
            message = exc.args[0] if exc.args else "Error interno al emitir el documento"
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        documento = self.get_object()
        result = DTEService.anular_documento(documento.id_documento)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def detalles_completos(self, request, pk=None):
        documento = self.get_object()
        result = DTEService.get_documento_con_detalles(documento.id_documento)

        if result:
            return Response(result, status=status.HTTP_200_OK)
        return Response({"error": "Documento no encontrado"}, status=status.HTTP_404_NOT_FOUND)
