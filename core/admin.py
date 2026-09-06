from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import DocumentoDetalle, DocumentoTributario, Empresa, Entidad, Perfil, PlanCuentas, Producto


# ============================================================
# Inline para Perfil en UserAdmin
# ============================================================
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = "Perfil"
    fields = ["empresa", "rol"]
    extra = 0


# ============================================================
# Personalizar UserAdmin para incluir el perfil
# ============================================================
class CustomUserAdmin(UserAdmin):
    inlines = [PerfilInline]
    list_display = ["username", "email", "first_name", "last_name", "is_staff", "get_empresa"]

    def get_empresa(self, obj):
        if hasattr(obj, "perfil") and obj.perfil.empresa:
            return obj.perfil.empresa.razon_social
        return "-"

    get_empresa.short_description = "Empresa"


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ============================================================
# Admin para Perfil
# ============================================================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["user", "empresa", "rol"]
    list_filter = ["rol", "empresa"]
    search_fields = ["user__username", "user__email", "empresa__razon_social"]


# ============================================================
# Admin para Empresa
# ============================================================
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "giro", "activo"]
    search_fields = ["rut", "razon_social"]
    list_filter = ["activo"]
    readonly_fields = ["id_empresa", "fecha_creacion", "fecha_modificacion"]


# ============================================================
# Admin para PlanCuentas
# ============================================================
@admin.register(PlanCuentas)
class PlanCuentasAdmin(admin.ModelAdmin):
    list_display = ["codigo_cuenta", "nombre_cuenta", "tipo_cuenta", "naturaleza", "activo"]
    search_fields = ["codigo_cuenta", "nombre_cuenta"]
    list_filter = ["tipo_cuenta", "naturaleza", "activo"]


# ============================================================
# Admin para Entidad
# ============================================================
@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "es_cliente", "es_proveedor", "activo"]
    search_fields = ["rut", "razon_social"]
    list_filter = ["es_cliente", "es_proveedor", "activo"]


# ============================================================
# Admin para Producto
# ============================================================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "precio_unitario", "stock_actual", "controla_stock"]
    search_fields = ["codigo", "nombre"]
    list_filter = ["controla_stock", "activo"]


# ============================================================
# Inline para DocumentoDetalle
# ============================================================
class DocumentoDetalleInline(admin.TabularInline):
    model = DocumentoDetalle
    extra = 1
    fields = ["numero_linea", "descripcion", "cantidad", "precio_unitario", "monto_neto", "monto_total"]
    readonly_fields = ["numero_linea"]


# ============================================================
# Admin para DocumentoTributario
# ============================================================
@admin.register(DocumentoTributario)
class DocumentoTributarioAdmin(admin.ModelAdmin):
    list_display = [
        "tipo_documento",
        "numero_documento",
        "folio",
        "fecha_emision",
        "id_entidad",
        "total",
        "estado",
        "contabilizado",
        "ver_detalles",
    ]
    list_filter = ["tipo_documento", "estado", "contabilizado"]
    search_fields = ["numero_documento", "folio"]
    readonly_fields = ["id_documento", "folio", "fecha_creacion", "fecha_modificacion"]
    inlines = [DocumentoDetalleInline]

    def ver_detalles(self, obj):
        count = obj.documentodetalle_set.count()
        return format_html(
            '<a href="/admin/core/documentodetalle/?id_documento__id__exact={}">Ver {} líneas</a>',
            obj.id_documento,
            count,
        )

    ver_detalles.short_description = "Detalles"


# ============================================================
# Admin para DocumentoDetalle
# ============================================================
@admin.register(DocumentoDetalle)
class DocumentoDetalleAdmin(admin.ModelAdmin):
    list_display = ["id_documento", "numero_linea", "descripcion", "cantidad", "monto_neto", "monto_total"]
    list_filter = ["id_documento__tipo_documento"]
    search_fields = ["descripcion"]
