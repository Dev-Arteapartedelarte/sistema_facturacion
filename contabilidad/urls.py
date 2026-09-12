from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AsientoContableViewSet,
    LibroContableViewSet,
    PeriodoContableViewSet,
    PlanCuentasViewSet,
    lista_asientos,
)

router = DefaultRouter()
router.register(r"asientos", AsientoContableViewSet, basename="asiento")
router.register(r"periodos", PeriodoContableViewSet, basename="periodo")
router.register(r"libros", LibroContableViewSet, basename="libro")
router.register(r"plan-cuentas", PlanCuentasViewSet, basename="plancuenta")

urlpatterns = [
    path("", lista_asientos, name="lista_asientos"),
    path(
        "asientos/lista-resumida/",
        AsientoContableViewSet.as_view({"get": "lista_resumida"}),
        name="asiento-lista-resumida",
    ),
    path("", include(router.urls)),
]
