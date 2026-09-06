import uuid

from django.db import connection


class DBHelpers:
    """Helpers para ejecutar funciones almacenadas de PostgreSQL"""

    @staticmethod
    def obtener_siguiente_numero(id_empresa: uuid.UUID, tipo: str, id_libro: uuid.UUID | None = None) -> int:
        """Obtiene el siguiente número de secuencia (asiento o pago)"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.obtener_siguiente_numero(%s, %s, %s)",
                [str(id_empresa), tipo, str(id_libro) if id_libro else None],
            )
            result = cursor.fetchone()
            return result[0] if result else 1

    @staticmethod
    def obtener_siguiente_folio_sii(id_empresa: uuid.UUID, tipo_documento: str) -> int:
        """Obtiene el siguiente folio SII para un tipo de documento"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT contabilidad.obtener_siguiente_folio_sii(%s, %s::tipo_documento_tributario)",
                [str(id_empresa), tipo_documento],
            )
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def generar_asiento_documento(id_documento: uuid.UUID) -> uuid.UUID:
        """Genera asiento contable para un documento"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_asiento_documento(%s)", [str(id_documento)])
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def generar_asiento_pago(id_pago: uuid.UUID) -> uuid.UUID:
        """Genera asiento contable para un pago"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_asiento_pago(%s)", [str(id_pago)])
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def validar_asiento_cuadrado(id_asiento: uuid.UUID) -> bool:
        """Verifica si un asiento está cuadrado"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.validar_asiento_cuadrado(%s)", [str(id_asiento)])
            result = cursor.fetchone()
            return result[0] if result else False

    @staticmethod
    def obtener_periodo_contable(id_empresa: uuid.UUID, fecha: str) -> uuid.UUID:
        """Obtiene o crea el período contable para una fecha"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.obtener_periodo_contable(%s, %s::date)", [str(id_empresa), fecha])
            result = cursor.fetchone()
            return result[0] if result else None
