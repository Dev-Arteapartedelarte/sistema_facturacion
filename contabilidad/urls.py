from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AsientoContableViewSet, LibroContableViewSet, PeriodoContableViewSet, PlanCuentasViewSet

router = DefaultRouter()
router.register(r"asientos", AsientoContableViewSet, basename="asiento")
router.register(r"periodos", PeriodoContableViewSet, basename="periodo")
router.register(r"libros", LibroContableViewSet, basename="libro")
router.register(r"plan-cuentas", PlanCuentasViewSet, basename="plancuenta")

urlpatterns = [
    path("", include(router.urls)),
]
