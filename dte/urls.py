# dte/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"documentos", views.DocumentoTributarioViewSet, basename="documento")
router.register(r"entidades", views.EntidadViewSet, basename="entidad")

urlpatterns = [
    path("health/", views.HealthCheckView.as_view(), name="health-check"),
    path("", views.lista_dte, name="lista_dte"),
    path(
        "documentos/lista-resumida/",
        views.DocumentoTributarioViewSet.as_view({"get": "lista_resumida"}),
        name="documento-lista-resumida",
    ),
    path("documentos/api-raw/", views.DocumentoTributarioRawListView.as_view(), name="documento-api-raw"),
    path("documentos/<uuid:pk>/xml/", views.ver_xml_dte, name="ver_xml_dte"),
    path("", include(router.urls)),
]
