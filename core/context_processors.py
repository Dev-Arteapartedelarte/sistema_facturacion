"""
Context processors para pasar variables a todas las plantillas.
"""


def empresa_actual(request):
    """
    Pasa la empresa actual a todas las plantillas.
    """
    if hasattr(request, "empresa_actual"):
        return {"empresa_actual": request.empresa_actual}
    return {"empresa_actual": None}
