from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DocumentoTributario

from .serializers import DocumentoTributarioSerializer
from .services import DTEService


class HealthCheckView(APIView):
    """Endpoint simple para verificar que la API funciona"""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({"status": "OK", "message": "API de facturación funcionando correctamente"})


class DocumentoTributarioViewSet(viewsets.ModelViewSet):
    queryset = DocumentoTributario.objects.all().order_by("-fecha_emision")
    serializer_class = DocumentoTributarioSerializer

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        documento = self.get_object()
        result = DTEService.emitir_documento(documento.id_documento)

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
