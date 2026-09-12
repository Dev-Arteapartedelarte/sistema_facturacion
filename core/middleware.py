# core/middleware.py
import logging

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

logger = logging.getLogger(__name__)


class EmpresaMiddleware:
    """
    Middleware que asigna la empresa actual al request.
    Soporta autenticación JWT.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Intentar autenticar con JWT si no hay usuario
        if not request.user.is_authenticated:
            try:
                auth = JWTAuthentication()
                result = auth.authenticate(request)
                if result:
                    user, _ = result
                    request.user = user
                    logger.info(f"🔑 Usuario autenticado vía JWT: {user.username}")
            except (InvalidToken, AuthenticationFailed) as e:
                logger.warning(f"⚠️ JWT inválido: {e}")

        # Solo para usuarios autenticados
        if request.user.is_authenticated:
            # Excluir rutas de admin y login
            excluded_paths = ["/admin/", "/login/", "/logout/", "/accounts/", "/api/token/"]
            is_excluded = any(request.path.startswith(path) for path in excluded_paths)

            if not is_excluded:
                logger.info(f"🔍 Middleware ejecutándose para: {request.path}")
                logger.info(f"👤 Usuario: {request.user.username}")

                try:
                    # Obtener empresa del perfil del usuario
                    if hasattr(request.user, "perfil") and request.user.perfil:
                        empresa = request.user.perfil.empresa
                        if empresa:
                            request.empresa_actual = empresa
                            logger.info(f"✅ Empresa asignada: {empresa.razon_social}")
                        else:
                            logger.warning(f"⚠️ Usuario {request.user.username} sin empresa asignada")
                            if request.user.is_superuser:
                                from core.models import Empresa

                                empresa = Empresa.objects.first()
                                if empresa:
                                    request.empresa_actual = empresa
                                    logger.info(f"✅ Empresa asignada (superuser): {empresa.razon_social}")
                                else:
                                    return JsonResponse({"error": "No hay empresas disponibles"}, status=400)
                            else:
                                return JsonResponse({"error": "Usuario sin empresa asignada"}, status=403)
                    else:
                        logger.warning(f"⚠️ Usuario {request.user.username} sin perfil")
                        if request.user.is_superuser:
                            from core.models import Empresa

                            empresa = Empresa.objects.first()
                            if empresa:
                                request.empresa_actual = empresa
                                logger.info(f"✅ Empresa asignada (superuser sin perfil): {empresa.razon_social}")
                            else:
                                return JsonResponse({"error": "No hay empresas disponibles"}, status=400)
                        else:
                            return JsonResponse({"error": "Usuario sin perfil"}, status=403)
                except Exception as e:
                    logger.error(f"❌ Error en middleware: {e}")
                    return JsonResponse({"error": f"Error al obtener perfil: {str(e)}"}, status=500)
            else:
                logger.info(f"⏭️ Ruta excluida: {request.path}")

        response = self.get_response(request)
        return response
