from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DocumentoTributario

from .permissions import EmpresaPermission
from .serializers import DocumentoTributarioSerializer
from .services import DTEService


class HealthCheckView(APIView):
    """Endpoint simple para verificar que la API funciona"""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "OK", "message": "API de facturación funcionando correctamente"})


class DocumentoTributarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Documentos Tributarios con control de acceso por empresa.
    """

    serializer_class = DocumentoTributarioSerializer
    permission_classes = [IsAuthenticated, EmpresaPermission]

    def get_queryset(self):
        """
        Filtra los documentos por la empresa del usuario.
        """
        if hasattr(self.request, "empresa_actual"):
            return DocumentoTributario.objects.filter(id_empresa=self.request.empresa_actual).order_by(
                "-fecha_emision", "-numero_documento"
            )
        return DocumentoTributario.objects.none()

    def perform_create(self, serializer):
        """
        Asigna automáticamente la empresa del usuario al crear.
        """
        if hasattr(self.request, "empresa_actual"):
            serializer.save(id_empresa=self.request.empresa_actual)
        else:
            raise PermissionError("No tiene empresa asignada")

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        """Emitir un documento"""
        documento = self.get_object()
        result = DTEService.emitir_documento(documento.id_documento)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        """Anular un documento"""
        documento = self.get_object()
        result = DTEService.anular_documento(documento.id_documento)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def detalles_completos(self, request, pk=None):
        """Obtener documento con todos los detalles"""
        documento = self.get_object()
        result = DTEService.get_documento_con_detalles(documento.id_documento)

        if result:
            return Response(result, status=status.HTTP_200_OK)
        return Response({"error": "Documento no encontrado"}, status=status.HTTP_404_NOT_FOUND)
