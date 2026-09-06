from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_reportes, name="dashboard_reportes"),
    path("estado-resultados/", views.estado_resultados, name="estado_resultados"),
    path("balance-general/", views.balance_general_view, name="balance_general_reportes"),
    path("indicadores/", views.indicadores_financieros, name="indicadores"),
    path("api/test/", views.api_test, name="api_test"),
    path("api/estado-resultados/", views.api_estado_resultados, name="api_estado_resultados"),
    path("api/balance-general/", views.api_balance_general, name="api_balance_general"),
]
