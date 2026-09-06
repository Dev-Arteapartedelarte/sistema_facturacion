# config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("api/dte/", include("dte.urls")),
    path("api/contabilidad/", include("contabilidad.urls")),
    path("reportes/", include("reportes.urls")),
    path("lce/", include("lce.urls")),  # ← AGREGAR
    path("api/lce/", include("lce.urls")),  # ← AGREGAR
    path("api/seguridad/", include("seguridad.urls")),
]
