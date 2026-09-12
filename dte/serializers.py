# dte/serializers.py
from decimal import Decimal

from django.db import connection, transaction
from rest_framework import serializers

from core.models import (
    DocumentoDetalle,
    DocumentoReferencia,
    DocumentoTraslado,
    DocumentoTributario,
    Entidad,
)


class DocumentoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoDetalle
        fields = [
            "id_detalle",
            "numero_linea",
            "id_producto",
            "codigo_producto",
            "descripcion",
            "cantidad",
            "unidad_medida",
            "precio_unitario",
            "descuento_porcentaje",
            "descuento_monto",
            "monto_neto",
            "monto_exento",
            "monto_iva",
            "monto_total",
        ]


class DocumentoTrasladoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoTraslado
        fields = [
            "tipo_despacho",
            "ind_traslado",
            "patente",
            "patente_carro",
            "rut_transportista",
            "rut_chofer",
            "nombre_chofer",
            "dir_destino",
            "comuna_destino",
            "ciudad_destino",
            "fecha_salida",
            "hora_salida",
            "fecha_llegada",
        ]
        required = False

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = {
                key: (None if isinstance(value, str) and not value.strip() else value) for key, value in data.items()
            }
        return super().to_internal_value(data)


class DocumentoReferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoReferencia
        fields = [
            "id_documento_referenciado",
            "tipo_documento_ref",
            "folio_ref",
            "fecha_ref",
            "razon_ref",
        ]
        required = False


class EntidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entidad
        fields = ["id_entidad", "rut", "razon_social", "giro"]


class DocumentoTributarioSerializer(serializers.ModelSerializer):
    detalles = DocumentoDetalleSerializer(many=True, source="documentodetalle_set")
    traslado = DocumentoTrasladoSerializer(required=False, allow_null=True)
    referencias = DocumentoReferenciaSerializer(many=True, required=False)
    razon_social_entidad = serializers.CharField(source="id_entidad.razon_social", read_only=True)
    rut_entidad = serializers.CharField(source="id_entidad.rut", read_only=True)

    class Meta:
        model = DocumentoTributario
        fields = [
            "id_documento",
            "tipo_documento",
            "numero_documento",
            "folio",
            "fecha_emision",
            "fecha_vencimiento",
            "id_empresa",
            "id_entidad",
            "razon_social_entidad",
            "rut_entidad",
            "neto",
            "exento",
            "iva",
            "total",
            "impuesto_adicional",
            "tipo_impuesto_adicional",
            "estado",
            "glosa",
            "observaciones",
            "contabilizado",
            "fecha_contabilizacion",
            "detalles",
            "traslado",
            "referencias",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = [
            "numero_documento",
            "folio",
            "estado",
            "contabilizado",
            "fecha_contabilizacion",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        extra_kwargs = {
            "total": {"required": False},
            "iva": {"required": False},
        }

    def validate(self, data):
        """Validación y cálculo automático de IVA y total."""
        neto = data.get("neto", Decimal("0"))
        exento = data.get("exento", Decimal("0"))
        iva = data.get("iva", Decimal("0"))
        total = data.get("total", Decimal("0"))
        tipo_documento = data.get("tipo_documento")

        if tipo_documento == "GUIA_DESPACHO":
            traslado = data.get("traslado") or self.initial_data.get("traslado")
            if not traslado:
                raise serializers.ValidationError(
                    {
                        "traslado": (
                            "La guía de despacho requiere los datos de traslado "
                            "(documento_traslado) exigidos por la Resolución Ex. "
                            "SII N° 154/2025."
                        )
                    }
                )
            campos_requeridos = [
                "tipo_despacho",
                "ind_traslado",
                "dir_destino",
                "comuna_destino",
                "ciudad_destino",
                "fecha_salida",
                "hora_salida",
            ]
            faltantes = [c for c in campos_requeridos if not traslado.get(c)]
            if faltantes:
                raise serializers.ValidationError(
                    {"traslado": (f"Faltan campos obligatorios de traslado: {', '.join(faltantes)}")}
                )

        if tipo_documento and tipo_documento in ["GUIA_DESPACHO", "FACTURA_EXENTA"]:
            data["iva"] = Decimal("0")
            data["total"] = neto + exento
            return data

        if iva == Decimal("0") and "iva" not in self.initial_data:
            iva = neto * Decimal("0.19")
            data["iva"] = iva.quantize(Decimal("0.01"))

        if total == Decimal("0") and "total" not in self.initial_data:
            total = neto + data.get("iva", Decimal("0")) + exento
            data["total"] = total.quantize(Decimal("0.01"))

        if "iva" in data:
            data["iva"] = data["iva"].quantize(Decimal("0.01"))
        if "total" in data:
            data["total"] = data["total"].quantize(Decimal("0.01"))

        total_calculado = neto + data.get("iva", Decimal("0")) + exento
        if abs(data.get("total", Decimal("0")) - total_calculado) > Decimal("0.01"):
            raise serializers.ValidationError(
                {"total": f"El total ({data['total']}) no coincide con neto + iva + exento ({total_calculado})"}
            )

        return data

    def validate_neto(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("El neto no puede ser negativo")
        return value

    def validate_exento(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("El exento no puede ser negativo")
        return value

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop("documentodetalle_set", [])
        traslado_data = validated_data.pop("traslado", None)
        referencias_data = validated_data.pop("referencias", [])

        empresa = validated_data.get("id_empresa")
        empresa_id = empresa.id_empresa if empresa else None

        if not empresa_id:
            raise serializers.ValidationError({"id_empresa": "Este campo es requerido"})

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(numero_documento), 0) + 1 
                FROM documento_tributario 
                WHERE id_empresa = %s
            """,
                [str(empresa_id)],
            )
            numero_documento = cursor.fetchone()[0]

        validated_data["numero_documento"] = numero_documento
        validated_data["estado"] = "BORRADOR"

        documento = DocumentoTributario.objects.create(**validated_data)

        for detalle_data in detalles_data:
            detalle_data["id_documento"] = documento
            DocumentoDetalle.objects.create(**detalle_data)

        if traslado_data:
            traslado_data["id_documento"] = documento
            DocumentoTraslado.objects.create(**traslado_data)

        for ref_data in referencias_data:
            ref_data["id_documento"] = documento
            DocumentoReferencia.objects.create(**ref_data)

        return documento

    @transaction.atomic
    def update(self, instance, validated_data):
        detalles_data = validated_data.pop("documentodetalle_set", None)
        traslado_data = validated_data.pop("traslado", None)
        referencias_data = validated_data.pop("referencias", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if traslado_data is not None:
            DocumentoTraslado.objects.update_or_create(
                id_documento=instance,
                defaults=traslado_data,
            )

        if detalles_data is not None:
            instance.documentodetalle_set.all().delete()
            for detalle_data in detalles_data:
                detalle_data["id_documento"] = instance
                DocumentoDetalle.objects.create(**detalle_data)

        if referencias_data is not None:
            instance.referencias.all().delete()
            for ref_data in referencias_data:
                ref_data["id_documento"] = instance
                DocumentoReferencia.objects.create(**ref_data)

        return instance
