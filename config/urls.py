# config/urls.py
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path, reverse_lazy
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class DashboardAdminSite(admin.AdminSite):
    """AdminSite que tras iniciar sesión redirige al dashboard en vez del índice de admin."""

    def login(self, request, extra_context=None):
        response = super().login(request, extra_context)
        if request.user.is_authenticated and isinstance(response, HttpResponseRedirect):
            return HttpResponseRedirect(reverse_lazy("dashboard"))
        return response


# Reemplaza la clase del sitio admin por defecto: conserva los registros de
# modelos y cambia el login para que aterrice en el dashboard.
admin.site.__class__ = DashboardAdminSite


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/dte/", include("dte.urls")),
    path("api/contabilidad/", include("contabilidad.urls")),
    path("reportes/", include("reportes.urls")),
    path("lce/", include("lce.urls")),
    path("api/lce/", include("lce.urls")),
    path("api/seguridad/", include("seguridad.urls")),
]
