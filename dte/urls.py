from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentoTributarioViewSet, HealthCheckView

router = DefaultRouter()
router.register(r"documentos", DocumentoTributarioViewSet, basename="documento")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("", include(router.urls)),
]
