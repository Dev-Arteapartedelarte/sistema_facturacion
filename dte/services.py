import uuid

from django.db import transaction

from core.models import DocumentoTributario


class DTEService:
    """Servicio para operaciones de DTE"""

    @staticmethod
    def emitir_documento(id_documento: uuid.UUID) -> dict:
        """Emite un documento (cambia estado a EMITIDO)"""
        with transaction.atomic():
            documento = DocumentoTributario.objects.get(id_documento=id_documento)

            if documento.estado != "BORRADOR":
                return {
                    "success": False,
                    "error": f"El documento está en estado {documento.estado}, no se puede emitir",
                }

            # Cambiar estado a EMITIDO - los triggers hacen el resto
            documento.estado = "EMITIDO"
            documento.save()

            # Recargar para obtener folio y otros datos actualizados
            documento.refresh_from_db()

            return {
                "success": True,
                "id_documento": str(documento.id_documento),
                "folio": documento.folio,
                "estado": documento.estado,
                "contabilizado": documento.contabilizado,
            }

    @staticmethod
    def anular_documento(id_documento: uuid.UUID) -> dict:
        """Anula un documento"""
        with transaction.atomic():
            documento = DocumentoTributario.objects.get(id_documento=id_documento)

            if documento.estado in ["ANULADO", "RECHAZADO_SII"]:
                return {"success": False, "error": f"El documento ya está {documento.estado}"}

            documento.estado = "ANULADO"
            documento.save()

            return {"success": True, "id_documento": str(documento.id_documento), "estado": documento.estado}

    @staticmethod
    def get_documento_con_detalles(id_documento: uuid.UUID):
        """Obtiene un documento con todos sus detalles"""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    d.id_documento,
                    d.tipo_documento,
                    d.numero_documento,
                    d.folio,
                    d.fecha_emision,
                    d.estado,
                    d.neto,
                    d.iva,
                    d.total,
                    e.razon_social as entidad_nombre,
                    e.rut as entidad_rut,
                    json_agg(
                        json_build_object(
                            'id_detalle', dd.id_detalle,
                            'numero_linea', dd.numero_linea,
                            'descripcion', dd.descripcion,
                            'cantidad', dd.cantidad,
                            'precio_unitario', dd.precio_unitario,
                            'monto_neto', dd.monto_neto,
                            'monto_total', dd.monto_total
                        ) ORDER BY dd.numero_linea
                    ) as detalles
                FROM documento_tributario d
                JOIN entidad e ON e.id_entidad = d.id_entidad
                LEFT JOIN documento_detalle dd ON dd.id_documento = d.id_documento
                WHERE d.id_documento = %s
                GROUP BY d.id_documento, e.razon_social, e.rut
            """,
                [str(id_documento)],
            )

            row = cursor.fetchone()
            if row:
                return {
                    "id_documento": row[0],
                    "tipo_documento": row[1],
                    "numero_documento": row[2],
                    "folio": row[3],
                    "fecha_emision": row[4],
                    "estado": row[5],
                    "neto": row[6],
                    "iva": row[7],
                    "total": row[8],
                    "entidad_nombre": row[9],
                    "entidad_rut": row[10],
                    "detalles": row[11],
                }
            return None
