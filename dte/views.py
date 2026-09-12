# dte/views.py
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DocumentoTributario, Empresa, Entidad

from .permissions import EmpresaPermission
from .serializers import DocumentoTributarioSerializer, EntidadSerializer
from .services import DTEService


def _parse_fields_param(request, fields_default):
    """Parse the ?fields= query parameter and return a list of field names."""
    fields = request.query_params.get("fields")
    if fields:
        return [f.strip() for f in fields.split(",") if f.strip()]
    return fields_default


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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        fields = _parse_fields_param(request, ["id_entidad", "rut", "razon_social", "giro"])
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        if fields != ["__all__"]:
            data = [{k: v for k, v in item.items() if k in fields} for item in data]
        return Response(data)


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

    @action(detail=False, methods=["get"])
    def lista_resumida(self, request):
        """Vista resumida con combo de campos clave"""
        fields = _parse_fields_param(
            request, ["id_documento", "tipo_documento", "numero_documento", "folio", "fecha_emision", "total", "estado"]
        )
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        if fields != ["__all__"]:
            data = [{k: v for k, v in item.items() if k in fields} for item in data]
        return Response(data)


class DocumentoTributarioRawListView(APIView):
    """Devuelve el JSON en bruto de los documentos tributarios en el navegador.

    Misma serialización que el listado principal, sin paginación ni filtros de
    campos, pensada para visualizar la respuesta en el navegador. Abierta en
    desarrollo (sin autenticación); si no hay empresa_actual se usa la primera
    empresa registrada.
    """

    permission_classes = []
    authentication_classes = []
    serializer_class = DocumentoTributarioSerializer

    def get(self, request):
        empresa = getattr(request, "empresa_actual", None)
        if not empresa:
            empresa_id = (
                DocumentoTributario.objects.order_by("id_empresa")
                .values_list("id_empresa", flat=True)
                .distinct()
                .first()
            )
            if empresa_id:
                empresa = Empresa.objects.filter(id_empresa=empresa_id).first()
            else:
                empresa = Empresa.objects.first()
        if not empresa:
            return Response({"detail": "No hay empresas disponibles"}, status=status.HTTP_400_BAD_REQUEST)
        queryset = DocumentoTributario.objects.filter(id_empresa=empresa).order_by(
            "-fecha_emision", "-numero_documento"
        )
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


def _empresa_del_request(request):
    """Resuelve la empresa actual, con respaldo en la primera registrada."""
    empresa = getattr(request, "empresa_actual", None)
    if not empresa:
        empresa = Empresa.objects.first()
        if empresa:
            request.empresa_actual = empresa
    return empresa


@login_required(login_url="login")
def lista_dte(request):
    """Página HTML con el listado de documentos tributarios, filtrable por cliente."""
    empresa = _empresa_del_request(request)
    if not empresa:
        return render(request, "dte/lista_dte.html", {"error": "No hay empresa asignada"})

    documentos = DocumentoTributario.objects.filter(id_empresa=empresa)
    clientes = Entidad.objects.filter(
        id_empresa=empresa,
        id_entidad__in=documentos.values_list("id_entidad", flat=True).distinct(),
    ).order_by("razon_social")

    cliente_seleccionado = None
    cliente = request.GET.get("cliente")
    if cliente:
        try:
            cliente_uuid = UUID(str(cliente))
        except ValueError:
            cliente_uuid = None
        if cliente_uuid:
            cliente_obj = clientes.filter(id_entidad=cliente_uuid).first()
            if cliente_obj:
                cliente_seleccionado = cliente_obj
                documentos = documentos.filter(id_entidad=cliente_obj)

    documentos = documentos.order_by("-fecha_emision", "-numero_documento")
    return render(
        request,
        "dte/lista_dte.html",
        {
            "empresa": empresa,
            "documentos": documentos,
            "clientes": clientes,
            "cliente_seleccionado": cliente_seleccionado,
        },
    )


@login_required(login_url="login")
def ver_xml_dte(request, pk):
    """Página HTML para visualizar el XML de un documento tributario (DTE)."""
    empresa = _empresa_del_request(request)
    if not empresa:
        return render(request, "dte/ver_xml.html", {"error": "No hay empresa asignada"})

    documento = DocumentoTributario.objects.filter(id_empresa=empresa, id_documento=pk).first()
    if not documento:
        return render(request, "dte/ver_xml.html", {"error": "Documento no encontrado"})

    xml_content = documento.xml_documento
    if not xml_content:
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_xml_dte(%s)", [str(pk)])
            row = cursor.fetchone()
            xml_content = row[0] if row else None

    return render(
        request,
        "dte/ver_xml.html",
        {
            "empresa": empresa,
            "documento": documento,
            "xml_content": xml_content,
            "error": None if xml_content else "No se pudo generar el XML para este documento",
        },
    )
