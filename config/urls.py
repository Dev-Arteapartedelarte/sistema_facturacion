from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),  # Dashboard
    path("api/dte/", include("dte.urls")),
    path("api/contabilidad/", include("contabilidad.urls")),
    path("api/reportes/", include("reportes.urls")),
    path("api/lce/", include("lce.urls")),
    path("api/seguridad/", include("seguridad.urls")),
]
