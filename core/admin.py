from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AsientoContable,
    AsientoDetalle,
    DocumentoDetalle,
    DocumentoTributario,
    Empresa,
    Entidad,
    FolioSii,
    LibroContable,
    MedioPago,
    Pago,
    PeriodoContable,
    PlanCuentas,
    Producto,
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "giro", "activo"]
    search_fields = ["rut", "razon_social"]
    list_filter = ["activo"]
    readonly_fields = ["id_empresa", "fecha_creacion", "fecha_modificacion"]


@admin.register(PlanCuentas)
class PlanCuentasAdmin(admin.ModelAdmin):
    list_display = ["codigo_cuenta", "nombre_cuenta", "tipo_cuenta", "naturaleza", "activo"]
    search_fields = ["codigo_cuenta", "nombre_cuenta"]
    list_filter = ["tipo_cuenta", "naturaleza", "activo"]


@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "es_cliente", "es_proveedor", "activo"]
    search_fields = ["rut", "razon_social"]
    list_filter = ["es_cliente", "es_proveedor", "activo"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "precio_unitario", "stock_actual", "controla_stock"]
    search_fields = ["codigo", "nombre"]
    list_filter = ["controla_stock", "activo"]


class DocumentoDetalleInline(admin.TabularInline):
    model = DocumentoDetalle
    extra = 1
    fields = ["numero_linea", "descripcion", "cantidad", "precio_unitario", "monto_neto", "monto_total"]
    readonly_fields = ["numero_linea"]


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
    fieldsets = (
        ("Información Principal", {"fields": ("id_empresa", "tipo_documento", "numero_documento", "folio")}),
        ("Fechas", {"fields": ("fecha_emision", "fecha_vencimiento")}),
        ("Entidad", {"fields": ("id_entidad",)}),
        ("Montos", {"fields": ("neto", "exento", "iva", "total", "impuesto_adicional")}),
        ("Estado", {"fields": ("estado", "contabilizado", "fecha_contabilizacion")}),
        ("Información Adicional", {"fields": ("glosa", "observaciones", "xml_documento")}),
    )

    def ver_detalles(self, obj):
        count = obj.documentodetalle_set.count()
        return format_html(
            '<a href="/admin/core/documentodetalle/?id_documento__id__exact={}">Ver {} líneas</a>',
            obj.id_documento,
            count,
        )

    ver_detalles.short_description = "Detalles"


@admin.register(DocumentoDetalle)
class DocumentoDetalleAdmin(admin.ModelAdmin):
    list_display = ["id_documento", "numero_linea", "descripcion", "cantidad", "monto_neto", "monto_total"]
    list_filter = ["id_documento__tipo_documento"]
    search_fields = ["descripcion"]


@admin.register(AsientoContable)
class AsientoContableAdmin(admin.ModelAdmin):
    list_display = ["numero_asiento", "fecha_asiento", "tipo_asiento", "glosa", "total_debe", "total_haber", "estado"]
    list_filter = ["tipo_asiento", "estado"]
    search_fields = ["numero_asiento", "glosa"]
    readonly_fields = ["id_asiento", "numero_asiento", "total_debe", "total_haber", "fecha_creacion"]
    fieldsets = (
        ("Información Principal", {"fields": ("numero_asiento", "fecha_asiento", "tipo_asiento")}),
        ("Empresa y Período", {"fields": ("id_empresa", "id_libro", "id_periodo")}),
        ("Descripción", {"fields": ("glosa",)}),
        ("Estado", {"fields": ("estado", "fecha_contabilizacion")}),
        ("Totales", {"fields": ("total_debe", "total_haber")}),
    )


@admin.register(AsientoDetalle)
class AsientoDetalleAdmin(admin.ModelAdmin):
    list_display = ["id_asiento", "numero_linea", "id_cuenta", "tipo_movimiento", "monto"]
    list_filter = ["tipo_movimiento"]
    search_fields = ["id_asiento__numero_asiento"]


@admin.register(PeriodoContable)
class PeriodoContableAdmin(admin.ModelAdmin):
    list_display = ["año", "mes", "fecha_inicio", "fecha_fin", "estado"]
    list_filter = ["estado"]
    search_fields = ["año", "mes"]


@admin.register(LibroContable)
class LibroContableAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "activo"]
    search_fields = ["codigo", "nombre"]


@admin.register(FolioSii)
class FolioSiiAdmin(admin.ModelAdmin):
    list_display = ["tipo_documento", "folio_desde", "folio_hasta", "folio_actual", "activo"]
    list_filter = ["tipo_documento", "activo"]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ["numero_pago", "fecha_pago", "id_entidad", "monto_total", "contabilizado"]
    list_filter = ["tipo_pago", "contabilizado"]
    search_fields = ["numero_pago"]


@admin.register(MedioPago)
class MedioPagoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "tipo", "activo"]
    search_fields = ["codigo", "nombre"]
    list_filter = ["tipo", "activo"]
