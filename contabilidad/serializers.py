from rest_framework import serializers

from core.models import AsientoContable, AsientoDetalle, LibroContable, PeriodoContable, PlanCuentas


class AsientoDetalleSerializer(serializers.ModelSerializer):
    codigo_cuenta = serializers.CharField(source="id_cuenta.codigo_cuenta", read_only=True)
    nombre_cuenta = serializers.CharField(source="id_cuenta.nombre_cuenta", read_only=True)
    razon_social_entidad = serializers.CharField(source="id_entidad.razon_social", read_only=True, allow_null=True)

    class Meta:
        model = AsientoDetalle
        fields = [
            "id_detalle",
            "numero_linea",
            "id_cuenta",
            "codigo_cuenta",
            "nombre_cuenta",
            "tipo_movimiento",
            "monto",
            "id_entidad",
            "razon_social_entidad",
            "glosa",
        ]


class AsientoContableSerializer(serializers.ModelSerializer):
    detalles = AsientoDetalleSerializer(many=True, source="asientodetalle_set", read_only=True)
    nombre_empresa = serializers.CharField(source="id_empresa.razon_social", read_only=True)
    nombre_libro = serializers.CharField(source="id_libro.nombre", read_only=True)
    periodo = serializers.CharField(source="id_periodo.__str__", read_only=True)

    class Meta:
        model = AsientoContable
        fields = [
            "id_asiento",
            "numero_asiento",
            "fecha_asiento",
            "tipo_asiento",
            "glosa",
            "estado",
            "total_debe",
            "total_haber",
            "id_empresa",
            "nombre_empresa",
            "id_libro",
            "nombre_libro",
            "id_periodo",
            "periodo",
            "fecha_contabilizacion",
            "fecha_creacion",
            "detalles",
        ]
        read_only_fields = [
            "numero_asiento",
            "estado",
            "total_debe",
            "total_haber",
            "fecha_contabilizacion",
            "fecha_creacion",
        ]


class PeriodoContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoContable
        fields = "__all__"


class LibroContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroContable
        fields = "__all__"


class PlanCuentasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanCuentas
        fields = [
            "id_cuenta",
            "codigo_cuenta",
            "nombre_cuenta",
            "tipo_cuenta",
            "naturaleza",
            "nivel",
            "es_detalle",
            "activo",
            "clasificacion_ifrs",
        ]
