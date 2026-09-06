# contabilidad/permissions.py
from rest_framework import permissions


class EmpresaPermission(permissions.BasePermission):
    """
    Permiso que verifica que el usuario tenga acceso a la empresa del objeto.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Los superusuarios tienen acceso total
        if request.user.is_superuser:
            return True

        return hasattr(request, "empresa_actual") and request.empresa_actual is not None

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if hasattr(obj, "id_empresa") and hasattr(request, "empresa_actual"):
            return obj.id_empresa == request.empresa_actual

        return True
