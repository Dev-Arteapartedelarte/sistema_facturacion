from django.contrib import messages
from django.shortcuts import redirect


class EmpresaMiddleware:
    """
    Middleware que asigna la empresa actual al request usando el perfil del usuario.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo para usuarios autenticados
        if request.user.is_authenticated:
            # Excluir rutas de admin y login
            excluded_paths = ["/admin/", "/login/", "/logout/", "/accounts/"]
            is_excluded = any(request.path.startswith(path) for path in excluded_paths)

            if not is_excluded:
                try:
                    # Obtener empresa del perfil del usuario
                    if hasattr(request.user, "perfil") and request.user.perfil:
                        empresa = request.user.perfil.empresa
                        if empresa:
                            request.empresa_actual = empresa
                        else:
                            if request.user.is_superuser:
                                from core.models import Empresa

                                empresa = Empresa.objects.first()
                                if empresa:
                                    request.empresa_actual = empresa
                                else:
                                    messages.error(request, "No hay empresas disponibles en el sistema.")
                                    return redirect("/admin/")
                            else:
                                messages.error(request, "Su usuario no tiene una empresa asignada.")
                                return redirect("/admin/")
                    else:
                        if request.user.is_superuser:
                            from core.models import Empresa

                            empresa = Empresa.objects.first()
                            if empresa:
                                request.empresa_actual = empresa
                            else:
                                messages.error(request, "No hay empresas disponibles en el sistema.")
                                return redirect("/admin/")
                        else:
                            messages.error(request, "Su usuario no tiene perfil.")
                            return redirect("/admin/")
                except Exception as e:
                    messages.error(request, f"Error al obtener perfil: {e}")
                    return redirect("/admin/")

        response = self.get_response(request)
        return response
