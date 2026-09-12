# lce/urls.py
from django.urls import path

from . import views

urlpatterns = [
    # HTML Views
    path("", views.dashboard_lce, name="dashboard_lce"),
    path("libro-diario/", views.generar_libro_diario, name="generar_libro_diario"),
    path("libro-mayor/", views.generar_libro_mayor, name="generar_libro_mayor"),
    path("diccionario/", views.generar_diccionario_cuentas, name="generar_diccionario"),
    path("previsualizar/", views.previsualizar_libro_diario, name="previsualizar_lce"),
    path("ver-xml/<str:tipo>/", views.ver_xml_libro, name="ver_xml_libro"),
    # API
    path("api/periodos/", views.api_periodos, name="api_periodos_lce"),
    path("api/cal/", views.api_cal, name="api_cal_lce"),
]
